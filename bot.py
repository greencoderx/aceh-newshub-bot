import os
import tweepy
from datetime import datetime, timedelta, timezone

# --- X API v2 setup ---
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")

# Tweepy client for v2 (read tweets)
client_v2 = tweepy.Client(bearer_token=BEARER_TOKEN)

# Tweepy API v1.1 client (post tweets)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api_v1 = tweepy.API(auth)

# Aceh news sources
sources = ["SerambiNews", "AJNN_net", "ModusAceh", "Dialeksis"]

# File to track already posted tweet IDs
posted_ids_file = "posted_ids.txt"
if not os.path.exists(posted_ids_file):
    open(posted_ids_file, "w").close()

with open(posted_ids_file, "r") as f:
    posted_ids = set(line.strip() for line in f.readlines())

def save_posted_id(tweet_id):
    with open(posted_ids_file, "a") as f:
        f.write(f"{tweet_id}\n")
    posted_ids.add(tweet_id)

def run_bot():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    for username in sources:
        try:
            # Get user info
            user = client_v2.get_user(username=username)
            user_id = user.data.id

            # Fetch recent tweets (max 5)
            tweets = client_v2.get_users_tweets(
                id=user_id,
                max_results=5,
                tweet_fields=["created_at", "text", "id"]
            )

            if not tweets.data:
                print(f"No tweets found for {username}")
                continue

            for t in tweets.data:
                # Skip duplicates
                if t.id in posted_ids:
                    continue

                # Only post tweets from last hour
                if t.created_at < one_hour_ago:
                    print(f"Skipping old tweet: {t.id}")
                    continue

                # Prepare tweet text
                tweet_text = f"{t.text}\n\nSource: @{username}"

                # Post tweet
                try:
                    api_v1.update_status(tweet_text)
                    print(f"Posted new tweet from {username}: {t.id}")
                    save_posted_id(t.id)
                except tweepy.TweepyException as e:
                    print(f"Failed to post tweet {t.id}: {e}")

        except Exception as e:
            print(f"Error fetching tweets from {username}: {e}")

if __name__ == "__main__":
    run_bot()
