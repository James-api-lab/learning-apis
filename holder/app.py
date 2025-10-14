import os
import time
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
start_time = time.time()

# ----- Config -------------------------------------------------
class Config:
    VERSION = "0.1"
    DEBUG = True
    OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")


app.config.from_object(Config)  # <-- fixed
app.config.update(JSON_SORT_KEYS=False, APP_NAME="Week 4 Flask API")

# ----- Logging ------------------------------------------------
os.makedirs("logs", exist_ok=True)
log_handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_handler.setFormatter(formatter)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

@app.before_request
def log_request():
    app.logger.info(f"{request.method} {request.path}")

# Optional simple text access log
os.makedirs("data", exist_ok=True)
LOG_PATH = "data/access.log"

@app.after_request
def log_after(response):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {request.method} {request.path} {response.status_code}\n")
    return response

# ----- Routes -------------------------------------------------
@app.route("/")
def home():
    return jsonify(message="Week 4 Flask API is live")

@app.route("/health")
def health():
    uptime = round(time.time() - start_time, 2)
    return jsonify(status="ok", uptime=f"{uptime}s", version=app.config["VERSION"])

@app.route("/meta")
def meta():
    return jsonify(
        app=app.config["APP_NAME"],
        author="James",
        version=app.config["VERSION"],
        env=app.config.get("ENV", "production"),
        server_time=datetime.utcnow().isoformat() + "Z",
        has_weather_key=bool(app.config.get("OPENWEATHER_KEY")),
        docs=[
            {"path": url_for("home"), "desc": "home"},
            {"path": url_for("health"), "desc": "health"},
            {"path": url_for("meta"), "desc": "meta"},
        ]
    )

@app.route("/demo", methods=["GET", "POST"])
def demo():
    if request.method == "POST":
        return jsonify(status="received", method="POST")
    return jsonify(status="ready", method="GET")

@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Route not found", hint="Check your endpoint name"), 404

@app.route("/list")
def list_example():
    return jsonify(numbers=[1, 2, 3], message="Lists convert cleanly to JSON")

@app.route("/status")
def status_code():
    return jsonify(ok=True), 201  # custom status code

@app.route("/headers")
def headers():
    # caution: exposes headers; use only for learning
    return jsonify(dict(request.headers))

@app.errorhandler(500)
def server_error(e):
    app.logger.exception("Unhandled server error")
    return jsonify(error="Internal server error"), 500

# --- W4D2 DEMOS ------------------------------------------------------

# PATH PARAM: the resource identity
@app.route("/hello/<name>")
def hello_name(name):
    """Example of using a path parameter."""
    return jsonify(message=f"Hello, {name.capitalize()}!")

# PATH PARAM (with type conversion)
@app.route("/square/<int:n>")
def square_number(n):
    """Only matches if <n> is an integer."""
    return jsonify(number=n, squared=n * n)

# QUERY PARAMS: optional modifiers
@app.route("/add")
def add_numbers():
    """Adds ?a= and ?b= query parameters."""
    a_str = request.args.get("a")
    b_str = request.args.get("b")
    if a_str is None or b_str is None:
        return jsonify(error="Missing query params 'a' and/or 'b'"), 400
    try:
        a = float(a_str)
        b = float(b_str)
    except ValueError:
        return jsonify(error="Params must be numbers"), 400
    return jsonify(operation="add", a=a, b=b, result=a + b)

# POST BODY: JSON payload
@app.route("/echo", methods=["POST"])
def echo_json():
    """Echos back the JSON body you send."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Invalid or missing JSON body"), 400
    return jsonify(received=data, message="JSON echo complete")


# ----- Entry --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
