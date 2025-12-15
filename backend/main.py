from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import os
import asyncio
import httpx
from typing import Optional

from backend.database import get_db, init_db
from backend.models import Secret
from backend.schemas import SecretCreate, SecretResponse, SecretView, PasswordVerify
from backend.security import (
    hash_password, verify_password, sanitize_text, 
    sanitize_filename, get_mime_type, validate_file_type
)
from backend.cleanup import cleanup_expired_secrets, delete_secret_immediately
from backend.storage import upload_file as cloudinary_upload, delete_file as cloudinary_delete
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="OneTimeView API",
    description="Secure one-time message and file sharing API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration - Allow Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE_FREE = int(os.getenv("MAX_FILE_SIZE_FREE", 104857600))  # 100MB
MAX_FILE_SIZE_PREMIUM = int(os.getenv("MAX_FILE_SIZE_PREMIUM", 524288000))  # 500MB

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start cleanup task"""
    init_db()
    asyncio.create_task(cleanup_expired_secrets())
# ============================================================================
# SERVE STATIC FRONTEND FILES
# ============================================================================

# Mount static files (CSS, JS, etc.)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

@app.get("/")
async def serve_index():
    """Serve frontend index.html"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found"}

@app.get("/create")
async def serve_create():
    """Serve create page"""
    create_path = FRONTEND_DIR / "create.html"
    if create_path.exists():
        return FileResponse(create_path)
    return {"error": "Page not found"}

@app.get("/view/{secret_id}")
async def serve_view(secret_id: str):
    """Serve view page"""
    view_path = FRONTEND_DIR / "view.html"
    if view_path.exists():
        return FileResponse(view_path)
    return {"error": "Page not found"}

@app.get("/expired")
async def serve_expired():
    """Serve expired page"""
    expired_path = FRONTEND_DIR / "expired.html"
    if expired_path.exists():
        return FileResponse(expired_path)
    return {"error": "Page not found"}

@app.get("/privacy")
async def serve_privacy():
    """Serve privacy policy page"""
    privacy_path = FRONTEND_DIR / "privacy.html"
    if privacy_path.exists():
        return FileResponse(privacy_path)
    return {"error": "Page not found"}

@app.get("/terms")
async def serve_terms():
    """Serve terms of service page"""
    terms_path = FRONTEND_DIR / "terms.html"
    if terms_path.exists():
        return FileResponse(terms_path)
    return {"error": "Page not found"}




@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/test-cloudinary")
async def test_cloudinary():
    """Test Cloudinary configuration"""
    import cloudinary
    
    config_info = {
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key_exists": bool(os.getenv("CLOUDINARY_API_KEY")),
        "api_secret_exists": bool(os.getenv("CLOUDINARY_API_SECRET")),
        "cloudinary_configured": bool(cloudinary.config().cloud_name)
    }
    
    # Try a simple test upload
    try:
        from io import BytesIO
        test_data = BytesIO(b"test")
        result = cloudinary.uploader.upload(
            test_data,
            resource_type="raw",
            folder="onetimeview_test"
        )
        
        # Delete the test file
        cloudinary.uploader.destroy(result['public_id'], resource_type='raw')
        
        return {
            "status": "success",
            "config": config_info,
            "test_upload": "successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "config": config_info,
            "error": str(e)
        }


