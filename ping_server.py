import requests
import sys

try:
    response = requests.get('http://127.0.0.1:5000/')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Server is responsive.")
        if "RAE" in response.text:
            print("Welcome page content verified.")
        else:
            print("Welcome page content missing.")
    else:
        print("Server returned unexpected status.")
except Exception as e:
    print(f"Failed to connect: {e}")
