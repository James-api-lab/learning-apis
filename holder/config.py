import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    VERSION = "0.1"
    DEBUG = True
    OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