@app.post("/api/secrets", response_model=SecretResponse)
@limiter.limit("10/minute")
async def create_secret(
    request: Request,
    content_type: str = Form(...),
    content: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    expiry_hours: Optional[int] = Form(None),
    max_views: Optional[int] = Form(1),
    is_premium: bool = Form(False),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Create a new secret"""
    
    # Validate content type
    if content_type not in ["text", "image", "video", "file"]:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    # For text secrets, content is required
    if content_type == "text":
        if not content:
            raise HTTPException(status_code=400, detail="Content is required for text secrets")
        content = sanitize_text(content)
    
    # For file-based secrets, file is required
    if content_type in ["image", "video", "file"]:
        if not file:
            raise HTTPException(status_code=400, detail="File is required")
    
    # Validate and set max_views
    if max_views is None or max_views < 1:
        max_views = 1
    if max_views > 10:
        max_views = 10
    
    # Create secret object
    secret = Secret(
        content_type=content_type,
        max_views=max_views,
        is_premium=is_premium
    )
    
    # Handle text content
    if content_type == "text":
        secret.content = content
    
    # Handle file upload - Use Cloudinary
    if file:
        # Validate file type
        is_valid, detected_type = validate_file_type(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Check file size based on tier
        max_size = MAX_FILE_SIZE_PREMIUM if is_premium else MAX_FILE_SIZE_FREE
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File size exceeds limit ({max_size / 1024 / 1024}MB)"
            )
        
        # Determine resource type for Cloudinary
        # Force RAW for everything to avoid "Failed to ping image" errors
        # We will proxy images through our backend to fix headers
        resource_type = "raw"
        
        # Upload to Cloudinary
        file_content = await file.read()
        try:
            upload_result = cloudinary_upload(file_content, resource_type=resource_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
        secret.cloud_url = upload_result["secure_url"]
        secret.cloud_public_id = upload_result["public_id"]
        secret.cloud_resource_type = upload_result.get("resource_type", resource_type)
        secret.file_name = file.filename
        secret.mime_type = get_mime_type(file.filename)
    
    # Handle password
    if password:
        secret.password_hash = hash_password(password)
    
    # Handle expiry
    if expiry_hours is not None:
        if expiry_hours == 0:
            if not is_premium:
                raise HTTPException(
                    status_code=403, 
                    detail="No Expiry option requires premium subscription"
                )
            secret.expiry_time = None
        else:
            secret.expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
    else:
        secret.expiry_time = datetime.utcnow() + timedelta(hours=24)
    
    # Save to database
    db.add(secret)
    db.commit()
    db.refresh(secret)
    
    # Build response with frontend URL (Vercel)
    frontend_url = os.getenv("FRONTEND_URL", "https://onetimeview-sooty.vercel.app")
    return SecretResponse(
        id=secret.id,
        url=f"{frontend_url}/view/{secret.id}",
        expires_at=secret.expiry_time,
        has_password=bool(secret.password_hash),
        content_type=secret.content_type,
        max_views=secret.max_views
    )


@app.post("/api/secrets/{secret_id}/verify")
@limiter.limit("10/minute")
async def verify_password_endpoint(
    request: Request,
    secret_id: str,
    data: PasswordVerify,
    db: Session = Depends(get_db)
):
    """Verify password for a secret (does not check view count, only time expiry)"""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Only check time-based expiry here, NOT view count
    if secret.expiry_time and datetime.utcnow() > secret.expiry_time:
        raise HTTPException(status_code=404, detail="Secret has expired")
    
    if not secret.password_hash:
        return {"verified": True}
    
    if verify_password(data.password, secret.password_hash):
        return {"verified": True}
    
    return {"verified": False}


@app.get("/api/secrets/{secret_id}", response_model=SecretView)
@limiter.limit("10/minute")
async def get_secret(
    request: Request,
    secret_id: str,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve a secret (ONE-TIME VIEW)"""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Check if already viewed or expired
    if secret.is_expired():
        delete_secret_immediately(secret_id)
        raise HTTPException(status_code=404, detail="Secret has expired or already been viewed")
    
    # Verify password if required
    if secret.password_hash:
        if not password:
            raise HTTPException(status_code=401, detail="Password required")
        if not verify_password(password, secret.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    # Increment view count
    secret.increment_view()
    db.commit()
    
    # Calculate remaining views
    remaining_views = secret.max_views - secret.view_count
    
    # Prepare response
    response = SecretView(
        content_type=secret.content_type,
        content=secret.content if secret.content_type == "text" else None,
        file_name=secret.file_name,
        mime_type=secret.mime_type,
        remaining_views=remaining_views
    )
    
    # For files, provide Cloudinary URL or fallback to download URL
    if secret.cloud_url:
        # For images, we must proxy through backend to get correct Content-Type (since we upload as raw)
        if secret.content_type == "image":
            base_url = str(request.base_url).rstrip('/')
            response.download_url = f"{base_url}/api/image/{secret_id}"
        else:
            response.download_url = secret.cloud_url
    elif secret.file_path:
        base_url = str(request.base_url).rstrip('/')
        if secret.content_type == "image":
            response.download_url = f"{base_url}/api/image/{secret_id}"
        elif secret.content_type == "video":
            response.download_url = f"{base_url}/api/video/{secret_id}"
        else:
            response.download_url = f"{base_url}/api/file/{secret_id}"
    
    # Check if we need to clean up
    if secret.view_count >= secret.max_views:
        if secret.content_type == "text":
            # For text, we can delete immediately as content is in response
            delete_secret_immediately(secret_id)
        else:
            # For files/images/videos, we MUST defer deletion
            # The frontend needs to fetch the file URL after this response
            # We'll set a short expiry (5 mins) as a failsafe
            # The file serving endpoint will trigger the actual deletion
            secret.expiry_time = datetime.utcnow() + timedelta(minutes=5)
            db.commit()
    
    return response


@app.get("/api/image/{secret_id}")
@limiter.limit("10/minute")
async def serve_image(
    request: Request,
    secret_id: str,
    background: BackgroundTasks,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Serve image file (proxy from Cloudinary if needed)"""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Manual expiry check to allow "last view" access
    # We allow access if view_count == max_views (since get_secret just incremented it)
    # But deny if it exceeded
    if secret.view_count > secret.max_views:
         raise HTTPException(status_code=404, detail="Secret has expired or already been viewed")
         
    if secret.expiry_time and datetime.utcnow() > secret.expiry_time:
        raise HTTPException(status_code=404, detail="Secret has expired")
    
    if secret.password_hash:
        if not password:
            raise HTTPException(status_code=401, detail="Password required")
        if not verify_password(password, secret.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    if secret.content_type != "image":
        raise HTTPException(status_code=400, detail="This secret is not an image")

    # Schedule deletion if max views reached or exceeded
    if secret.view_count >= secret.max_views:
        background.add_task(delete_secret_immediately, secret_id)
    
    # Use Cloudinary URL if available - PROXY IT
    if secret.cloud_url:
        # Proxy the raw file from Cloudinary but serve with correct mime type
        try:
            async def iterfile():
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", secret.cloud_url) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            yield chunk

            return StreamingResponse(iterfile(), media_type=secret.mime_type or "image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")
    
    # Fallback to local file
    if not secret.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(secret.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type=secret.mime_type
    )


@app.get("/api/video/{secret_id}")
@limiter.limit("10/minute")
async def serve_video(
    request: Request,
    secret_id: str,
    background: BackgroundTasks,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Serve video file with range request support (view count already handled by /api/secrets endpoint)"""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
        
    # Manual expiry check to allow "last view" access
    if secret.view_count > secret.max_views:
         raise HTTPException(status_code=404, detail="Secret has expired or already been viewed")
         
    if secret.expiry_time and datetime.utcnow() > secret.expiry_time:
        raise HTTPException(status_code=404, detail="Secret has expired")
    
    if secret.password_hash:
        if not password:
            raise HTTPException(status_code=401, detail="Password required")
        if not verify_password(password, secret.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    if secret.content_type != "video":
        raise HTTPException(status_code=400, detail="This secret is not a video")
    
    # Schedule deletion if max views reached or exceeded
    if secret.view_count >= secret.max_views:
        background.add_task(delete_secret_immediately, secret_id)

    # Use Cloudinary URL if available
    if secret.cloud_url:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=secret.cloud_url)
    
    # Fallback to local file
    if not secret.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(secret.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Parse Range header for video streaming support
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if len(range_match) > 1 and range_match[1] else file_size - 1
        
        # Ensure end doesn't exceed file size
        end = min(end, file_size - 1)
        chunk_size = end - start + 1
        
        # Create streaming response with range
        def file_iterator():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": secret.mime_type or "video/mp4",
        }
        
        return StreamingResponse(
            file_iterator(),
            status_code=206,  # Partial Content
            headers=headers,
            media_type=secret.mime_type or "video/mp4"
        )
    else:
        # No range header - return full file
        return FileResponse(
            path=file_path,
            media_type=secret.mime_type or "video/mp4",
            headers={"Accept-Ranges": "bytes"}
        )


@app.get("/api/file/{secret_id}")
@limiter.limit("10/minute")
async def serve_file(
    request: Request,
    secret_id: str,
    background: BackgroundTasks,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Serve file for download (view count already handled by /api/secrets endpoint)"""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Manual expiry check to allow "last view" access
    if secret.view_count > secret.max_views:
         raise HTTPException(status_code=404, detail="Secret has expired or already been viewed")
         
    if secret.expiry_time and datetime.utcnow() > secret.expiry_time:
        raise HTTPException(status_code=404, detail="Secret has expired")
    
    if secret.password_hash:
        if not password:
            raise HTTPException(status_code=401, detail="Password required")
        if not verify_password(password, secret.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    if secret.content_type != "file":
        raise HTTPException(status_code=400, detail="This secret is not a file")
    
    # Schedule deletion if max views reached or exceeded
    if secret.view_count >= secret.max_views:
        background.add_task(delete_secret_immediately, secret_id)

    # Use Cloudinary URL if available
    if secret.cloud_url:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=secret.cloud_url)
    
    # Fallback to local file
    if not secret.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(secret.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=secret.file_name,
        media_type=secret.mime_type
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
