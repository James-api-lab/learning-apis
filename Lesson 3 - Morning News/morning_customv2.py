# morning_custom.py
import os
import datetime
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv


# Absolute path to the .env in Lesson 3 folder
ENV_PATH = Path(r"C:\Users\James Gilmore\Desktop\Learning APIs\Lesson 3 - Morning News\.env")
load_dotenv(dotenv_path=ENV_PATH)

# =========================
# Config (tweak if you like)
# =========================
CITY = "Seattle"
SEATTLE_LIMIT = 5
WORLD_LIMIT = 3
SAVE_TO_DISK = False  # set True to also save a JSON snapshot
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"  # Set DEV_MODE=true in .env to cache
CACHE_MINUTES = 30  # How long to cache in dev mode

# =========================
# Helper Functions
# =========================
def safe_fetch(func, fallback, *args, **kwargs):
    """Wrapper to catch errors and return fallback data"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ Warning: {func.__name__} failed: {e}")
        return fallback

def cached_fetch(name, fetch_func, *args, **kwargs):
    """Cache API responses in dev mode to avoid rate limits"""
    if not DEV_MODE:
        return fetch_func(*args, **kwargs)
    
    cache_file = f".cache_{name}.json"
    
    # Check cache
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            if time.time() - cache['timestamp'] < CACHE_MINUTES * 60:
                print(f"📦 Using cached {name}")
                return cache['data']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    # Fetch fresh
    print(f"🔄 Fetching fresh {name}")
    data = fetch_func(*args, **kwargs)
    try:
        with open(cache_file, 'w') as f:
            json.dump({'timestamp': time.time(), 'data': data}, f)
    except Exception as e:
        print(f"Could not cache {name}: {e}")
    return data

# -----------------------
# Weather helpers (no key)
# -----------------------
def geocode_city(city: str):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=20,
    )
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        raise RuntimeError(f"City not found: {city}")
    top = results[0]
    return float(top["latitude"]), float(top["longitude"])

def fetch_today_high_low(city: str = CITY):
    lat, lon = geocode_city(city)
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()["daily"]
    tmax = d["temperature_2m_max"][0]
    tmin = d["temperature_2m_min"][0]
    return {"city": city, "high_c": tmax, "low_c": tmin}

def c_to_f(c):
    if isinstance(c, (int, float)):
        return c * 9 / 5 + 32
    return 0  # fallback for errors

# ------------------------
# News helpers (NewsAPI)
# ------------------------
BLOCKED_SOURCES = {
    "Yahoo Entertainment",
    "Slashdot.org",
    "ETFDailyNews.com",
    "ETFDailyNews",
    "Daily Mail",
}

SEA_DOMAINS = [
    "seattletimes.com",
    "king5.com",
    "kiro7.com",
    "komonews.com",
    "seattlepi.com",
    "geekwire.com",
    "crosscut.com",
    "q13fox.com",
    "mynorthwest.com",
    "seattlemet.com",
]

FINANCE_DOMAINS = [
    "reuters.com",
    "wsj.com",
    "ft.com",
    "bloomberg.com",
    "cnbc.com",
    "marketwatch.com",
    "americanbanker.com",
    "bankrate.com",
]

def newsapi_everything(
    query: str,
    limit: int,
    *,
    domains: list[str] | None = None,
    search_in: str = "title,description",
):
    key = os.getenv("NEWSAPI_API_KEY")
    if not key:
        raise RuntimeError("NEWSAPI_API_KEY not set in .env")

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(limit * 3, 50),  # fetch extra, filter locally
        "searchIn": search_in,
    }
    if domains:
        params["domains"] = ",".join(domains)

    r = requests.get(
        "https://newsapi.org/v2/everything",
        params=params,
        headers={"X-Api-Key": key},
        timeout=30,
    )
    if r.status_code == 401:
        raise RuntimeError(f"NewsAPI auth failed: {r.text[:200]}")
    r.raise_for_status()

    arts = r.json().get("articles") or []
    items, seen_titles = [], set()
    for a in arts:
        title = (a.get("title") or "").strip()
        source = (a.get("source") or {}).get("name") or ""
        if not title or title in seen_titles or source in BLOCKED_SOURCES:
            continue
        seen_titles.add(title)
        items.append(
            {
                "title": title,
                "source": source,
                "url": a.get("url"),
                "publishedAt": a.get("publishedAt"),
            }
        )
        if len(items) >= limit:
            break
    return items

def seattle_top(limit=SEATTLE_LIMIT):
    return newsapi_everything(
        query="Seattle", limit=limit, domains=SEA_DOMAINS, search_in="title,description"
    )

def newsapi_top_world(limit: int = WORLD_LIMIT):
    key = os.getenv("NEWSAPI_API_KEY")
    if not key:
        raise RuntimeError("NEWSAPI_API_KEY not set in .env")

    sources = "bbc-news,reuters,associated-press"
    r = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={"sources": sources, "pageSize": min(limit, 20)},
        headers={"X-Api-Key": key},
        timeout=30,
    )

    # If your plan can't use these sources, fallback
    if r.status_code in (401, 426):
        return newsapi_everything("world news OR global news", limit)

    r.raise_for_status()
    arts = r.json().get("articles") or []
    out = []
    for a in arts:
        title = (a.get("title") or "").strip()
        if not title:
            continue
        out.append(
            {
                "title": title,
                "source": (a.get("source") or {}).get("name"),
                "url": a.get("url"),
                "publishedAt": a.get("publishedAt"),
            }
        )
        if len(out) >= limit:
            break
    return out

# -------------------------
# Banking summary (optional OpenAI)
# -------------------------
def ai_summarize_banking():
    api_key = os.getenv("OPENAI_API_KEY")  # optional
    articles = newsapi_everything(
        query='(bank OR banking OR "interest rates" OR mortgage OR lender OR FDIC OR Basel OR regulation)',
        limit=6,
        domains=FINANCE_DOMAINS,
        search_in="title,description",
    )
    bullets = "\n".join([f"- {a['title']} ({a['source']})" for a in articles])

    if not api_key:
        return {"summary": f"(local) Banking headlines:\n{bullets}", "items": articles}

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a concise banking/markets analyst. Be factual and include the 'so what'.",
            },
            {
                "role": "user",
                "content": f"Summarize these banking headlines in 4–6 sentences, including risks and opportunities:\n{bullets}",
            },
        ],
        "max_tokens": 250,
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    return {"summary": text, "items": articles}

# -------------------------
# Email (SendGrid via HTTP)
# -------------------------
def send_email(subject: str, html_body: str):
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("EMAIL_USER")
    to_email = os.getenv("EMAIL_TO")
    if not all([api_key, from_email, to_email]):
        raise RuntimeError("SENDGRID_API_KEY, EMAIL_USER, EMAIL_TO must be set")

    payload = {
        "from": {"email": from_email, "name": "Morning Brief"},
        "personalizations": [{"to": [{"email": to_email}], "reply_to": {"email": from_email}}],
        "subject": subject,
        # send both plain text and html; no tracking; no sandbox
        "content": [
            {"type": "text/plain", "value": "Plain test body."},
            {"type": "text/html",  "value": html_body or "<p>hi</p>"},
        ],
        "tracking_settings": {
            "click_tracking": {"enable": False, "enable_text": False},
            "open_tracking": {"enable": False}
        },
        "mail_settings": {"sandbox_mode": {"enable": False}},
    }

    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    print("SendGrid status:", r.status_code, r.text[:200])
    if r.status_code >= 300:
        raise RuntimeError(f"SendGrid error {r.status_code}: {r.text[:200]}")

# -------------------------
# Parallel fetching
# -------------------------
def fetch_all_data_parallel():
    """Fetch all data in parallel - much faster!"""
    results = {}
    
    # Define all the tasks
    tasks = {
        "weather": lambda: cached_fetch("weather", fetch_today_high_low, CITY),
        "seattle": lambda: cached_fetch("seattle", seattle_top, SEATTLE_LIMIT),
        "world": lambda: cached_fetch("world", newsapi_top_world, WORLD_LIMIT),
        "banking": lambda: cached_fetch("banking", ai_summarize_banking)
    }
    
    # Run them in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {executor.submit(func): key for key, func in tasks.items()}
        
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
                print(f"✅ Completed: {key}")
            except Exception as e:
                print(f"❌ Failed {key}: {e}")
                # Provide fallbacks
                if key == "weather":
                    results[key] = {"city": CITY, "high_c": "?", "low_c": "?"}
                elif key in ["seattle", "world"]:
                    results[key] = []
                elif key == "banking":
                    results[key] = {"summary": "Banking news unavailable", "items": []}
    
    return results

# ---------------
# Main
# ---------------
if __name__ == "__main__":
    print("🚀 Starting Morning Brief Generator...")
    print(f"📍 City: {CITY}")
    print(f"🔧 Dev Mode: {'ON (using cache)' if DEV_MODE else 'OFF'}")
    print("-" * 50)
    
    # Fetch all data in parallel (much faster!)
    start_time = time.time()
    data = fetch_all_data_parallel()
    fetch_time = time.time() - start_time
    print(f"⏱️ All data fetched in {fetch_time:.1f} seconds")
    
    # Extract results
    wx = data.get("weather", {"city": CITY, "high_c": "?", "low_c": "?"})
    seattle_5 = data.get("seattle", [])
    world_3 = data.get("world", [])
    banking = data.get("banking", {"summary": "Banking news unavailable", "items": []})
    
    # Handle temperature conversion safely
    try:
        high_f = c_to_f(wx.get("high_c", 0))
        low_f = c_to_f(wx.get("low_c", 0))
    except:
        high_f, low_f = 0, 0

    # Console view
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"📰 MORNING BRIEF ({today})")
    print(f"{'='*50}")
    
    # Weather
    if wx.get("high_c") != "?":
        print(f"\n🌡️ {wx['city']} Weather Today:")
        print(f"   High: {high_f:.1f}°F ({wx['high_c']:.1f}°C)")
        print(f"   Low:  {low_f:.1f}°F ({wx['low_c']:.1f}°C)")
    else:
        print(f"\n⚠️ Weather data unavailable for {wx['city']}")

    # Seattle News
    print(f"\n📍 Top {len(seattle_5)} Seattle Stories:")
    if seattle_5:
        for i, a in enumerate(seattle_5, 1):
            print(f"{i}. {a['title']}")
            print(f"   📰 {a['source']}")
            print(f"   🔗 {a['url']}")
    else:
        print("   No Seattle news available")

    # World News
    print(f"\n🌍 Top {len(world_3)} World Stories:")
    if world_3:
        for i, a in enumerate(world_3, 1):
            print(f"{i}. {a['title']}")
            print(f"   📰 {a['source']}")
            print(f"   🔗 {a['url']}")
    else:
        print("   No world news available")

    # Banking
    print("\n🏦 Banking Summary:")
    print(f"   {banking['summary']}")

    # Email
    def list_items(items):
        if not items:
            return "<li><em>No articles available</em></li>"
        return "".join(
            f"<li><a href='{a['url']}'>{a['title']}</a> <em>({a['source']})</em></li>"
            for a in items
        )

    # Build email HTML
    weather_section = ""
    if wx.get("high_c") != "?":
        weather_section = f"""
        <h3>{wx['city']} Weather</h3>
        <p><strong>{wx['city']}:</strong> High {high_f:.1f}°F / Low {low_f:.1f}°F
        <br>(High {wx['high_c']:.1f}°C / Low {wx['low_c']:.1f}°C)</p>
        """
    else:
        weather_section = f"""
        <h3>{wx['city']} Weather</h3>
        <p><em>Weather data temporarily unavailable</em></p>
        """

    html = f"""
    <h2>Morning Brief — {today}</h2>

    {weather_section}

    <h3>Top Seattle Stories</h3>
    <ol>{list_items(seattle_5)}</ol>

    <h3>Top World Stories</h3>
    <ol>{list_items(world_3)}</ol>

    <h3>Banking Summary</h3>
    <p>{banking['summary'].replace(chr(10), '<br/>')}</p>
    
    <hr>
    <p style="color: #666; font-size: 0.9em;">
    Generated in {fetch_time:.1f} seconds • 
    {len(seattle_5) + len(world_3) + len(banking.get('items', []))} articles processed
    </p>
    """

    # Send email (with error handling)
    print(f"\n{'='*50}")
    try:
        send_email(
            subject=f"Morning Brief — {wx['city']} & World ({today})", 
            html_body=html
        )
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email failed: {e}")
        print("   (Check your SENDGRID_API_KEY, EMAIL_USER, and EMAIL_TO in .env)")

    # Optional: save a snapshot
    if SAVE_TO_DISK:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"morning_{stamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": stamp,
                    "fetch_time_seconds": fetch_time,
                    "weather": wx, 
                    "seattle": seattle_5, 
                    "world": world_3, 
                    "banking": banking
                },
                f,
                indent=2,
            )
        print(f"💾 Saved snapshot: {filename}")
    
    print(f"{'='*50}")
    print("✨ Morning Brief Complete!")