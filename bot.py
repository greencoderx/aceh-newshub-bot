import os
import tweepy

# X API v2
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")

# Initialize v2 client (read tweets)
client_v2 = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize v1.1 client (to post tweets)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api_v1 = tweepy.API(auth)

# List of Aceh news sources
sources = ["SerambiNews", "AJNN_net", "ModusAceh", "Dialeksis"]

# Keep track of posted tweets (to avoid duplicates)
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
    for username in sources:
        try:
            # Get user ID
            user = client_v2.get_user(username=username)
            user_id = user.data.id

            # Get last 5 tweets
            tweets = client_v2.get_users_tweets(id=user_id, max_results=5, tweet_fields=["created_at","text","id"])
            if not tweets.data:
                print(f"No tweets found for {username}")
                continue

            for t in tweets.data:
                if t.id in posted_ids:
                    continue  # skip duplicates

                # Post tweet as new tweet
                tweet_text = f"{t.text}\n\nSource: @{username}"
                try:
                    api_v1.update_status(tweet_text)
                    print(f"Posted tweet from {username}: {t.id}")
                    save_posted_id(t.id)
                except tweepy.TweepyException as e:
                    print(f"Failed to post tweet {t.id}: {e}")

        except Exception as e:
            print(f"Error fetching tweets from {username}: {e}")

if __name__ == "__main__":
    run_bot()
