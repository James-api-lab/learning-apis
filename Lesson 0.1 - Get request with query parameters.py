import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 47.61,     # Seattle
    "longitude": -122.33,
    "current_weather": True
}

response = requests.get(url, params=params)
print("Status:", response.status_code)
print("JSON:", response.json())
