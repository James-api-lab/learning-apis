import requests

url = "https://postman-echo.com/post"
payload = {"student": "James", "lesson": "APIs POST"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print("Status:", response.status_code)
print("JSON:", response.json())
