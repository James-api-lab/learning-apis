# app/__init__.py (top of file)
import logging, os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import time

from flask import Flask, jsonify, request  # <-- ensure Flask is imported
from .config import configure_app          # <-- ensure this is imported
from .db import db                         # <-- ensure this is imported

def create_app():
    app = Flask(__name__)
    configure_app(app)
    db.init_app(app)

    # -- Logging: rotating file logger --
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(logs_dir / "app.log", maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info("🚀 app started, logging to %s", logs_dir / "app.log")  # <-- forces file creation

    with app.app_context():
        from .models import WeatherRecord
        db.create_all()

    @app.get("/health")
    def health():
        return jsonify(ok=True, version="0.1.0")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found"), 404

    @app.errorhandler(Exception)
    def internal(e):
        app.logger.exception("Unhandled error")
        return jsonify(error="Internal Server Error"), 500

    @app.before_request
    def _start_timer():
        setattr(app, "_req_start", time())

    @app.after_request
    def _log_response(resp):
        try:
            dur_ms = (time() - getattr(app, "_req_start", time())) * 1000
            app.logger.info("%s %s %s %d %.1fms",
                            request.method, request.path, request.remote_addr,
                            resp.status_code, dur_ms)
        except Exception:
            pass
        return resp

    from .routes.records import bp as records_bp
    app.register_blueprint(records_bp, url_prefix="/records")
    return app
