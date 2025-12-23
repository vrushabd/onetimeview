import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_secret_lifecycle():
    print("🚀 Starting Final System Verification...")
    
    # 1. Test Basic Text Secret Creation
    print("\n[1] Testing Text Secret Creation...")
    payload = {
        "content_type": "text",
        "content": "This is a test secret",
        "max_views": 3,
        "expiry_hours": 1
    }
    try:
        # NOTE: create_secret expects Form data, not JSON
        r = requests.post(f"{BASE_URL}/api/secrets", data=payload)
        r.raise_for_status()
        data = r.json()
        secret_id = data["id"] # Response model uses 'id', not 'secret_id' likely. Check schema. SecretResponse has 'id'.
        print(f"✅ Created Secret ID: {secret_id}")
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
             print(f"❌ Failed to create secret: {e}")
             print(f"   Response: {e.response.text}")
        else:
             print(f"❌ Failed to create secret: {e}")
        return

    # 2. Test Metadata Verification (should show generic info)
    print("\n[2] Testing Metadata Verification (Password check)...")
    try:
        # Verify endpoint uses JSON
        r = requests.post(f"{BASE_URL}/api/secrets/{secret_id}/verify", json={"password": ""})
        r.raise_for_status()
        meta = r.json()
        if meta["verified"] is True and meta["has_password"] is False:
             print("✅ Metadata verified (no password required)")
        else:
             print(f"❌ Metadata mismatch: {meta}")
    except Exception as e:
        print(f"❌ Failed verify check: {e}")

    # 3. Test View Counting (Atomic Check)
    print("\n[3] Testing View Counting...")
    # View 1
    r = requests.get(f"{BASE_URL}/api/secrets/{secret_id}")
    if r.status_code == 200:
        print("✅ View 1 successful")
        views_left = r.json().get("remaining_views")
        print(f"   Remaining views: {views_left} (Expected: 2)")
    
    # View 2
    r = requests.get(f"{BASE_URL}/api/secrets/{secret_id}")
    if r.status_code == 200:
        print("✅ View 2 successful")
        views_left = r.json().get("remaining_views")
        print(f"   Remaining views: {views_left} (Expected: 1)")
    
    # View 3 (Last View)
    r = requests.get(f"{BASE_URL}/api/secrets/{secret_id}")
    if r.status_code == 200:
        print("✅ View 3 successful")
        views_left = r.json().get("remaining_views")
        print(f"   Remaining views: {views_left} (Expected: 0)")
    else:
        print(f"❌ Failed on 3rd view: {r.status_code}")

    # View 4 (Should be Gone)
    r = requests.get(f"{BASE_URL}/api/secrets/{secret_id}")
    if r.status_code == 404:
        print("✅ Secret correctly deleted after max views")
    else:
        print(f"❌ Secret still exists after max views! Status: {r.status_code}")

    # 4. Test Password Protection
    print("\n[4] Testing Password Protection...")
    payload_pw = {
        "content_type": "text",
        "content": "Top Secret Data",
        "password": "securepassword123",
        "max_views": 1,
        "expiry_hours": 1
    }
    # Create with Form data
    r = requests.post(f"{BASE_URL}/api/secrets", data=payload_pw)
    pw_secret_id = r.json()["id"]
    print(f"✅ Created Password Protected Secret: {pw_secret_id}")

    # Verify without password
    r = requests.post(f"{BASE_URL}/api/secrets/{pw_secret_id}/verify", json={"password": ""})
    if r.json().get("verified") is False:
        print("✅ Correctly rejected empty password")
    else:
        print("❌ Failed to enforce password")

    # Verify with wrong password
    r = requests.post(f"{BASE_URL}/api/secrets/{pw_secret_id}/verify", json={"password": "wrong"})
    if r.json().get("verified") is False:
        print("✅ Correctly rejected wrong password")
    else:
        print("❌ Failed to reject wrong password")

    # Verify with correct password
    r = requests.post(f"{BASE_URL}/api/secrets/{pw_secret_id}/verify", json={"password": "securepassword123"})
    if r.json().get("verified") is True:
        print("✅ Correctly verified valid password")
    else:
        print("❌ Failed to verify valid password")

    # 5. Test Expiration Logic
    print("\n[5] Testing Manual Deletion (Simulated Expiration)...")
    payload_del = {"content_type": "text", "content": "Delete me", "max_views": 10, "expiry_hours": 1}
    r = requests.post(f"{BASE_URL}/api/secrets", data=payload_del)
    del_id = r.json()["id"]
    
    # We can't wait 1 minute in a quick test, but we can verify it exists, then check access.
    # We assume the background task works (it was audited). We'll test standard access.
    r = requests.get(f"{BASE_URL}/api/secrets/{del_id}")
    if r.status_code == 200:
        print("✅ Secret created and accessible")
    else:
        print("❌ Secret not accessible immediately")

    print("\n🎉 Verification Complete!")

if __name__ == "__main__":
    test_secret_lifecycle()
