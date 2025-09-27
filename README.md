# Fuzzy Song Recommender (INCOMPLETE)
A personal project that explores how fuzzy logic can be applied to music recommendation.
Instead of relying on opaque algorithms, this recommender uses my own Spotify listening data and a set of fuzzy rules to suggest songs that fit a chosen mood.

# Files / File Structure
streaminghistory/ -> contains JSON files of all my streaming history (not included here for privacy)<br/>
.env -> my spotify developer client and client secret (not included here for privacy)<br/>
songdata.py -> gets the number of unique songs the user has listened to<br/>
streaminghistory.py -> displays the top n songs (in number of times played) (uses matplotlib)<br/>
toolenvprof.py -> queries Spotify's API to display any artists top 10 songs

# NOTE:
You (as a user) will not be able to run this code since the spotify API .env variables and data were removed. If you so choose to add your own environment
variables and streaming data, this program will work as intended.
