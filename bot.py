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
    per_source_stats = {}

    for source in SOURCES:
        posted = 0
        skipped = 0
        errors = 0
        print(f"🔄 Checking tweets from: {source}")
        try:
            tweets = client.get_users_tweets(id=source, max_results=5)
            if not tweets or "data" not in tweets or not tweets.data:
                print(f"⚠ No tweets found for {source}")
                continue

            for tweet in tweets.data:
                tweet_id = str(tweet.id)
                if last_seen.get(source) == tweet_id:
                    skipped += 1
                    total_skipped += 1
                    print(f"⏭ Skipping old tweet: {tweet_id}")
                    continue

                text = tweet.text
                if any(kw.lower() in text.lower() for kw in KEYWORDS):
                    try:
                        client.create_tweet(text=text)
                        posted += 1
                        total_posted += 1
                        last_seen[source] = tweet_id
                        print(f"✅ Tweet posted: {tweet_id}")
                    except Exception as e:
                        errors += 1
                        total_errors += 1
                        print(f"❌ Failed posting tweet {tweet_id}: {e}")

        except Exception as e:
            errors += 1
            total_errors += 1
            print(f"❌ Error fetching tweets from {source}: {e}")
            time.sleep(60)

        per_source_stats[source] = {"posted": posted, "skipped": skipped, "errors": errors}

    # Save last seen
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(last_seen, f, indent=2)

    # -----------------------------
    # Generate dashboard HTML in gh-pages folder
    # -----------------------------
    DASHBOARD_DIR = "gh-pages"
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    DASHBOARD_FILE = os.path.join(DASHBOARD_DIR, "index.html")

    with open(DASHBOARD_FILE, "w") as f:
        f.write(f"""
<html>
<head>
<title>AcehNewsHub Bot Status</title>
<meta http-equiv="refresh" content="600">
<style>
body {{ font-family: Arial, sans-serif; background:#f5f5f5; color:#333; padding:2rem; }}
h1 {{ color:#2a9d8f; }}
table {{ border-collapse: collapse; width:80%; }}
td, th {{ border:1px solid #999; padding:8px; text-align:left; }}
</style>
</head>
<body>
<h1>AcehNewsHub Bot Status</h1>
<p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<h2>Summary</h2>
<table>
<tr><th>Total Tweets Posted</th><td>{total_posted}</td></tr>
<tr><th>Total Tweets Skipped</th><td>{total_skipped}</td></tr>
<tr><th>Total Errors</th><td>{total_errors}</td></tr>
</table>
<h2>Per-Source Stats</h2>
<table>
<tr><th>Source</th><th>Posted</th><th>Skipped</th><th>Errors</th></tr>
""")
        for source, stats in per_source_stats.items():
            f.write(f"<tr><td>{source}</td><td>{stats['posted']}</td><td>{stats['skipped']}</td><td>{stats['errors']}</td></tr>\n")

        f.write("""
</table>
</body>
</html>
""")
    print(f"📊 Dashboard updated: {DASHBOARD_FILE}")

    # Final summary
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