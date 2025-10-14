from pathlib import Path
from dotenv import load_dotenv
import os

def configure_app(app):
    load_dotenv()
    BASE = Path(__file__).resolve().parent.parent  # project root
    DATA = BASE / "data"
    LOGS = BASE / "logs"
    DATA.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATA / 'weather.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
