# Prelim results # 1
# Written by Van Nipper

import os
import time
import json
import base64
import dotenv
from requests import post, get

# Song class: contains artist and song name, overrides equals and hash
class Song:
    def __init__(self, aristName, songName, songId):
        self.artistName = aristName
        self.songName = songName
        self.songId = songId

    def __eq__(self, other):
        return (self.songId == other.songId)
    
    def __hash__(self):
        return hash(self.songId)

# Load spotify data
def load_spotify_data(folder_path):
    all_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_data.extend(data)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON: {file_name}")
    return all_data

# Get a hashSet of unique songs
def get_spotify_song_list(data):
    songList = []
    for entry in data:
        artistName = entry.get('artistName', '').strip()
        songName = entry.get('trackName', '').strip()
        songId = entry.get('songId', '').strip()

        if (artistName.lower() != 'unknown arist' and songName.lower() != 'unknown track'):
            songList.append(Song(artistName, songName, songId))
    
    return set(songList)

# Get API Tokenc
def get_token(client_id, client_secret):
     headers = {
          'Authorization' : 'Basic ' + str(base64.b64encode((client_id + ':' + client_secret).encode('utf-8')), 'utf-8'),
          'Content-Type' : 'application/x-www-form-urlencoded'
     }
     data = {'grant_type' : 'client_credentials'}

     return json.loads(post('https://accounts.spotify.com/api/token', headers=headers, data=data).content)['access_token']

# Get API Auth Header
def get_auth_header(token):
     return {'Authorization' : 'Bearer ' + token}

# Get attributes of a song using spotify's API
def get_song_attributes(token, song):
    url = f"https://api.spotify.com/v1/audio-features/{song.songId}"
    headers = get_auth_header(token)
    response = get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get attributes for {song.songName}: {response.status_code}")
        return None

    data = response.json()
    return {
        "valence": data.get("valence", 0.5),
        "energy": data.get("energy", 0.5),
        "danceability": data.get("danceability", 0.5),
        "tempo": data.get("tempo", 120),
        "acousticness": data.get("acousticness", 0.5),
        "instrumentalness": data.get("instrumentalness", 0.0)
    }

# Moods for user to select from
MOOD_RULES = {
    "happy": {
        "valence_happy": 1.0,
        "energy_energetic": 0.8,
        "dance_high": 0.7
    },
    "sad": {
        "valence_sad": 1.0,
        "energy_calm": 0.8,
        "dance_low": 0.6
    },
    "calm": {
        "energy_calm": 1.0,
        "acoustic_acoustic": 0.8,
        "tempo_slow": 0.7
    },
    "energetic": {
        "energy_energetic": 1.0,
        "tempo_fast": 0.9,
        "dance_high": 0.8
    }
}

# Returns a dictionary of fuzzified songs
def fuzzify_song(song):
    v = song["valence"]
    e = song["energy"]
    d = song["danceability"]
    t = song["tempo"]
    a = song["acousticness"]
    instr = song["instrumentalness"]

    return {
        # Valence
        "valence_sad": trap(v, 0.0, 0.0, 0.15, 0.35),
        "valence_neutral": tri(v, 0.25, 0.5, 0.75),
        "valence_happy": trap(v, 0.65, 0.85, 1.0, 1.0),

        # Energy
        "energy_calm": trap(e, 0.0, 0.0, 0.15, 0.35),
        "energy_moderate": tri(e, 0.25, 0.5, 0.75),
        "energy_energetic": trap(e, 0.65, 0.85, 1.0, 1.0),

        # Danceability
        "dance_low": trap(d, 0.0, 0.0, 0.2, 0.4),
        "dance_medium": tri(d, 0.3, 0.5, 0.7),
        "dance_high": trap(d, 0.6, 0.8, 1.0, 1.0),

        # Tempo (BPM 50–200 typical)
        "tempo_slow": trap(t, 50, 50, 70, 90),
        "tempo_moderate": tri(t, 80, 100, 120),
        "tempo_fast": trap(t, 110, 130, 200, 200),

        # Acousticness
        "acoustic_electronic": trap(a, 0.0, 0.0, 0.15, 0.35),
        "acoustic_mixed": tri(a, 0.25, 0.5, 0.75),
        "acoustic_acoustic": trap(a, 0.65, 0.85, 1.0, 1.0),

        # Instrumentalness
        "instr_vocal": trap(instr, 0.0, 0.0, 0.05, 0.2),
        "instr_mixed": tri(instr, 0.15, 0.35, 0.6),
        "instr_instrumental": trap(instr, 0.5, 0.7, 1.0, 1.0),
    }

# Membership functions
def trap(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    elif a < x < b:
        return (x - a) / (b - a) if b != a else 1.0
    elif b <= x <= c:
        return 1.0
    elif c < x < d:
        return (d - x) / (d - c) if d != c else 1.0
    return 0.0

def tri(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    elif a < x < b:
        return (x - a) / (b - a) if b != a else 1.0
    elif b <= x < c:
        return (c - x) / (c - b) if c != b else 1.0
    return 0.0

# Check fuzzy song's membership for the mood
def score_song_for_mood(fuzzy_song, mood):
    if mood not in MOOD_RULES:
        raise ValueError(f"Unknown mood: {mood}")
    
    rules = MOOD_RULES[mood]
    score = 0.0
    total_weight = 0.0
    for feature, weight in rules.items():
        score += fuzzy_song.get(feature, 0) * weight
        total_weight += weight
    return score / total_weight if total_weight > 0 else 0

# Return recommended playlist
def recommend_playlist(fuzzy_songs_list, songs_with_features, mood, top_n=20):
    scored_songs = [
        (songs_with_features[i], score_song_for_mood(fuzzy_songs_list[i], mood))
        for i in range(len(fuzzy_songs_list))
    ]
    
    # Sort descending by score
    scored_songs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N song attributes
    return scored_songs[:top_n]

if __name__ == "__main__":
    import time

    dotenv.load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    token = get_token(client_id, client_secret)

    # Load Spotify data
    my_data = load_spotify_data('streaminghistory')
    my_songs_set = get_spotify_song_list(my_data)
    my_songs = list(my_songs_set)  # keep order consistent

    songs_with_features = []
    songs_list = []

    for song in my_songs:
        attrs = get_song_attributes(token, song)
        if not attrs:
            # Skip song if attributes couldn't be fetched
            print(f"Skipping {song.artistName} - {song.songName}")
            continue
        songs_with_features.append(attrs)
        songs_list.append(song)
        time.sleep(0.1)

    if not songs_with_features:
        print("No valid songs found. Cannot generate playlist.")
    else:
        # Fuzzify songs
        fuzzy_songs_list = list(map(fuzzify_song, songs_with_features))

        # Prompt user for mood
        while True:
            mood = input("Enter your mood (happy, sad, calm, energetic): ").strip().lower()
            if mood in MOOD_RULES:
                break
            print("Invalid mood. Please choose from: happy, sad, calm, energetic.")

        # Recommend playlist
        playlist = recommend_playlist(fuzzy_songs_list, songs_list, mood, top_n=10)

        print(f"\nRecommended playlist for mood '{mood}':\n")
        for song, score in playlist:
            print(f"{song.artistName} - {song.songName} (score: {score:.2f})")
            