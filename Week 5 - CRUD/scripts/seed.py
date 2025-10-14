from app import create_app
from app.db import db
from app.models import WeatherRecord

def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        if not WeatherRecord.query.first():
            db.session.add_all([
                WeatherRecord(city="Seattle", temp=18, humidity=70),
                WeatherRecord(city="Tokyo",   temp=24, humidity=65),
                WeatherRecord(city="Austin",  temp=31, humidity=50),
            ])
            db.session.commit()
            print("Seeded 3 records.")
        else:
            print("Database already has data; skipping seed.")

if __name__ == "__main__":
    main()
