import os
class Config:
    VERSION = "0.1"
    DEBUG = True
    APP_NAME = "Week 4 Flask API"
    JSON_SORT_KEYS = False
    OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
