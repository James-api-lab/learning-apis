# scripts/seed.py
from datetime import datetime, timedelta
import random

from app import create_app
from app.db import db
from app.models import WeatherRecord

def seed_sample_rows():
    """Seed some predictable + some random data; idempotent if run multiple times."""
    # if there are already rows, do nothing
    if WeatherRecord.query.count() > 0:
        print("Seed: rows already present; skipping.")
        return

    cities = ["Seattle", "Austin", "Tokyo", "London", "Denver"]
    base = datetime.utcnow() - timedelta(days=7)

    rows = []
    for i in range(30):
        city = random.choice(cities)
        temp = round(random.uniform(5, 35), 1)
        humidity = round(random.uniform(25, 90), 1)
        rec = WeatherRecord(city=city, temp=temp, humidity=humidity)
        # optional: if your model allows custom created_at, set it here
        # rec.created_at = base + timedelta(hours=i*4)
        rows.append(rec)

    db.session.add_all(rows)
    db.session.commit()
    print(f"Seed: inserted {len(rows)} rows.")

def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_sample_rows()

if __name__ == "__main__":
    main()
