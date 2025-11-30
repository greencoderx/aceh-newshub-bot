import os
import json
import time
from datetime import datetime
import tweepy

# Load credentials from environment
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

print("🚀 Bot starting...")
print("🔑 Tokens loaded?", all([BEARER_TOKEN, API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]))

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)

SOURCES = [
    "infoBMKG","infoBMKG1","Aceh","ModusAceh","acehworldtime","Dialeksis_news",
    "SerambiNews","tribunnews","acehtribun","acehinfo","AcehKoran","kumparan",
    "tempodotco","metro_tv","tvOneNews","detikcom","narasinewsroom","najwashihab",
    "narasitv","matanajwa","beritasatu","weathermonitors","volcaholic1",
    "BBCIndonesia","CNNIndonesia","CNN","trtworld","ALJazeera","AJEnglish","kompascom"
]

KEYWORDS = [
    "Aceh", "Banda Aceh", "Aceh Besar", "Pidie", "Lhokseumawe", "Sabang", "Bireuen",
    "Langsa", "Meulaboh", "Simeulue", "Gayo Lues", "Aceh Jaya", "Aceh Tamiang",
    "Aceh Singkil", "Aceh Barat", "Aceh Barat Daya", "Aceh Selatan", "Aceh Tenggara",
    "Aceh Timur", "Aceh Utara", "Aceh Tengah", "Bener Meriah"
]
KEYWORDS_LOWER = [kw.lower() for kw in KEYWORDS]

LAST_SEEN_FILE = "last_seen.json"
if os.path.exists(LAST_SEEN_FILE):
    with open(LAST_SEEN_FILE, "r") as f:
        last_seen = json.load(f)
else:
    last_seen = {}

def run_bot():
    total_posted = 0
    total_skipped = 0
    total_errors = 0
    per_source = {}

    for source in SOURCES:
        per_source[source] = {"posted": 0, "skipped": 0, "errors": 0}
        print(f"🔄 Checking @{source}")
        try:
            resp = client.get_users_tweets(id=source, max_results=5)
        except Exception as e:
            print(f"❌ Failed fetching @{source}: {e}")
            total_errors += 1
            per_source[source]["errors"] += 1
            continue

        tweets = getattr(resp, "data", None)
        if not tweets:
            print(f"⚠ No tweets for @{source}")
            continue

        for t in tweets:
            tid = str(t.id)
            if last_seen.get(source) == tid:
                total_skipped += 1
                per_source[source]["skipped"] += 1
                print(f"⏭ Skip old tweet {tid}")
                continue

            text = t.text or ""
            if not any(kw in text.lower() for kw in KEYWORDS_LOWER):
                total_skipped += 1
                per_source[source]["skipped"] += 1
                print(f"⏭ Skip (no keyword) {tid}")
                continue

            try:
                client.create_tweet(text=text)
                print(f"✅ Posted tweet {tid}")
                total_posted += 1
                per_source[source]["posted"] += 1
                last_seen[source] = tid
            except Exception as e:
                print(f"❌ Failed posting {tid}: {e}")
                total_errors += 1
                per_source[source]["errors"] += 1

    # Save last seen
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(last_seen, f, indent=2)

    # Build dashboard
    DASH_DIR = "gh-pages"
    os.makedirs(DASH_DIR, exist_ok=True)
    dash_file = os.path.join(DASH_DIR, "index.html")
    with open(dash_file, "w") as f:
        f.write(f"""
<!doctype html>
<html>
<head><meta charset="utf-8"><title>AcehNewsHub Status</title>
<meta http-equiv="refresh" content="600">
<style>body{{font-family:Arial;padding:20px;}} table{{border-collapse:collapse;width:100%;}} th,td{{border:1px solid #ccc;padding:8px;}}</style>
</head>
<body>
  <h1>AcehNewsHub Bot Status</h1>
  <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  <h2>Summary</h2>
  <ul>
    <li>Total posted: {total_posted}</li>
    <li>Total skipped: {total_skipped}</li>
    <li>Total errors: {total_errors}</li>
  </ul>
  <h2>Per‑source stats</h2>
  <table>
    <tr><th>Source</th><th>Posted</th><th>Skipped</th><th>Errors</th></tr>
""")
        for s, stats in per_source.items():
            f.write(f"<tr><td>{s}</td><td>{stats['posted']}</td><td>{stats['skipped']}</td><td>{stats['errors']}</td></tr>\n")
        f.write("""
  </table>
</body>
</html>
""")
    print(f"📊 Dashboard generated: {dash_file}")

    print("=== Run Summary ===")
    print("Posted:", total_posted, "Skipped:", total_skipped, "Errors:", total_errors)

if __name__ == "__main__":
    run_bot()