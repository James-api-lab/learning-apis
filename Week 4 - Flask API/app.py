# app.py
# Week 4 – Flask API (Day 1–3)
# - JSON-first responses with clean 400/404/500 handlers
# - Path params (/hello/<name>, /square/<int:n>)
# - Query params (/add?a=..&b=..)
# - POST JSON body (/echo)
# - OpenWeather integration:
#     * /weather/<city>?units=metric|imperial|standard
#     * /weather?cities=Seattle,Tokyo,Paris&units=...
#   with caching + CSV logging
# - Request logging (rotating file + simple access log)

from __future__ import annotations
import csv
import os
import time
import logging
import requests
import json, urllib.parse

from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


from flask import Flask, request, jsonify, url_for, redirect
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
# app.py (top-level after app = Flask(...))

from flask import render_template



# ---------------------------------------------------------------------
# Environment & Config
# ---------------------------------------------------------------------

# Load .env that sits NEXT TO this file (works no matter where you run python)
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# External config.py must define class Config with:
#   VERSION, DEBUG, APP_NAME, JSON_SORT_KEYS, OPENWEATHER_KEY
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
from flask_cors import CORS
CORS(app)
start_time = time.time()

# ---------------------------------------------------------------------
# Logging (rotating file + simple access log)
# ---------------------------------------------------------------------

os.makedirs("logs", exist_ok=True)
log_handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

os.makedirs("data", exist_ok=True)
ACCESS_LOG_PATH = "data/access.log"


@app.before_request
def _log_request() -> None:
    app.logger.info(f"{request.method} {request.path}")


@app.after_request
def _log_after(response):
    ts = datetime.now(timezone.utc).isoformat()
    with open(ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {request.method} {request.path} {response.status_code}\n")
    return response


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def make_chart(data, city, units="metric"):
    """Build a QuickChart URL to visualize temperature trends."""
    temps = [r["temp"] for r in data if r["temp"] is not None]
    labels = [r["ts"].split("T")[0] if r.get("ts") else "" for r in data]

    chart_cfg = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": f"{city} temperature ({units})",
                "data": temps,
                "fill": False
            }]
        },
        "options": {
            "plugins": {"title": {"display": True, "text": f"Weather History for {city}"}},
            "scales": {"y": {"beginAtZero": False}}
        }
    }
    cfg_json = json.dumps(chart_cfg, separators=(",", ":"))
    return "https://quickchart.io/chart?c=" + urllib.parse.quote_plus(cfg_json)

def read_weather_log(path: str = "data/weather_log.csv", city: str | None = None, limit: int | None = None):
    """
    Read weather_log.csv and return a list of dicts.
    - city: optional filter (case-insensitive)
    - limit: if provided, return only the most recent N rows
    """
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if city and row.get("city", "").lower() != city.lower():
                continue
            rows.append({
                "ts": row.get("ts"),
                "city": row.get("city"),
                "units": row.get("units"),
                "temp": float(row["temp"]) if row.get("temp") not in (None, "", "None") else None,
                "humidity": float(row["humidity"]) if row.get("humidity") not in (None, "", "None") else None,
                "description": row.get("description"),
            })
    # keep chronological order; DictReader preserves file order (oldest→newest)
    if limit:
        rows = rows[-int(limit):]
    return rows

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_float(name: str) -> float:
    """Get a required numeric query param or raise 400."""
    val = request.args.get(name)
    if val is None:
        raise BadRequest(f"Missing query param '{name}'")
    try:
        return float(val)
    except ValueError:
        raise BadRequest(f"Query param '{name}' must be a number")


# --- Tiny in-memory cache for weather (5 min TTL) ---
CACHE_TTL = 300  # seconds
# key: (city_lower, units) -> (expiry_ts, data_dict)
_weather_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}


def cache_get(city: str, units: str) -> Optional[Dict[str, Any]]:
    key = (city.lower(), units)
    entry = _weather_cache.get(key)
    if not entry:
        return None
    expiry, data = entry
    if time.time() > expiry:
        _weather_cache.pop(key, None)
        return None
    return data


def cache_set(city: str, units: str, data: Dict[str, Any]) -> None:
    key = (city.lower(), units)
    _weather_cache[key] = (time.time() + CACHE_TTL, data)


