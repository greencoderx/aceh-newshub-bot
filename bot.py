import os
import json
import time
from datetime import datetime
import tweepy

# -----------------------------
# Load credentials from env
# -----------------------------
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

print("🚀 Bot starting...")
print("🔑 Tokens loaded?", all([BEARER_TOKEN, API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]))

# -----------------------------
# Tweepy client setup
# -----------------------------
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)

# -----------------------------
# Sources & keywords
# -----------------------------
SOURCES = [
    "infoBMKG","infoBMKG1","Aceh","ModusAceh","acehworldtime","Dialeksis_news",
    "SerambiNews","tribunnews","acehtribun","acehinfo","AcehKoran","kumparan",
    "tempodotco","metro_tv","tvOneNews","detikcom","narasinewsroom","najwashihab",
    "narasitv","matanajwa","beritasatu","weathermonitors","volcaholic1",
    "BBCIndonesia","CNNIndonesia","CNN","trtworld","ALJazeera","AJEnglish","kompascom"
]

KEYWORDS = [
    "Banda Aceh","Aceh Besar","Pidie","Lhokseumawe","Sabang","Bireuen",
    "Langsa","Meulaboh","Simeulue","Gayo Lues","Aceh Jaya","Aceh Tamiang",
    "Aceh Singkil","Aceh Barat","Aceh Barat Daya","Aceh Selatan","Aceh Tenggara",
    "Aceh Timur","Aceh Utara","Aceh Tengah","Aceh Barat Daya","Bener Meriah"
]

# -----------------------------
# Last seen cache
# -----------------------------
LAST_SEEN_FILE = "last_seen.json"
if os.path.exists(LAST_SEEN_FILE):
    with open(LAST_SEEN_FILE, "r") as f:
        last_seen = json.load(f)
else:
    last_seen = {}

# -----------------------------
# Main bot function
# -----------------------------
def run_bot():
    total_posted = 0
    total_skipped = 0
    total_errors = 0

    for source in SOURCES:
        print(f"🔄 Checking tweets from: {source}")
        try:
            tweets = client.get_users_tweets(id=source, max_results=5)  # Adjust API call
            if not tweets or "data" not in tweets or not tweets.data:
                print(f"⚠ No tweets found for {source}")
                continue

            for tweet in tweets.data:
                tweet_id = str(tweet.id)
                if last_seen.get(source) == tweet_id:
                    print(f"⏭ Skipping old tweet: {tweet_id}")
                    total_skipped += 1
                    continue

                text = tweet.text
                if any(kw.lower() in text.lower() for kw in KEYWORDS):
                    try:
                        client.create_tweet(text=text)
                        print(f"✅ Tweet posted: {tweet_id}")
                        total_posted += 1
                        last_seen[source] = tweet_id
                    except Exception as e:
                        print(f"❌ Failed posting tweet {tweet_id}: {e}")
                        total_errors += 1

        except Exception as e:
            print(f"❌ Error fetching tweets from {source}: {e}")
            total_errors += 1
            time.sleep(60)  # wait if rate-limited

    # Save last seen
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(last_seen, f, indent=2)

    # Summary
    print("\n=== AcehNewsHub Bot Run Summary ===")
    print(f"Total tweets posted: {total_posted}")
    print(f"Total tweets skipped: {total_skipped}")
    print(f"Total errors: {total_errors}")
    print("=================================")


# -----------------------------
# Run bot safely
# -----------------------------
if __name__ == "__main__":
    try:
        run_bot()
    except Exception as e:
        print("❌ Bot crashed:", e)