# Prelim 1
# Written by Van Nipper

import pandas as pd
import json
import glob
from sklearn.preprocessing import MinMaxScaler
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Load spotify csv data from Kaggle
df = kagglehub.dataset_load(
    KaggleDatasetAdapter.PANDAS,
    "maharshipandya/-spotify-tracks-dataset",
    path="dataset.csv"
)
print(f"Dataset loaded. {len(df)} songs are available.")

# Define features
numeric_features = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
    "tempo"
]

# Get rid of unnecessary data
df = df.dropna(subset=numeric_features + ["track_name", "artists"]) 
scaler = MinMaxScaler()
df[numeric_features] = scaler.fit_transform(df[numeric_features])

# Load user's streaming history from JSON files (local)
user_tracks = set()
for file in glob.glob("./streaminghistory/*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            track_name = entry.get("trackName", "").lower()
            artist = entry.get("artistName", "").split(";")[0].lower()
            if track_name and artist:
                user_tracks.add((track_name, artist))

# Remove all songs from the dataset that the user hasn't listened to
def in_user_history(row):
    track_name = str(row["track_name"]).lower() if pd.notnull(row["track_name"]) else ''
    artist = str(row["artists"]).split(";")[0].lower() if pd.notnull(row["artists"]) else ''
    return (track_name, artist) in user_tracks

df = df[df.apply(in_user_history, axis=1)]
print(f"{len(df)} songs remain after filtering.")

# Exist if no matching tracks are found
if df.empty:
    print("No matching tracks found. Exiting.")
    exit()

# Remove duplicate tracks
df["artist_primary"] = df["artists"].apply(lambda x: str(x).split(";")[0].lower())
df = df.drop_duplicates(subset=["track_name", "artist_primary"])

# Fuzzy mood matching definitions
mood_targets = {
    "happy": {"valence": 0.8, "energy": 0.8, "danceability": 0.7},
    "sad": {"valence": 0.2, "energy": 0.3, "acousticness": 0.6},
    "chill": {"valence": 0.5, "energy": 0.4, "instrumentalness": 0.5},
    "party": {"valence": 0.7, "energy": 0.9, "danceability": 0.9}
}

# Get target mood from user
while True:
    mood = input("\nEnter mood (happy/sad/chill/party): ").lower().strip()
    if mood not in mood_targets:
        print("Please choose from happy, sad, chill, or party.")
    else:
        break
target = mood_targets[mood]

# Perform fuzzy matching
def mood_score(row, target_dict):
    score = 0
    for feature, value in target_dict.items():
        score += (1 - abs(row[feature] - value))  # closer = better
    return score / len(target_dict)

df["mood_score"] = df.apply(lambda row: mood_score(row, target), axis=1)

# Recommend top ten songs (10 song playlist)
top_tracks = df.sort_values("mood_score", ascending=False).head(10)
print(f"Top 10 tracks for mood '{mood}':\n")
for i, row in enumerate(top_tracks.itertuples(), start=1):
    print(f"{i}. {row.track_name} — {row.artists}  "
          f"(Genre: {row.track_genre}, Score: {row.mood_score:.3f})")
