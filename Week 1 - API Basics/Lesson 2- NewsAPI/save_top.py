# save_top.py
import requests, json, datetime

BASE = "http://127.0.0.1:8001"
r = requests.get(f"{BASE}/news/top", params={"country":"us","limit":5}, timeout=30)
r.raise_for_status()
data = r.json()

stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
with open(f"top_{stamp}.json","w",encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("Saved:", f.name)
