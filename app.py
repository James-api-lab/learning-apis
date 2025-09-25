import os
import requests
from fastapi import FastAPI, Query
from pathlib import Path
from dotenv import load_dotenv

# load the .env sitting next to this file
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

app = FastAPI(title="Local Weather API")


WMO_CODE_TEXT = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def code_to_text(code: int) -> str:
    return WMO_CODE_TEXT.get(int(code), f"Unknown code {code}")

def fetch_weather(lat: float, lon: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current_weather": True}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["current_weather"]

def summarize_weather(wx: dict, *, imperial: bool = False) -> str:
    desc = code_to_text(wx["weathercode"])
    if imperial:
        temp_f = wx["temperature"] * 9/5 + 32
        wind_mph = wx["windspeed"] * 0.621371
        return f"{desc}. Temp {temp_f:.1f}°F, wind {wind_mph:.1f} mph."
    return f"{desc}. Temp {wx['temperature']}°C, wind {wx['windspeed']} km/h."

@app.get("/weather")
def get_weather(
    lat: float = Query(47.61, description="Latitude"),
    lon: float = Query(-122.33, description="Longitude"),
    units: str = Query("metric", description="'metric' or 'imperial'")
):
    wx = fetch_weather(lat, lon)
    summary = summarize_weather(wx, imperial=(units == "imperial"))
    return {"ok": True, "location": {"lat": lat, "lon": lon}, "current": wx, "summary": summary, "units": units}

@app.get("/")
def home():
    return {
        "message": "Hi! Try /weather or /docs",
        "examples": [
            "/weather",
            "/weather?units=imperial",
            "/docs"
        ]
    }


from fastapi import HTTPException

@app.get("/weather/summary")
def ai_summary(
    lat: float = Query(47.61),
    lon: float = Query(-122.33),
    units: str = Query("metric")
):
    wx = fetch_weather(lat, lon)
    summary = summarize_weather(wx, imperial=(units == "imperial"))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": True, "summary": f"(local) {summary}"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Be concise and friendly."},
            {"role": "user", "content": f"Rewrite this: {summary}"}
        ],
        "max_tokens": 50,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {r.text[:200]}")
    text = r.json()["choices"][0]["message"]["content"].strip()
    return {"ok": True, "summary": text}


from fastapi import HTTPException

def geocode_city(city: str):
    # Open-Meteo’s free geocoder (no key)
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 1}, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail=f"City not found: {city}")
    top = results[0]
    return float(top["latitude"]), float(top["longitude"])

@app.get("/weather/by-city")
def weather_by_city(city: str, units: str = Query("metric")):
    lat, lon = geocode_city(city)
    wx = fetch_weather(lat, lon)
    summary = summarize_weather(wx, imperial=(units == "imperial"))
    return {
        "ok": True,
        "city": city,
        "location": {"lat": lat, "lon": lon},
        "summary": summary,
        "units": units
    }

@app.get("/weather/summary/by-city")
def ai_summary_by_city(city: str, units: str = Query("metric")):
    lat, lon = geocode_city(city)
    wx = fetch_weather(lat, lon)
    summary = summarize_weather(wx, imperial=(units == "imperial"))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": True, "summary": f"(local) {summary}", "city": city}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Be concise and friendly."},
            {"role": "user", "content": f"Rewrite this: {summary}"}
        ],
        "max_tokens": 50,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {r.text[:200]}")
    text = r.json()["choices"][0]["message"]["content"].strip()
    return {"ok": True, "city": city, "summary": text, "units": units}
