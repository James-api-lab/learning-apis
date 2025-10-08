import os, pathlib
from dotenv import load_dotenv
load_dotenv(dotenv_path=pathlib.Path(".env"))
print("FROM:", os.getenv("EMAIL_USER"))
print("TO  :", os.getenv("EMAIL_TO"))
print("SG? ", bool(os.getenv("SENDGRID_API_KEY")))
