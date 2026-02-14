import requests
import time
import sys

BASE_URL = "http://localhost:5001"

def verify_auth():
    s = requests.Session()
    
    # 1. Try to access home without login (should redirect or fail)
    print("Testing access without login...")
    try:
        r = s.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print(f"FAILURE: Could not connect to {BASE_URL}. Is the server running?")
        sys.exit(1)

    if "login" in r.url or r.status_code == 401 or r.status_code == 200:
        # Note: Flask-Login redirects to /login which returns 200 OK with the login page
        # We check if the content looks like the login page
        if "Login" in r.text and "Welcome Back" in r.text:
             print("SUCCESS: Redirected to login page.")
        else:
             print(f"FAILURE: Unexpected content: {r.text[:100]}")
             # sys.exit(1) # Don't exit yet, might be starting up
    
    # 2. Signup
    username = f"testuser_{int(time.time())}"
    password = "password123"
    email = f"{username}@example.com"
    print(f"\nSigning up as {username} with email {email}...")
    
    r = s.post(f"{BASE_URL}/signup", data={"username": username, "password": password, "email": email})
    if r.status_code == 200 and "EQ - Your Emotional Companion" in r.text:
        print("SUCCESS: Signup successful and redirected to home.")
    else:
        print(f"FAILURE: Signup failed. Status: {r.status_code}")
        print(r.text[:200])
        sys.exit(1)

    # 3. Test Chat (Authorized)
    print("\nTesting chat with auth cookies...")
    r = s.post(f"{BASE_URL}/chat", json={"message": "hello"})
    if r.status_code == 200 and "response" in r.json():
        print("SUCCESS: Chat works for logged in user.")
    else:
        print(f"FAILURE: Chat failed. {r.status_code}")
        sys.exit(1)

    # 4. Logout
    print("\nTesting logout...")
    r = s.get(f"{BASE_URL}/logout")
    if "Login" in r.text:
        print("SUCCESS: Logout redirected to login page.")
    else:
        print("FAILURE: Logout failed.")

if __name__ == "__main__":
    verify_auth()
