from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_password_view_limit():
    print("1. Creating password-protected secret with 1 view...")
    response = client.post(
        "/api/secrets",
        data={
            "content_type": "text", 
            "content": "Secret Data",
            "password": "mypassword",
            "max_views": 1,
            "expiry_hours": 24
        }
    )
    
    if response.status_code != 200:
        print(f"Failed to create secret: {response.text}")
        return
        
    data = response.json()
    secret_id = data["id"]
    print(f"Secret created: {secret_id}")
    
    # 2. Simulate Page Load (Verify endpoint with empty password)
    print("\n2. Simulating First Page Load (Verify call)...")
    response = client.post(
        f"/api/secrets/{secret_id}/verify",
        json={"password": ""}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200 and response.json().get("verified") == False:
        print(">> Correctly returned 'verified: false'")
    else:
        print(">> UNEXPECTED RESPONSE")

    # 3. Simulate Refresh (Verify endpoint with empty password again)
    print("\n3. Simulating Refresh (Second Verify call)...")
    response = client.post(
        f"/api/secrets/{secret_id}/verify",
        json={"password": ""}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print(">> SUCCESS: Secret is still accessible (not expired)")
    else:
        print(">> FAILURE: Secret seems expired/deleted prematurely")

if __name__ == "__main__":
    test_password_view_limit()
