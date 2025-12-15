import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from io import BytesIO

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
        # If file_obj is bytes, wrap it in BytesIO
        if isinstance(file_obj, bytes):
            file_obj = BytesIO(file_obj)
        
        response = cloudinary.uploader.upload(
            file_obj,
            resource_type=resource_type,
            folder="onetimeview_secrets"  # Keep organized
        )
        return {
            "public_id": response.get("public_id"),
            "secure_url": response.get("secure_url"),
            "format": response.get("format"),
            "resource_type": response.get("resource_type")
        }
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

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
