import requests
import time
import sys

def verify():
    url = "http://localhost:5000/chat"
    try:
        # Wait a bit for server to start
        time.sleep(2)
        
        # Test 1: Sad message
        print("Sending 'I am sad'...")
        response = requests.post(url, json={"message": "I am sad"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 2: Identity
        print("\nSending 'Who created you?'...")
        response = requests.post(url, json={"message": "Who created you?"})
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200 and "Rae Company" in data.get("response", ""):
            print("SUCCESS: Identity check passed")
        else:
            print("FAILURE: Identity check failed")

    except Exception as e:
        print(f"FAILURE: Could not connect to API. {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
