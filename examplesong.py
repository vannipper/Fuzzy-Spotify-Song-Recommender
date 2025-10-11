import os
import json
import base64
from requests import post, get
import dotenv

# Get API token
def get_token(client_id, client_secret):
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    response = post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    return response.json()['access_token']

# Get auth header
def get_auth_header(token):
    return {'Authorization': 'Bearer ' + token}

# Search for a track
def search_track(token, artist, track_name):
    query = f"{track_name} artist:{artist}"
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    if response.status_code != 200:
        print(f"Search failed: {response.status_code}")
        return None
    items = response.json().get("tracks", {}).get("items", [])
    if not items:
        print("Track not found.")
        return None
    return items[0]["id"], items[0]["name"], items[0]["artists"][0]["name"]

# Get audio features for a track
def get_audio_features(token, track_id):
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get audio features: {response.status_code}")
        return None
    return response.json()

if __name__ == "__main__":
    dotenv.load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token = get_token(client_id, client_secret)

    track_id, track_name, artist_name = search_track(token, "Taylor Swift", "Love Story")
    if track_id:
        print(f"Found track: {artist_name} - {track_name} (ID: {track_id})")
        features = get_audio_features(token, track_id)
        print("Audio features:")
        print(json.dumps(features, indent=2))
