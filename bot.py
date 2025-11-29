import os
import tweepy

API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(
    API_KEY, API_SECRET,
    ACCESS_TOKEN, ACCESS_SECRET
)
api = tweepy.API(auth)

sources = [
    "SerambiNews",
    "AJNN_net",
    "ModusAceh",
    "Dialeksis",
]

def run_bot():
    for source in sources:
        print(f"Checking tweets from: {source}")
        try:
            tweets = api.user_timeline(
                screen_name=source,
                count=5,
                tweet_mode="extended"
            )

            if not tweets:
                print(f"No tweets found for {source}")
                continue

            for t in tweets:
                try:
                    print(f"Attempting retweet: {t.id} - {t.full_text[:50]}...")
                    api.retweet(t.id)
                    print(f"Retweeted successfully: {t.id}")
                except tweepy.TweepyException as e:
                    print(f"Failed to retweet {t.id}: {e}")

        except Exception as e:
            print(f"Error fetching tweets from {source}: {e}")

if __name__ == "__main__":
    run_bot()
