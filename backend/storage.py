import os
import uuid
import logging
import traceback
from io import BytesIO
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_b2_endpoint_url():
    endpoint = os.getenv("B2_ENDPOINT_URL")
    if not endpoint:
        return endpoint

    endpoint = endpoint.strip()
    if "://" not in endpoint:
        endpoint = f"https://{endpoint}"

    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(
            "Invalid B2_ENDPOINT_URL. Use a full Backblaze S3 endpoint, "
            "for example: https://s3.us-east-005.backblazeb2.com"
        )

    return endpoint.rstrip("/")


def _get_client():
    """Create and return a boto3 S3 client configured for Backblaze B2."""
    load_dotenv(find_dotenv(usecwd=True), override=True)
    _require_b2_config()
    return boto3.client(
        "s3",
        endpoint_url=_get_b2_endpoint_url(),
        aws_access_key_id=os.getenv("B2_KEY_ID"),
        aws_secret_access_key=os.getenv("B2_APP_KEY"),
        config=Config(signature_version="s3v4"),
    )


def _require_b2_config():
    required = ("B2_ENDPOINT_URL", "B2_KEY_ID", "B2_APP_KEY", "B2_BUCKET_NAME")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Backblaze B2 is not configured. Missing: {', '.join(missing)}")
    _get_b2_endpoint_url()


def upload_file(file_obj, resource_type="raw", original_filename=None):
    """
    Upload a file to Backblaze B2.
    Accepts bytes or file-like objects.
    Returns a dictionary with 'public_id' (the B2 file key) and 'secure_url'.
    """
    try:
        _require_b2_config()
        b2_endpoint = _get_b2_endpoint_url()
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
    Permanently delete a file from Backblaze B2 by its file key.
    Deletes all object versions and delete markers so no hidden versions or (2) * marks remain.
    resource_type is kept for API compatibility but unused for B2.
    """
    try:
        _require_b2_config()
        client = _get_client()
        bucket = os.getenv("B2_BUCKET_NAME")

        # In Backblaze B2, versioned buckets retain previous versions and place
        # a delete marker when standard delete_object is called. To hard-delete
        # permanently, we must delete every version ID and delete marker explicitly.
        versions_to_delete = []
        try:
            paginator = client.get_paginator("list_object_versions")
            for page in paginator.paginate(Bucket=bucket, Prefix=file_key):
                for v in page.get("Versions", []):
                    if v["Key"] == file_key:
                        versions_to_delete.append({"Key": file_key, "VersionId": v["VersionId"]})
                for m in page.get("DeleteMarkers", []):
                    if m["Key"] == file_key:
                        versions_to_delete.append({"Key": file_key, "VersionId": m["VersionId"]})
        except Exception as list_err:
            logger.warning(f"Failed to list object versions for {file_key}: {list_err}")

        if versions_to_delete:
            for i in range(0, len(versions_to_delete), 1000):
                chunk = versions_to_delete[i:i + 1000]
                client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": chunk, "Quiet": True}
                )
            logger.info(f"B2 permanent purge successful ({len(versions_to_delete)} versions/markers) — key: {file_key}")
            return True

        # Fallback to standard delete if no versions were found
        client.delete_object(Bucket=bucket, Key=file_key)
        logger.info(f"B2 standard delete successful — key: {file_key}")
        return True
    except ClientError as e:
        logger.error(f"B2 delete ClientError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"B2 delete unexpected error: {str(e)}")
        return False


def purge_orphaned_b2_files(active_keys=None):
    """
    Scans Backblaze B2 and permanently deletes:
    1. All lingering delete markers (which show as (2) * in the B2 console).
    2. All file versions whose key is not in active_keys (if active_keys is provided).
    """
    try:
        _require_b2_config()
        client = _get_client()
        bucket = os.getenv("B2_BUCKET_NAME")
        paginator = client.get_paginator("list_object_versions")

        to_delete = []
        for page in paginator.paginate(Bucket=bucket):
            for m in page.get("DeleteMarkers", []):
                to_delete.append({"Key": m["Key"], "VersionId": m["VersionId"]})
            if active_keys is not None:
                for v in page.get("Versions", []):
                    if v["Key"] not in active_keys:
                        to_delete.append({"Key": v["Key"], "VersionId": v["VersionId"]})

        if to_delete:
            for i in range(0, len(to_delete), 1000):
                chunk = to_delete[i:i + 1000]
                client.delete_objects(Bucket=bucket, Delete={"Objects": chunk, "Quiet": True})
            logger.info(f"B2 orphaned purge complete: purged {len(to_delete)} items.")
        return len(to_delete)
    except Exception as e:
        logger.error(f"Error purging orphaned B2 files: {e}")
        return 0


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
