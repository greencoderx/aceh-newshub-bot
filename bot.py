import os
import time
import json
import logging
import requests
import tweepy
from datetime import datetime

# ---------------------------------------
# Logging
# ---------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# ---------------------------------------
# Twitter Authentication
# ---------------------------------------
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)


# ---------------------------------------
# Sources to monitor
# ---------------------------------------
SOURCE_ACCOUNTS = [
    "infoBMKG",
    "BNPB_Indonesia",
    "metoffice",
    "NWS",
]

STATE_FILE = "state.json"


# ---------------------------------------
# Load saved state
# ---------------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


# ---------------------------------------
# Save state
# ---------------------------------------
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# ---------------------------------------
# Dashboard update
# ---------------------------------------
def update_dashboard(last_checked):
    html = f"""
    <html>
    <head><title>Weather Bot Status</title></head>
    <body>
        <h1>Weather Bot Status Dashboard</h1>
        <p><b>Last Updated:</b> {datetime.utcnow().isoformat()} UTC</p>
        <h2>Source Accounts</h2>
        <ul>
            {''.join([f'<li>{src}</li>' for src in SOURCE_ACCOUNTS])}
        </ul>
        <h2>Last Tweet IDs</h2>
        <pre>{json.dumps(last_checked, indent=4)}</pre>
    </body>
    </html>
    """
    with open("status.html", "w") as f:
        f.write(html)


# ---------------------------------------
# Main processing
# ---------------------------------------
def check_and_retweet():
    state = load_state()
    last_checked = state.get("last_checked", {})

    for src in SOURCE_ACCOUNTS:
        logging.info(f"Checking tweets from: {src}")

        try:
            tweets = api.user_timeline(screen_name=src, count=5, tweet_mode="extended")
        except tweepy.TooManyRequests:
            logging.warning("Rate limit hit — skipping this cycle (NO LONG SLEEP).")
            return last_checked
        except Exception as e:
            logging.error(f"Error fetching tweets: {e}")
            continue

        last_seen = last_checked.get(src, None)

        for tweet in reversed(tweets):
            if str(tweet.id) == str(last_seen):
                continue

            logging.info(f"Retweeting: {tweet.id}")
            try:
                api.retweet(tweet.id)
                last_checked[src] = tweet.id
            except tweepy.TooManyRequests:
                logging.warning("Rate limit hit during retweet — skipping remaining tweets.")
                return last_checked
            except Exception as e:
                logging.error(f"Retweet error: {e}")

    return last_checked


# ---------------------------------------
# Run once per workflow (no long sleeping!)
# ---------------------------------------
if __name__ == "__main__":
    logging.info("Bot started — SINGLE RUN MODE")

    last_checked = check_and_retweet()

    save_state({"last_checked": last_checked})
    update_dashboard(last_checked)

    logging.info("Bot finished — ready for next cron run")
