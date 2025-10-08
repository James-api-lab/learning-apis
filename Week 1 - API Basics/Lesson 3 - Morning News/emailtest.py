import os, requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

api_key = os.getenv("SENDGRID_API_KEY")
from_email = os.getenv("EMAIL_USER")
to_email = os.getenv("EMAIL_TO")

resp = requests.post(
    "https://api.sendgrid.com/v3/mail/send",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": "SMTP test (SendGrid)",
        "content": [{"type": "text/html", "value": "<p>Hello from Morning Brief</p>"}],
    },
    timeout=30
)
if resp.status_code >= 300:
    raise SystemExit(f"SendGrid error {resp.status_code}: {resp.text[:200]}")
print("OK via SendGrid")
