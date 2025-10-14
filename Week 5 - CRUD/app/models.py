from .db import db
from datetime import datetime

class WeatherRecord(db.Model):
    __tablename__ = "weather_record"
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), nullable=False, index=True)
    temp = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "temp": self.temp,
            "humidity": self.humidity,
            "created_at": self.created_at.isoformat(),
        }
