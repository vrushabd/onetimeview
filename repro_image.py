from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_image_flow():
    # 1. Create a dummy image file
    with open("test_image.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    try:
        # 2. Upload the image secret
        print("Uploading secret...")
        with open("test_image.png", "rb") as f:
            response = client.post(
                "/api/secrets",
                data={
                    "content_type": "image", 
                    "max_views": 1,
                    "expiry_hours": 24
                },
                files={"file": ("test_image.png", f, "image/png")}
            )
        
        if response.status_code != 200:
            print(f"Failed to create secret: {response.text}")
            return
            
        data = response.json()
        secret_id = data["id"]
        print(f"Secret created: {secret_id}")
        
        # 3. Get secret metadata (this triggers view count increment)
        print("Fetching secret metadata...")
        response = client.get(f"/api/secrets/{secret_id}")
        if response.status_code != 200:
             print(f"Failed to get secret: {response.text}")
             return
        
        view_data = response.json()
        print(f"Download URL: {view_data['download_url']}")
        
        # 4. Fetch the image content (this mimics the browser request)
        print("Fetching image content...")
        # Extract path from URL or just construct it
        image_path = f"/api/image/{secret_id}"
        response = client.get(image_path)
        
        if response.status_code == 200:
            print(f"SUCCESS: Image fetched. Size: {len(response.content)} bytes")
        else:
            print(f"FAILURE: Failed to fetch image. Status: {response.status_code}")
            print(f"Response: {response.text}")

    finally:
        if os.path.exists("test_image.png"):
            os.remove("test_image.png")

if __name__ == "__main__":
    test_image_flow()
