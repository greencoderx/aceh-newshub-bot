import os
import json
import tweepy
import time
from datetime import datetime, timezone

# -----------------------------
# X API AUTH
# -----------------------------
api_key = os.getenv("X_API_KEY")
api_secret = os.getenv("X_API_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_secret = os.getenv("X_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(
    api_key, api_secret, access_token, access_secret
)
api = tweepy.API(auth)

# -----------------------------
# CONFIG: LIST OF SOURCES
# -----------------------------
SOURCES = [
    "infoBMKG","infoBMKG1","Aceh","ModusAceh","acehworldtime",
    "Dialeksis_news","SerambiNews","tribunnews","acehtribun",
    "acehinfo","AcehKoran","kumparan","tempodotco","metro_tv",
    "tvOneNews","detikcom","narasinewsroom","najwashihab",
    "narasitv","matanajwa","beritasatu","weathermonitors",
    "volcaholic1","BBCIndonesia","CNNIndonesia","CNN",
    "trtworld","ALJazeera","AJEnglish","kompascom"
]

# -----------------------------
# SIMPLE STATE STORAGE
# -----------------------------
STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

# Initialize missing keys
for src in SOURCES:
    if src not in state:
        state[src] = {"last_id": None}

# -----------------------------
# FETCH AND RETWEET
# -----------------------------
def process_source(username):
    print(f"Checking: @{username}")

    last_seen = state[username]["last_id"]

    try:
        tweets = api.user_timeline(
            screen_name=username,
            count=5,
            tweet_mode="extended",
            since_id=last_see
