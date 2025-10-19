import pytest
from app import create_app
from app.db import db
from app.models import WeatherRecord

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app.test_client()

def test_stats_empty(client):
    rv = client.get("/records/stats")
    assert rv.status_code == 200
    assert rv.get_json() == []

def test_stats_with_data(client):
    app = client.application
    with app.app_context():
        db.session.add_all([
            WeatherRecord(city="Seattle", temp=20, humidity=50),
            WeatherRecord(city="Seattle", temp=22, humidity=55),
            WeatherRecord(city="Austin",  temp=30, humidity=40),
        ])
        db.session.commit()

    rv = client.get("/records/stats")
    assert rv.status_code == 200
    data = rv.get_json()
    by_city = {row["city"]: row for row in data}
    assert by_city["Seattle"]["count"] == 2
    assert round(by_city["Seattle"]["avg_temp"], 2) == 21.0
    assert by_city["Austin"]["count"] == 1
    assert by_city["Austin"]["avg_temp"] == 30.0
