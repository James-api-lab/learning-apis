# news_app.py
import os
import requests
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv

# Load .env sitting in this folder
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

app = FastAPI(title="Local News API")


def fetch_headlines(topic: str, limit: int = 5):
    """
    Fetch recent headlines for a topic using NewsAPI /v2/everything.
    Returns a list of dicts with title, source, url, publishedAt, description.
    """
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NEWSAPI_API_KEY not set (put it in .env)")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "sortBy": "publishedAt",
        "pageSize": max(1, min(limit, 20)),
        "language": "en",
    }
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, params=params, headers=headers, timeout=30)

    if r.status_code == 401:
        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        raise HTTPException(status_code=401, detail=f"NewsAPI auth failed: {msg}. Check NEWSAPI_API_KEY in .env")

    r.raise_for_status()
    data = r.json()

    articles = data.get("articles") or []
    results, seen = [], set()
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        results.append({
            "title": title,
            "source": (a.get("source") or {}).get("name"),
            "url": a.get("url"),
            "publishedAt": a.get("publishedAt"),
            "description": a.get("description"),
        })
        if len(results) >= limit:
            break
    return results


@app.get("/")
def home():
    return {
        "message": "Hi! Try /news, /news/summary, or /news/top",
        "examples": [
            "/news?topic=ai&limit=5",
            "/news/summary?topic=fintech&limit=5&style=neutral",
            "/news/top?country=us",
            "/docs",
        ],
    }


@app.get("/news")
def get_news(topic: str = Query("AI"), limit: int = Query(5, ge=1, le=20)):
    items = fetch_headlines(topic, limit)
    return {"ok": True, "topic": topic, "count": len(items), "items": items}


@app.get("/news/summary")
def get_news_summary(
    topic: str = Query("AI"),
    limit: int = Query(5, ge=1, le=20),
    style: str = Query("neutral"),  # neutral|optimistic|skeptical
):
    items = fetch_headlines(topic, limit)
    bullets = "\n".join([f"- {it['title']} ({it['source']})" for it in items])

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "ok": True,
            "topic": topic,
            "count": len(items),
            "items": items,
            "summary": f"(local) Top {len(items)} {topic} headlines:\n{bullets}",
            "style": style,
        }

    tone = {
        "neutral": "Write a neutral 3–4 sentence brief.",
        "optimistic": "Write an upbeat, opportunity-focused 3–4 sentence brief.",
        "skeptical": "Write a cautious, risk-aware 3–4 sentence brief.",
    }.get(style, "Write a neutral 3–4 sentence brief.")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a concise analyst for daily briefs."},
            {"role": "user", "content": f"{tone}\nSummarize these headlines about {topic}:\n{bullets}"},
        ],
        "max_tokens": 220,
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60
    )
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {r.text[:200]}")
    text = r.json()["choices"][0]["message"]["content"].strip()

    return {"ok": True, "topic": topic, "count": len(items), "items": items, "summary": text, "style": style}


@app.get("/news/top")
def get_top_headlines(
    country: str = Query("us"),
    limit: int = Query(5, ge=1, le=20),
):
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NEWSAPI_API_KEY not set")

    url = "https://newsapi.org/v2/top-headlines"
    params = {"country": country, "pageSize": limit}
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, params=params, headers=headers, timeout=30)

    if r.status_code == 401:
        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        raise HTTPException(status_code=401, detail=f"NewsAPI auth failed: {msg}")

    r.raise_for_status()
    data = r.json()
    items = [
        {
            "title": (a.get("title") or "").strip(),
            "source": (a.get("source") or {}).get("name"),
            "url": a.get("url"),
        }
        for a in (data.get("articles") or [])
        if (a.get("title") or "").strip()
    ][:limit]

    return {"ok": True, "count": len(items), "items": items}
