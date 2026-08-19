import os
import uuid
import logging
import traceback
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_client():
    """Create and return a boto3 S3 client configured for Backblaze B2."""
    load_dotenv(find_dotenv(usecwd=True), override=True)
    _require_b2_config()
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("B2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("B2_KEY_ID"),
        aws_secret_access_key=os.getenv("B2_APP_KEY"),
        config=Config(signature_version="s3v4"),
    )


def _require_b2_config():
    required = ("B2_ENDPOINT_URL", "B2_KEY_ID", "B2_APP_KEY", "B2_BUCKET_NAME")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Backblaze B2 is not configured. Missing: {', '.join(missing)}")


def upload_file(file_obj, resource_type="raw", original_filename=None):
    """
    Upload a file to Backblaze B2.
    Accepts bytes or file-like objects.
    Returns a dictionary with 'public_id' (the B2 file key) and 'secure_url'.
    """
    try:
        _require_b2_config()
        b2_endpoint = os.getenv("B2_ENDPOINT_URL")
        b2_bucket = os.getenv("B2_BUCKET_NAME")
        logger.info(f"B2 upload — endpoint: {b2_endpoint}, bucket: {b2_bucket}")

        # Wrap bytes in BytesIO
        if isinstance(file_obj, bytes):
            file_obj = BytesIO(file_obj)
            file_obj.seek(0)

        # Determine extension from original filename
        ext = ""
        if original_filename and "." in original_filename:
            ext = "." + original_filename.rsplit(".", 1)[-1].lower()

        # Generate a unique key under the secrets/ folder
        file_key = f"secrets/{uuid.uuid4()}{ext}"

        # Determine content type
        import mimetypes
        content_type = "application/octet-stream"
        if original_filename:
            detected, _ = mimetypes.guess_type(original_filename)
            if detected:
                content_type = detected

        client = _get_client()
        client.upload_fileobj(
            file_obj,
            b2_bucket,
            file_key,
            ExtraArgs={"ContentType": content_type},
        )

        logger.info(f"B2 upload successful — key: {file_key}")

        # Build a base URL (for private buckets we generate presigned URLs at serve time)
        secure_url = f"{b2_endpoint.rstrip('/')}/{b2_bucket}/{file_key}"

        return {
            "public_id": file_key,
            "secure_url": secure_url,
            "resource_type": resource_type,
        }

    except Exception as e:
        logger.error(f"B2 upload error: {str(e)}")
        logger.error(traceback.format_exc())
        raise e


def delete_file(file_key, resource_type="raw"):
    """
    Delete a file from Backblaze B2 by its file key.
    resource_type is kept for API compatibility but unused for B2.
    """
    try:
        _require_b2_config()
        client = _get_client()
        client.delete_object(Bucket=os.getenv("B2_BUCKET_NAME"), Key=file_key)
        logger.info(f"B2 delete successful — key: {file_key}")
        return True
    except ClientError as e:
        logger.error(f"B2 delete ClientError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"B2 delete unexpected error: {str(e)}")
        return False


def generate_presigned_url(file_key, expiry_seconds=300, filename=None, as_attachment=False):
    """
    Generate a short-lived presigned URL for a private B2 file.
    Default expiry: 5 minutes.
    """
    try:
        _require_b2_config()
        client = _get_client()
        params = {"Bucket": os.getenv("B2_BUCKET_NAME"), "Key": file_key}
        if filename:
            disposition_type = "attachment" if as_attachment else "inline"
            safe_filename = filename.replace('"', "")
            params["ResponseContentDisposition"] = f'{disposition_type}; filename="{safe_filename}"'

        url = client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expiry_seconds,
        )
        logger.info(f"Presigned URL generated for key: {file_key}")
        return url
    except Exception as e:
        logger.error(f"B2 presigned URL error: {str(e)}")
        raise e
