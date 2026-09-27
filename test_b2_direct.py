import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv(override=True)

B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")

print(f"Key ID: '{B2_KEY_ID}'")
print(f"App Key: '{B2_APP_KEY}'")
print(f"Endpoint: '{B2_ENDPOINT_URL}'")
print(f"Bucket: '{B2_BUCKET_NAME}'")

client = boto3.client(
    "s3",
    endpoint_url=B2_ENDPOINT_URL,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APP_KEY,
    config=Config(signature_version="s3v4"),
)

try:
    response = client.list_objects_v2(Bucket=B2_BUCKET_NAME, MaxKeys=1)
    print("SUCCESS: connection works!")
except Exception as e:
    print(f"ERROR: {e}")