# ---------------------------------------------------------------------
# Error handlers (JSON everywhere)
# ---------------------------------------------------------------------

@app.errorhandler(BadRequest)
@app.errorhandler(400)
def _bad_request(e):
    # e.description will include our message from require_float etc.
    return jsonify(error="Bad request", detail=str(e)), 400


@app.errorhandler(404)
def _not_found(e):
    return jsonify(error="Route not found", hint="Check your endpoint name"), 404


@app.errorhandler(500)
def _server_error(e):
    app.logger.exception("Unhandled server error")
    return jsonify(error="Internal server error"), 500


# ---------------------------------------------------------------------
# Basic routes (Day 1–2)
# ---------------------------------------------------------------------
@app.route("/ui")
def ui():
    return render_template("ui.html")

@app.route("/")
def home():
    return jsonify(message="Week 4 Flask API is live")


@app.route("/health")
def health():
    uptime = round(time.time() - start_time, 2)
    return jsonify(status="ok", uptime=f"{uptime}s", version=app.config["VERSION"])


@app.route("/meta")
def meta():
    return jsonify(
        app=app.config["APP_NAME"],
        author="James",
        version=app.config["VERSION"],
        env=app.config.get("ENV", "production"),
        server_time=utc_now_iso(),
        has_weather_key=bool(app.config.get("OPENWEATHER_KEY")),
        cache_entries=len(_weather_cache),
        docs=[
            {"path": url_for("home"), "desc": "home"},
            {"path": url_for("health"), "desc": "health"},
            {"path": url_for("meta"), "desc": "meta"},
        ],
    )


@app.route("/demo", methods=["GET", "POST"])
def demo():
    if request.method == "POST":
        return jsonify(status="received", method="POST")
    return jsonify(status="ready", method="GET")


@app.route("/list")
def list_example():
    return jsonify(numbers=[1, 2, 3], message="Lists convert cleanly to JSON")


@app.route("/status")
def status_code():
    return jsonify(ok=True), 201  # example of a custom status code


@app.route("/headers")
def headers():
    # keep this debug-only
    if not app.debug:
        return jsonify(error="Not available in production"), 403
    return jsonify(dict(request.headers))


# Day 2 – params
@app.route("/hello/<name>")
def hello_name(name: str):
    return jsonify(message=f"Hello, {name.capitalize()}!")


@app.route("/square/<int:n>")
def square_number(n: int):
    return jsonify(number=n, squared=n * n)


@app.route("/add")
def add_numbers():
    a = require_float("a")
    b = require_float("b")
    return jsonify(operation="add", a=a, b=b, result=a + b)


@app.route("/echo", methods=["POST"])
def echo_json():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Invalid or missing JSON body"), 400
    return jsonify(received=data, message="JSON echo complete")

@app.route("/chart")
def chart():
    city = request.args.get("city")
    limit = int(request.args.get("limit", 7))
    if not city:
        return jsonify(error="Missing ?city="), 400

    from csv import DictReader
    path = "data/weather_log.csv"
    if not os.path.exists(path):
        return jsonify(error="No data logged yet"), 404

    records = []
    with open(path, encoding="utf-8") as f:
        reader = DictReader(f)
        for row in reader:
            if row["city"].lower() == city.lower():
                records.append(row)
    if not records:
        return jsonify(error=f"No records found for {city}"), 404

    # sort chronologically
    records = sorted(records, key=lambda r: r["ts"])[-limit:]
    url = make_chart(records, city)
    return jsonify(chart_url=url, count=len(records))

@app.route("/chart/view")
def chart_view():
    city = request.args.get("city")
    limit = int(request.args.get("limit", 7))
    if not city:
        return jsonify(error="Missing ?city="), 400

    records = read_weather_log(city=city, limit=limit)
    if not records:
        return jsonify(error=f"No records found for {city}"), 404

    url = make_chart(records, city)
    return redirect(url, code=302)

