import os
import json
from collections import Counter

def load_spotify_data(folder_path):
    """Load all Spotify JSON files from the given folder into a single list."""
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

def count_song_plays(data):
    """Count how many times each (artist, track) pair appears, ignoring 'Unknown'."""
    counter = Counter()
    for entry in data:
        artist = entry.get("artistName", "").strip()
        track = entry.get("trackName", "").strip()

        # skip unknowns
        if artist.lower() == "unknown artist" or track.lower() == "unknown track":
            continue  

        song_key = f"{artist} - {track}"
        counter[song_key] += 1
    return counter

if __name__ == "__main__":
    folder_path = "streaminghistory"
    data = load_spotify_data(folder_path)
    counter = count_song_plays(data)
    print(len(counter)) 
