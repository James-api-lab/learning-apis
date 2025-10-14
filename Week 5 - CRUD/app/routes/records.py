from flask import Blueprint, request, jsonify, abort
from sqlalchemy import func
from ..db import db
from ..models import WeatherRecord

bp = Blueprint("records", __name__)

@bp.get("/")
def list_records():
    limit = int(request.args.get("limit", 20))
    rows = WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).limit(limit)
    return jsonify([r.to_dict() for r in rows])

@bp.get("/<int:id>")
def get_record(id):
    rec = WeatherRecord.query.get(id) or abort(404)
    return jsonify(rec.to_dict())

@bp.post("/")
def create_record():
    data = request.get_json() or {}
    if "city" not in data:
        return jsonify(error="city required"), 400
    rec = WeatherRecord(city=data["city"], temp=data.get("temp"), humidity=data.get("humidity"))
    db.session.add(rec)
    db.session.commit()
    return jsonify(rec.to_dict()), 201

@bp.put("/<int:id>")
def update_record(id):
    rec = WeatherRecord.query.get(id) or abort(404)
    data = request.get_json() or {}
    for field in ("city","temp","humidity"):
        if field in data:
            setattr(rec, field, data[field])
    db.session.commit()
    return jsonify(rec.to_dict())

@bp.delete("/<int:id>")
def delete_record(id):
    rec = WeatherRecord.query.get(id) or abort(404)
    db.session.delete(rec)
    db.session.commit()
    return jsonify(deleted=id)

@bp.get("/stats")
def stats():
    results = (
        db.session.query(
            WeatherRecord.city,
            func.avg(WeatherRecord.temp).label("avg_temp"),
            func.count().label("count")
        ).group_by(WeatherRecord.city).all()
    )
    payload = []
    for city, avg_temp, count in results:
        payload.append({"city": city, "avg_temp": float(avg_temp) if avg_temp is not None else None, "count": int(count)})
    return jsonify(payload)
