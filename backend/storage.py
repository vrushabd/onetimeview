import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from io import BytesIO
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_file(file_obj, resource_type="auto"):
    """
    Upload a file to Cloudinary.
    Accepts bytes or file-like objects.
    Returns a dictionary with 'public_id', 'secure_url', and 'format'.
    """
    try:
        # Log configuration (without exposing secrets)
        logger.info(f"Cloudinary config - Cloud Name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
        logger.info(f"API Key exists: {bool(os.getenv('CLOUDINARY_API_KEY'))}")
        logger.info(f"API Secret exists: {bool(os.getenv('CLOUDINARY_API_SECRET'))}")
        logger.info(f"Resource type: {resource_type}")
        
        size_bytes = None

        # If file_obj is bytes, wrap it in BytesIO
        if isinstance(file_obj, bytes):
            size_bytes = len(file_obj)
            logger.info(f"Converting bytes to BytesIO (size: {size_bytes} bytes)")
            file_obj = BytesIO(file_obj)
            file_obj.name = "upload.dat" # Cloudinary often needs a name
            file_obj.seek(0)
        else:
            try:
                # Try to detect size if possible
                pos = file_obj.tell()
                file_obj.seek(0, 2)
                size_bytes = file_obj.tell()
                file_obj.seek(pos)
            except Exception:
                pass

        # Cloudinary free tier enforces a 10MB limit on basic uploads.
        # Use chunked upload for larger files (videos/raw up to our 100MB limit).
        if size_bytes and size_bytes > 10 * 1024 * 1024 and resource_type in {"raw", "video"}:
            logger.info(f"Using chunked upload for size {size_bytes} bytes")
            response = cloudinary.uploader.upload_large(
                file_obj,
                resource_type=resource_type,
                folder="onetimeview_secrets",
                chunk_size=6 * 1024 * 1024,  # 6MB chunks to stay under 10MB gateway
                eager_async=True
            )
        else:
            response = cloudinary.uploader.upload(
                file_obj,
                resource_type=resource_type,
                folder="onetimeview_secrets"  # Keep organized
            )
        
        logger.info(f"Upload successful - Public ID: {response.get('public_id')}")
        
        return {
            "public_id": response.get("public_id"),
            "secure_url": response.get("secure_url"),
            "format": response.get("format"),
            "resource_type": response.get("resource_type")
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise e

def delete_file(public_id, resource_type="auto"):
    """
    Delete a file from Cloudinary by public_id.
    """
    try:
        # For raw files (like zip, generic types), resource_type might need to be specific
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return True
    except Exception as e:
        print(f"Cloudinary delete error: {e}")
        return False
