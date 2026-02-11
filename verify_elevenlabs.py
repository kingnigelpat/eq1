import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "nzFihrBIvB34imQBuxub" # The male voice user requested

if not API_KEY:
    print("❌ Error: ELEVENLABS_API_KEY not found in .env file.")
    exit()

print(f"✅ Found API Key: {API_KEY[:5]}...{API_KEY[-4:]}")

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "text": "This is a test of the Eleven Labs integration.",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
}

print(f"Testing Voice ID: {VOICE_ID}...")
try:
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ ElevenLabs API Call Successful!")
        print(f"Received {len(response.content)} bytes of audio data.")
        with open("test_eleven.mp3", "wb") as f:
            f.write(response.content)
        print("Saved to test_eleven.mp3")
    else:
        print(f"❌ ElevenLabs API Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Exception: {e}")
