from flask import Flask, jsonify
from .config import configure_app
from .db import db

def create_app():
    app = Flask(__name__)
    configure_app(app)
    db.init_app(app)

    with app.app_context():
        from .models import WeatherRecord
        db.create_all()

    # Health check
    @app.get("/health")
    def health():
        return jsonify(ok=True, version="0.1.0")
    @app.get("/__routes")
    def list_routes():
        rules = []
        for r in app.url_map.iter_rules():
            rules.append({
                "rule": r.rule,
                "methods": sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"})
            })
        # Sort for stable display
        rules.sort(key=lambda x: x["rule"])
        return jsonify(rules)

    # ✅ Always return JSON for 404s (no more HTML pages)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found"), 404

    # (Optional) accept both /path and /path/
    # app.url_map.strict_slashes = False

    # Register blueprints
    from .routes.records import bp as records_bp
    app.register_blueprint(records_bp, url_prefix="/records")

    return app
