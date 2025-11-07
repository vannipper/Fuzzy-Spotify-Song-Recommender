# check_song_in_dataset.py
# Written by Van Nipper

import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter

# -----------------------------------------------
# Load Spotify dataset
# -----------------------------------------------
print("📥 Loading Spotify dataset from Kaggle...")
df = kagglehub.dataset_load(
    KaggleDatasetAdapter.PANDAS,
    "maharshipandya/-spotify-tracks-dataset",
    path="dataset.csv"
)
print(f"✅ Dataset loaded with {len(df)} songs.\n")

# Ensure columns are valid
if "track_name" not in df.columns or "artists" not in df.columns:
    raise ValueError("Dataset missing expected columns: 'track_name' or 'artists'.")

# -----------------------------------------------
# Function to check if a song/artist exists
# -----------------------------------------------
def check_song_in_dataset(song_name, artist_name):
    # Convert both dataset and input to lowercase for matching
    song_name = song_name.lower().strip()
    artist_name = artist_name.lower().strip()

    matches = df[
        (df["track_name"].str.lower().str.contains(song_name, na=False)) &
        (df["artists"].str.lower().str.contains(artist_name, na=False))
    ]

    if matches.empty:
        print(f"❌ '{song_name.title()}' by {artist_name.title()} not found in dataset.")
    else:
        print(f"✅ Found {len(matches)} match(es) for '{song_name.title()}' by {artist_name.title()}:\n")
        print(matches[["track_name", "artists", "track_genre"]].head(10).to_string(index=False))

# -----------------------------------------------
# Interactive loop
# -----------------------------------------------
while True:
    print("\n🔍 Enter a song to search (or type 'exit' to quit):")
    song = input("Song name: ").strip()
    if song.lower() == "exit":
        break
    artist = input("Artist name: ").strip()
    if artist.lower() == "exit":
        break

    check_song_in_dataset(song, artist)
