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

# List of Aceh news sources
sources = [
    "SerambiNews",
    "AJNN_net",
    "ModusAceh",
    "Dialeksis",
    "GoAcehco",
    "HABAaceh",
]

def run_bot():
    for source in sources:
        try:
            tweets = api.user_timeline(
                screen_name=source,
                count=5,
                tweet_mode="extended"
            )

            for t in tweets:
                try:
                    api.retweet(t.id)
                    print(f"Retweeted from {source}: {t.id}")
                except tweepy.TweepyException:
                    pass

        except Exception as e:
            print("Error fetching tweets:", e)

if __name__ == "__main__":
    run_bot()
