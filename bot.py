# bot.py
import os
import tweepy
import time
import json
import requests
from datetime import datetime, timedelta, timezone

# ==============================
# CONFIGURATION
# ==============================
GLOBAL_COOLDOWN = 3            # seconds between sources
RATE_LIMIT_SLEEP = 15 * 60     # per-source rate limit wait (15 minutes)
MEDIA_DOWNLOAD_RETRIES = 3
MEDIA_UPLOAD_RETRIES = 3
MEDIA_CHUNK_SIZE = 8192
MAX_RESULTS_PER_SOURCE = 10    # max tweets per API call
ONE_HOUR = timedelta(hours=1)

# ==============================
# API KEYS (from GitHub Secrets)
# ==============================
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

if not all([BEARER_TOKEN, API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    raise SystemExit("❌ Missing one or more X API environment variables")

# API v2 (read)
client_v2 = tweepy.Client(bearer_token=BEARER_TOKEN)

# API v1.1 (post)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api_v1 = tweepy.API(auth, wait_on_rate_limit=False)

# ==============================
# SOURCES TO MONITOR
# ==============================
sources = [
    "infoBMKG","infoBMKG1","Aceh","ModusAceh","acehworldtime","Dialeksis_news",
    "SerambiNews","tribunnews","acehtribun","acehinfo","AcehKoran","kumparan",
    "tempodotco","metro_tv","tvOneNews","detikcom","narasinewsroom","najwashihab",
    "narasitv","matanajwa","beritasatu","weathermonitors","volcaholic1",
    "BBCIndonesia","CNNIndonesia","CNN","trtworld","ALJazeera","AJEnglish","kompascom"
]

# ==============================
# KEYWORDS (kabupaten/kota Aceh)
# ==============================
keywords = [
    "Aceh", "Banda Aceh", "Berita", "Disaster",
    "Aceh Barat", "Aceh Barat Daya", "Aceh Besar", "Aceh Jaya",
    "Aceh Selatan", "Aceh Singkil", "Aceh Tamiang", "Aceh Tengah",
    "Aceh Tenggara", "Aceh Timur", "Aceh Utara", "Bener Meriah",
    "Bireuen", "Gayo Lues", "Nagan Raya", "Pidie", "Pidie Jaya",
    "Simeulue", "Subulussalam", "Langsa", "Lhokseumawe", "Meulaboh",
    "Sabang", "Takengon"
]
keywords_lower = [k.lower() for k in keywords]

# ==============================
# DUPLICATE FILTERING
# ==============================
posted_file = "posted_ids.txt"
if not os.path.exists(posted_file):
    open(posted_file, "w").close()

with open(posted_file, "r") as f:
    posted_ids = set(line.strip() for line in f.readlines())

def save_posted(tweet_id):
    tid = str(tweet_id)
    if tid not in posted_ids:
        posted_ids.add(tid)
        with open(posted_file, "a") as f:
            f.write(tid + "\n")

# ==============================
# LAST SEEN (PER-SOURCE CACHING)
# ==============================
LAST_SEEN_FILE = "last_seen.json"

if os.path.exists(LAST_SEEN_FILE):
    try:
        last_seen = json.load(open(LAST_SEEN_FILE, "r"))
    except json.JSONDecodeError:
        last_seen = {}
else:
    last_seen = {}

def save_last_seen():
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(last_seen, f, indent=2)

# ==============================
# STATUS DASHBOARD
# ==============================
STATUS_DIR = "status"
STATUS_JSON = os.path.join(STATUS_DIR, "status.json")
STATUS_HTML = os.path.join(STATUS_DIR, "index.html")
if not os.path.exists(STATUS_DIR):
    os.makedirs(STATUS_DIR, exist_ok=True)

# ==============================
# MEDIA DOWNLOAD & UPLOAD
# ==============================
def download_media(url, filename):
    for attempt in range(1, MEDIA_DOWNLOAD_RETRIES + 1):
        try:
            r = requests.get(url, stream=True, timeout=20)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(MEDIA_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            wait = 2 ** attempt
            print(f"⚠ Media download failed ({attempt}/{MEDIA_DOWNLOAD_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    print(f"❌ Failed to download media: {url}")
    return False


def upload_media(filename, chunked=False):
    for attempt in range(1, MEDIA_UPLOAD_RETRIES + 1):
        try:
            media = api_v1.media_upload(filename, chunked=chunked)
            return media.media_id
        except Exception as e:
            wait = 2 ** attempt
            print(f"⚠ Media upload failed ({attempt}/{MEDIA_UPLOAD_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    print(f"❌ Failed to upload media: {filename}")
    return None

# ==============================
# DASHBOARD WRITE
# ==============================
def write_status_dashboard(summary):
    # summary is a dict with run details
    # Write JSON
    with open(STATUS_JSON, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Write a simple HTML file
    html = f"""
    <!doctype html>
    <html lang=\"en\">
    <head>
      <meta charset=\"utf-8\">
      <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
      <title>AcehNewsHub — Run Status</title>
      <style>
        body{font-family:system-ui,Arial;margin:24px;color:#111}
        .card{border-radius:12px;padding:16px;background:#f8f9fb;box-shadow:0 6px 18px rgba(10,10,10,0.06);max-width:900px}
        h1{margin-top:0}
        pre{background:#fff;padding:12px;border-radius:8px;overflow:auto}
      </style>
    </head>
    <body>
      <div class=\"card\">
        <h1>AcehNewsHub — Latest Run</h1>
        <p><strong>Run time:</strong> {summary.get('run_time')}</p>
        <p><strong>Posted:</strong> {summary.get('posted')}</p>
        <p><strong>Skipped:</strong> {summary.get('skipped')}</p>
        <p><strong>Errors:</strong> {summary.get('errors')}</p>
        <h2>Per-source detail</h2>
        <pre>{json.dumps(summary.get('per_source', {}), indent=2)}</pre>
      </div>
    </body>
    </html>
    """
    with open(STATUS_HTML, "w") as f:
        f.write(html)

# ==============================
# MAIN BOT LOGIC
# ==============================
def run_bot():
    now = datetime.now(timezone.utc)
    cutoff = now - ONE_HOUR

    total_posted = 0
    total_skipped = 0
    total_errors = 0
    per_source = {}

    for username in sources:
        print(f"\n===== Checking @{username} =====")
        per_source.setdefault(username, {"posted":0,"skipped":0,"errors":0})

        # Load last seen
        since_id = last_seen.get(username)

        # Fetch user
        try:
            user = client_v2.get_user(username=username)
        except tweepy.TooManyRequests:
            print(f"⏳ Rate limit on user lookup @{username}. Sleeping {RATE_LIMIT_SLEEP//60}m.")
            time.sleep(RATE_LIMIT_SLEEP)
            total_errors += 1
            per_source[username]["errors"] += 1
            continue
        except Exception as e:
            print(f"❌ Cannot fetch user @{username}: {e}")
            total_errors += 1
            per_source[username]["errors"] += 1
            continue

        if not user or not user.data:
            print(f"⚠ User @{username} not found.")
            total_errors += 1
            per_source[username]["errors"] += 1
            continue

        user_id = user.data.id

        # Fetch tweets with since_id caching
        try:
            tweets = client_v2.get_users_tweets(
                id=user_id,
                max_results=MAX_RESULTS_PER_SOURCE,
                since_id=since_id,
                tweet_fields=["created_at", "text", "attachments"],
                expansions=["attachments.media_keys"],
                media_fields=["url", "type"]
            )
        except tweepy.TooManyRequests:
            print(f"⏳ Rate limit while fetching @{username}. Sleeping {RATE_LIMIT_SLEEP//60}m.")
            time.sleep(RATE_LIMIT_SLEEP)
            total_errors += 1
            per_source[username]["errors"] += 1
            continue
        except Exception as e:
            print(f"❌ Error fetching tweets for @{username}: {e}")
            total_errors += 1
            per_source[username]["errors"] += 1
            continue

        if not tweets or not tweets.data:
            print(f"No new tweets for @{username} since last_seen.")
            time.sleep(GLOBAL_COOLDOWN)
            continue

        # Build media map
        media_dict = {}
        if tweets.includes and "media" in tweets.includes:
            for m in tweets.includes["media"]:
                media_dict[m.media_key] = m

        # Process tweets newest-first
        for t in sorted(tweets.data, key=lambda x: x.id):
            tid = str(t.id)

            # duplicate
            if tid in posted_ids:
                total_skipped += 1
                per_source[username]["skipped"] += 1
                continue

            # last hour filter
            created = t.created_at
            if created < cutoff:
                print(f"Skipping old tweet: {tid}")
                total_skipped += 1
                per_source[username]["skipped"] += 1
                continue

            # keyword match
            text = t.text or ""
            if not any(k in text.lower() for k in keywords_lower):
                print(f"Skipping non-Aceh tweet {tid}")
                total_skipped += 1
                per_source[username]["skipped"] += 1
                continue

            # prepare tweet text
            tweet_text = " ".join(text.split())
            source_tag = f"\n\nSource: @{username}"
            if len(tweet_text) + len(source_tag) > 280:
                tweet_text = tweet_text[: 280 - len(source_tag) - 3] + "..."
            tweet_text += source_tag

            # handle media
            media_ids = []
            if t.attachments and "media_keys" in t.attachments:
                for mk in t.attachments["media_keys"]:
                    m = media_dict.get(mk)
                    if not m or not getattr(m, 'url', None):
                        continue

                    ext = ".jpg" if m.type == "photo" else ".mp4"
                    filename = f"/tmp/{mk}{ext}"

                    if not download_media(m.url, filename):
                        continue

                    chunked = m.type in ("video", "animated_gif")
                    mid = upload_med