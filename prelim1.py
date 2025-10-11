# minimal_spotify_playlist.py
import os
import json
import time
import base64
import dotenv
from requests import post, get
from flask import Flask, request
from threading import Thread

# Load environment variables
dotenv.load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPES = "user-library-read"

app = Flask(__name__)
user_token = None  # Will be set after login

# ------------------ Spotify Auth ------------------
def login_url():
    url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )
    return url

def exchange_code_for_token(code):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    response = post(url, headers=headers, data=data)
    return response.json().get("access_token")

@app.route("/callback")
def callback():
    global user_token
    code = request.args.get("code")
    user_token = exchange_code_for_token(code)
    return "Login successful! You can return to your terminal."

# ------------------ Spotify Data ------------------
def get_saved_tracks(token, limit=50):
    tracks = []
    url = f"https://api.spotify.com/v1/me/tracks?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}
    while url:
        r = get(url, headers=headers).json()
        for item in r.get("items", []):
            track = item["track"]
            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"]
            })
        url = r.get("next")
    return tracks

def get_audio_features(token, track_ids):
    headers = {"Authorization": f"Bearer {token}"}
    features = []
    for i in range(0, len(track_ids), 100):  # batch max 100 IDs
        batch_ids = track_ids[i:i+100]
        url = f"https://api.spotify.com/v1/audio-features?ids={','.join(batch_ids)}"
        r = get(url, headers=headers)
        try:
            data = r.json()
        except Exception:
            print(f"Failed to decode JSON for batch {i}-{i+len(batch_ids)}: {r.text}")
            continue
        batch_features = data.get("audio_features", [])
        # Skip None tracks
        features.extend([f for f in batch_features if f])
        time.sleep(0.1)  # avoid rate limits
    return features

# ------------------ Minimal Fuzzy Scoring ------------------
def fuzzify(track):
    v = track.get("valence", 0.5)
    e = track.get("energy", 0.5)
    return {
        "valence_happy": max(0, (v-0.5)*2),
        "valence_sad": max(0, (0.5-v)*2),
        "energy_energetic": max(0, (e-0.5)*2),
        "energy_calm": max(0, (0.5-e)*2)
    }

MOOD_RULES = {
    "happy": ["valence_happy", "energy_energetic"],
    "sad": ["valence_sad", "energy_calm"]
}

def score(track_fuzzy, mood):
    features = MOOD_RULES[mood]
    return sum(track_fuzzy[f] for f in features) / len(features)

# ------------------ MAIN ------------------
if __name__ == "__main__":
    print("1️⃣ Open this URL in your browser and log in:")
    print(login_url())
    print("\n2️⃣ After login, Spotify will redirect to your browser. Wait a few seconds...")

    # Run Flask in background thread
    Thread(target=lambda: app.run(port=5000)).start()

    # Wait for token
    while not user_token:
        time.sleep(1)

    # Fetch saved tracks
    tracks = get_saved_tracks(user_token)
    track_ids = [t["id"] for t in tracks]

    # Fetch audio features in batches
    features_list = get_audio_features(user_token, track_ids)

    # Compute fuzzy scores
    fuzzy_tracks = [fuzzify(f) for f in features_list]
    scored_tracks = list(zip(tracks, fuzzy_tracks))

    # Prompt user for mood
    while True:
        mood = input("Enter mood (happy, sad): ").strip().lower()
        if mood in MOOD_RULES:
            break
        print("Invalid mood.")

    # Score and sort
    scored_tracks.sort(key=lambda x: score(x[1], mood), reverse=True)

    print(f"\nTop 10 tracks for mood '{mood}':")
    for track, fuzzy in scored_tracks[:10]:
        print(f"{track['artist']} - {track['name']} (score: {score(fuzzy, mood):.2f})")

    print(f"Total saved tracks fetched: {len(tracks)}")
    print(f"Tracks with audio features: {len(features_list)}")
