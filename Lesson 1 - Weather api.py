import requests
import os
from fastapi import FastAPI, Query

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
