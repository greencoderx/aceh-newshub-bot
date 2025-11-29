import os
import tweepy
import time
from datetime import datetime, timedelta, timezone
import requests

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

# Keywords including all Aceh kabupaten/kota
keywords = [
    "Aceh", "Banda Aceh", "Berita", "Disaster",
    "Aceh Barat", "Aceh Barat Daya", "Aceh Besar", "Aceh Jaya",
    "Aceh Selatan", "Aceh Singkil", "Aceh Tamiang", "Aceh Tengah",
    "Aceh Tenggara", "Aceh Timur", "Aceh Utara", "Bener Meriah",
    "Bireuen", "Gayo Lues", "Nagan Raya", "Pidie", "Pidie Jaya",
    "Simeulue", "Subulussalam", "Langsa", "Lhokseumawe", "Meulaboh",
    "Sabang", "Takengon"
]

# Track posted tweet IDs
posted_ids_file = "posted_ids.txt"
if not os.path.exists(posted_ids_file):
    open(posted_ids_file, "w").close()

with open(posted_ids_file, "r") as f:
    posted_ids = set(line.strip() for line in f.readlines())

def save_posted_id(tweet_id):
    with open(posted_ids_file, "a") as f:
        f.write(f"{tweet_id}\n")
    posted_ids.add(tweet_id)

def download_media(url, filename):
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download media {url}: {e}")
        return False

def run_bot():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    total_posted = 0
    total_skipped = 0
    total_errors = 0

    for username in sources:
        try:
            user = client_v2.get_user(username=username)
            if user.data is None:
                print(f"User {username} not found, skipping.")
                total_errors += 1
                continue
            user_id = user.data.id

            tweets = client_v2.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=["created_at", "text", "id", "attachments"],
                expansions=["attachments.media_keys"],
                media_fields=["url", "type"]
            )

            if not tweets.data:
                print(f"No tweets found for {username}")
                total_skipped += 1
                continue

            media_dict = {}
            if tweets.includes and "media" in tweets.includes:
                for m in tweets.includes["media"]:
                    media_dict[m.media_key] = m

            for t in tweets.data:
                if t.id in posted_ids:
                    total_skipped += 1
                    continue

                if t.created_at < one_hour_ago:
                    print(f"Skipping old tweet: {t.id}")
                    total_skipped += 1
                    continue

                if not any(k.lower() in t.text.lower() for k in keywords):
                    print(f"Skipping tweet {t.id} due to missing keywords")
                    total_skipped += 1
                    continue

                # Clean tweet
                tweet_text = " ".join(t.text.split())
                max_len = 280
                if len(tweet_text) + len(f"\n\nSource: @{username}") > max_len:
                    tweet_text = tweet_text[:max_len - len(f"\n\nSource: @{username}") - 3] + "..."
                tweet_text += f"\n\nSource: @{username}"

                # Media handling
                media_ids = []
                if hasattr(t, "attachments") and t.attachments:
                    for key in t.attachments.get("media_keys", []):
                        m = media_dict.get(key)
                        if not m:
                            continue
                        filename = f"{key}"
                        if m.type == "photo":
                            filename += ".jpg"
                            if download_media(m.url, filename):
                                media = api_v1.media_upload(filename)
                                media_ids.append(media.media_id)
                                os.remove(filename)
                        elif m.type in ["video", "animated_gif"]:
                            filename += ".mp4"
                            if download_media(m.url, filename):
                                media = api_v1.media_upload(filename, chunked=True)
                                media_ids.append(media.media_id)
                                os.remove(filename)

                try:
                    api_v1.update_status(status=tweet_text, media_ids=media_ids if media_ids else None)
                    print(f"Posted new tweet from {username}: {t.id}")
                    save_posted_id(t.id)
                    total_posted += 1
                except tweepy.TweepyException as e:
                    print(f"Failed to post tweet {t.id}: {e}")
                    total_errors += 1

            time.sleep(5)

        except tweepy.TooManyRequests:
            print(f"Rate limit hit for {username}. Waiting 60 seconds...")
            time.sleep(60)
            total_errors += 1
        except Exception as e:
            print(f"Error fetching tweets from {username}: {e}")
            total_errors += 1

    # Logging summary
    print("\n=== AcehNewsHub Bot Run Summary ===")
    print(f"Total tweets posted: {total_posted}")
    print(f"Total tweets skipped: {total_skipped}")
    print(f"Total errors: {total_errors}")
    print("=================================\n")

if __name__ == "__main__":
    run_bot()