@app.route("/chart/html")
def chart_html():
    city = request.args.get("city")
    limit = int(request.args.get("limit", 7))
    if not city:
        return "<p>Missing ?city=</p>", 400

    records = read_weather_log(city=city, limit=limit)
    if not records:
        return f"<p>No records for {city}</p>", 404

    url = make_chart(records, city)
    return f"""<!doctype html>
<meta charset="utf-8">
<title>{city} Weather Chart</title>
<h1>{city} Weather (last {limit})</h1>
<img src="{url}" alt="Chart for {city}" />
<p><a href="{url}" target="_blank">Open image</a></p>"""


@app.route("/summary")
def summary():
    city = request.args.get("city")
    if not city:
        return jsonify(error="Missing ?city="), 400

    records = read_weather_log(city=city)
    if not records:
        return jsonify(error=f"No records for {city}"), 404

    temps = [r["temp"] for r in records if r["temp"] is not None]
    avg = round(sum(temps) / len(temps), 1)
    latest = records[-1]["temp"]
    trend = "up" if latest > avg else "down"

    summary_text = f"{city} avg {avg}°C — latest {latest}°C ({trend})"
    return jsonify(summary=summary_text)

@app.route("/history")
def history():
    city = request.args.get("city")
    limit = request.args.get("limit", 10)
    try:
        limit = int(limit)
    except ValueError:
        return jsonify(error="limit must be an integer"), 400

    records = read_weather_log(city=city, limit=limit)
    if not records:
        return jsonify(message="No records found", city=city), 404

    temps = [r["temp"] for r in records if r["temp"] is not None]
    hums  = [r["humidity"] for r in records if r["humidity"] is not None]

    summary = {
        "city": city or "All",
        "count": len(records),
        "avg_temp": round(sum(temps) / len(temps), 2) if temps else None,
        "min_temp": min(temps) if temps else None,
        "max_temp": max(temps) if temps else None,
        "avg_humidity": round(sum(hums) / len(hums), 2) if hums else None,
        "records": records,  # last N, chronological
    }
    return jsonify(summary)

@app.route("/history/stats")
def history_stats():
    city = request.args.get("city")
    records = read_weather_log(city=city)  # all rows for city, no limit
    if not records:
        return jsonify(message="No records found", city=city), 404

    temps = [r["temp"] for r in records if r["temp"] is not None]
    hums  = [r["humidity"] for r in records if r["humidity"] is not None]
    out = {
        "city": city or "All",
        "samples": len(records),
        "avg_temp": round(sum(temps) / len(temps), 2) if temps else None,
        "min_temp": min(temps) if temps else None,
        "max_temp": max(temps) if temps else None,
        "avg_humidity": round(sum(hums) / len(hums), 2) if hums else None,
    }
    return jsonify(out)

from collections import defaultdict

def group_daily(records):
    buckets = defaultdict(list)
    for r in records:
        day = (r["ts"] or "").split("T")[0]
        if day:
            buckets[day].append(r)
    daily = []
    for day, rows in sorted(buckets.items()):
        temps = [x["temp"] for x in rows if x["temp"] is not None]
        hums  = [x["humidity"] for x in rows if x["humidity"] is not None]
        daily.append({
            "date": day,
            "count": len(rows),
            "avg_temp": round(sum(temps)/len(temps), 2) if temps else None,
            "min_temp": min(temps) if temps else None,
            "max_temp": max(temps) if temps else None,
            "avg_humidity": round(sum(hums)/len(hums), 2) if hums else None,
        })
    return daily

@app.route("/history/daily")
def history_daily():
    city = request.args.get("city")
    limit_days = int(request.args.get("limit", 7))  # last N days
    records = read_weather_log(city=city)  # all rows for city
    if not records:
        return jsonify(message="No records found", city=city), 404
    daily = group_daily(records)
    return jsonify({
        "city": city or "All",
        "days": daily[-limit_days:]  # last N days
    })

# ---------------------------------------------------------------------
# Day 3 – OpenWeather integration
# ---------------------------------------------------------------------

