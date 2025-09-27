# Prelim results # 1
# Written by Van Nipper

import os
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

# Get API Token
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

def get_song_attributes(token, song):
    pass

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

if __name__ == "__main__":
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    token = get_token(client_id, client_secret)

    my_data = load_spotify_data('streaminghistory')
    my_songs = get_spotify_song_list(my_data)

    # GET SONG ATTRIBUTES HERE FROM SPOTIFY API

    fuzzy_songs_list = list(map(fuzzify_song, my_songs))