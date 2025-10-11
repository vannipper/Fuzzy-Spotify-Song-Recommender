import os
import json
import requests
import dotenv
from urllib.parse import urlencode
from flask import Flask, request

dotenv.load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"  # Must match your Spotify app settings
SCOPES = "user-library-read user-read-recently-played"

app = Flask(__name__)

# Step 1: Generate Spotify login URL
def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES
    }
    url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return url

# Step 2: Exchange code for token
def get_token(code):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    return response.json()  # Contains access_token, refresh_token

# Step 3: Fetch saved tracks
def fetch_saved_tracks(access_token, limit=20):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/me/tracks?limit={limit}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch tracks:", response.status_code)
        return []
    return response.json()["items"]

# Step 4: Get audio features for a track
def get_audio_features(access_token, track_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get audio features for {track_id}: {response.status_code}")
        return None
    return response.json()

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = get_token(code)
    access_token = token_info.get("access_token")
    if not access_token:
        return "Failed to get access token."

    # Fetch first 10 saved tracks
    tracks = fetch_saved_tracks(access_token, limit=10)
    print("\nFetched tracks:")
    for item in tracks:
        track = item["track"]
        features = get_audio_features(access_token, track["id"])
        print(f"{track['artists'][0]['name']} - {track['name']}: {features}")

    return "Check your console for the track list with audio features."

if __name__ == "__main__":
    print("Open this URL in your browser to login to Spotify:")
    print(get_auth_url())
    app.run(port=5000)