def ow_get_weather(city: str, units: str, api_key: str) -> Tuple[Optional[Dict[str, Any]], int, Optional[Dict[str, Any]]]:
    """Call OpenWeather and normalize the payload we return."""
    base = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": units}
    try:
        r = requests.get(base, params=params, timeout=10)
    except requests.exceptions.RequestException as ex:
        # Prefer a clear 502 for upstream/network issues
        return None, 502, {"message": "Upstream request failed", "detail": str(ex)}

    if r.status_code != 200:
        try:
            payload = r.json()
        except Exception:
            payload = {"message": r.text}
        return None, r.status_code, payload

    data = r.json()
    result = {
        "city": data.get("name", city),
        "units": units,
        "temp": data.get("main", {}).get("temp"),
        "humidity": data.get("main", {}).get("humidity"),
        "description": (data.get("weather") or [{}])[0].get("description"),
        "wind_speed": data.get("wind", {}).get("speed"),
        "ts": utc_now_iso(),
    }
    return result, 200, None


def append_weather_log(row: Dict[str, Any], path: str = "data/weather_log.csv") -> None:
    """Append a single-row CSV line (created on first write)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if is_new:
            f.write("ts,city,units,temp,humidity,description,wind_speed\n")
        # simple CSV (avoid commas in description)
        f.write(",".join([
            str(row.get("ts", "")),
            str(row.get("city", "")),
            str(row.get("units", "")),
            str(row.get("temp", "")),
            str(row.get("humidity", "")),
            str(row.get("description", "")).replace(",", " "),
            str(row.get("wind_speed", "")),
        ]) + "\n")


@app.route("/weather/<city>")
def weather_single(city: str):
    # nudge to bulk if commas are used in path
    if "," in city:
        return jsonify(
            error="Use bulk endpoint for multiple cities",
            example="/weather?cities=Seattle,New%20York,Paris"
        ), 400

    api_key = app.config.get("OPENWEATHER_KEY")
    if not api_key:
        return jsonify(error="Server missing OPENWEATHER_API_KEY"), 500

    units = request.args.get("units", "imperial")
    if units not in {"metric", "imperial", "standard"}:
        return jsonify(error="Invalid units. Use metric, imperial, or standard"), 400

    city = city.strip()

    # cache-first
    cached = cache_get(city, units)
    if cached:
        return jsonify({**cached, "cache": True})

    data, code, err = ow_get_weather(city, units, api_key)
    if code != 200:
        return jsonify(source="openweather", error=err), code

    # log & cache successful responses
    try:
        append_weather_log(data)
    except Exception:
        app.logger.exception("Failed to append weather log")

    cache_set(city, units, data)
    return jsonify({**data, "cache": False})


@app.route("/weather")
def weather_bulk():
    """
    GET /weather?cities=Seattle,Tokyo,Paris&units=metric
    Returns: { units, count, results: [ ... ], errors: [ ... ] }
    """
    api_key = app.config.get("OPENWEATHER_KEY")
    if not api_key:
        return jsonify(error="Server missing OPENWEATHER_API_KEY"), 500

    units = request.args.get("units", "imperial")
    if units not in {"metric", "imperial", "standard"}:
        return jsonify(error="Invalid units. Use metric, imperial, or standard"), 400

    raw = request.args.get("cities", "")
    cities: List[str] = [c.strip() for c in raw.split(",") if c.strip()]
    if not cities:
        return jsonify(error="Missing 'cities' query param (comma-separated)"), 400

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    def fetch_one(city_name: str) -> Dict[str, Any]:
        # cache-first
        cached = cache_get(city_name, units)
        if cached:
            return {"data": {**cached, "cache": True}, "city": city_name, "code": 200, "err": None}

        data, code, err = ow_get_weather(city_name, units, api_key)
        if code == 200:
            try:
                append_weather_log(data)
            except Exception:
                app.logger.exception("Failed to append weather log (bulk)")
            cache_set(city_name, units, data)
            return {"data": {**data, "cache": False}, "city": city_name, "code": code, "err": None}

        return {"data": None, "city": city_name, "code": code, "err": err}

    # modest concurrency to respect upstream rate limits
    with ThreadPoolExecutor(max_workers=min(6, len(cities))) as ex:
        futures = [ex.submit(fetch_one, c) for c in cities]
        for fut in as_completed(futures):
            res = fut.result()
            if res["code"] == 200:
                results.append(res["data"])
            else:
                errors.append({"city": res["city"], "code": res["code"], "error": res["err"]})

    return jsonify({"units": units, "count": len(results), "results": results, "errors": errors})


# ---------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Respect DEBUG from Config; ensures /headers lock in "prod"
    app.run(debug=app.config["DEBUG"])
