from flask import Flask, jsonify
from .config import configure_app
from .db import db

def create_app():
    app = Flask(__name__)
    configure_app(app)
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy is aware of them
        from .models import WeatherRecord
        # Create tables if they don't exist
        db.create_all()

    # Health check
    @app.get("/health")
    def health():
        return jsonify(ok=True, version="0.1.0")

    # Register blueprints
    from .routes.records import bp as records_bp
    app.register_blueprint(records_bp, url_prefix="/records")

    return app
