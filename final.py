# Prelim 2
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
    "happy":          {"danceability": 0.8, "energy": 0.8, "valence": 0.7, "acousticness": 0.3, "instrumentalness": 0.1, "liveness": 0.7, "speechiness": 0.2, "tempo": 0.7},
    "sad":            {"danceability": 0.3, "energy": 0.3, "valence": 0.2, "acousticness": 0.7, "instrumentalness": 0.3, "liveness": 0.2, "speechiness": 0.2, "tempo": 0.4},
    "chill":          {"danceability": 0.5, "energy": 0.4, "valence": 0.5, "acousticness": 0.6, "instrumentalness": 0.6, "liveness": 0.3, "speechiness": 0.2, "tempo": 0.4},
    "party":          {"danceability": 0.9, "energy": 0.9, "valence": 0.8, "acousticness": 0.1, "instrumentalness": 0.1, "liveness": 0.4, "speechiness": 0.3, "tempo": 0.8},
    "focus":          {"danceability": 0.4, "energy": 0.3, "valence": 0.4, "acousticness": 0.7, "instrumentalness": 0.7, "liveness": 0.2, "speechiness": 0.1, "tempo": 0.3},
    "workout":        {"danceability": 0.8, "energy": 0.9, "valence": 0.7, "acousticness": 0.1, "instrumentalness": 0.1, "liveness": 0.4, "speechiness": 0.2, "tempo": 0.9},
    "romantic":       {"danceability": 0.6, "energy": 0.5, "valence": 0.7, "acousticness": 0.6, "instrumentalness": 0.2, "liveness": 0.3, "speechiness": 0.2, "tempo": 0.5},
    "angry":          {"danceability": 0.5, "energy": 0.9, "valence": 0.2, "acousticness": 0.1, "instrumentalness": 0.1, "liveness": 0.5, "speechiness": 0.4, "tempo": 0.9},
    "melancholy":     {"danceability": 0.4, "energy": 0.3, "valence": 0.3, "acousticness": 0.8, "instrumentalness": 0.4, "liveness": 0.2, "speechiness": 0.2, "tempo": 0.4},
    "energetic":      {"danceability": 0.8, "energy": 1.0, "valence": 0.8, "acousticness": 0.1, "instrumentalness": 0.1, "liveness": 0.4, "speechiness": 0.3, "tempo": 1.0},
    "sleep":          {"danceability": 0.2, "energy": 0.1, "valence": 0.3, "acousticness": 0.9, "instrumentalness": 0.8, "liveness": 0.1, "speechiness": 0.1, "tempo": 0.2},
}

# Get target mood from user
while True:
    print("\nAvailable moods:")
    print(", ".join(sorted(mood_targets.keys())))
    mood = input("\nEnter mood: ").lower().strip()
    if mood not in mood_targets:
        print("Please choose from the list provided.")
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


# Example Spotify playlist (defined manually from spotify auto-generated playlist)
spotify_happy_playlist = [
    {"track_name": "Brand New", "artist": "Ben Rector"},
    {"track_name": "I'm Yours", "artist": "Jason Mraz"},
    {"track_name": "Talk Too Much", "artist": "COIN"},
    {"track_name": "As It Was", "artist": "Harry Styles"},
    {"track_name": "Cutie", "artist": "COIN"},
    {"track_name": "Mr. Brightside", "artist": "The Killers"},
    {"track_name": "All Star", "artist": "Smash Mouth"}, # not found
    {"track_name": "Build Your Kingdom Here", "artist": "Rend Collective"},
    {"track_name": "House of The Lord", "artist": "Phil Wickham"},
    {"track_name": "Crash My Car", "artist": "COIN"}
]

# Find scores of those songs in your dataset
comparison_rows = []
for song in spotify_happy_playlist:
    name = song["track_name"].lower()
    artist = song["artist"].lower()
    match = df[(df["track_name"].str.lower() == name) &
               (df["artists"].str.lower().str.contains(artist))]
    if not match.empty:
        row = match.iloc[0]
        comparison_rows.append({
            "track_name": row["track_name"],
            "artist": row["artists"],
            "mood_score": row["mood_score"]
        })
    else:
        comparison_rows.append({
            "track_name": song["track_name"],
            "artist": song["artist"],
            "mood_score": None
        })

# Create dataframe for clarity
comparison_df = pd.DataFrame(comparison_rows)

# Calculate averages and print comparison
print("\nComparison with Spotify playlist:\n")
print(comparison_df)

valid_scores = comparison_df["mood_score"].dropna()
if not valid_scores.empty:
    avg_generated = top_tracks["mood_score"].mean()
    avg_spotify = valid_scores.mean()
    print(f"\nAverage mood score of generated playlist: {avg_generated:.3f}")
    print(f"Average mood score of Spotify playlist:  {avg_spotify:.3f}")
    print(f"Difference: {abs(avg_generated - avg_spotify):.3f}")
else:
    print("⚠️ None of the Spotify playlist songs were found in the dataset.")
