# 🧱 Week 5 — Flask CRUD + Persistence  
### *Learning APIs Project*

---

## 📚 Overview

This week marks your transition from *API consumer* to *API creator*.

You’ve already built stateless APIs that fetched external data.  
Now, you’re building **persistent**, **database-backed** APIs that own and manage their own data using:

- **Flask** — lightweight Python web framework for routes & requests  
- **SQLite** — local relational database (single `.db` file)  
- **SQLAlchemy** — ORM translating Python objects ↔ SQL tables  
- **CRUD pattern** — Create, Read, Update, Delete routes for full data control  

By the end of Week 5 you’ll have:
✅ A functioning Flask + SQLite backend  
✅ Real CRUD endpoints  
✅ Validation & error handling  
✅ Basic tests  
✅ A mental model for migrating to **FastAPI** next week  

---

## 🗂️ Folder Structure

```bash
week5-flask-crud/
├─ app/
│  ├─ __init__.py        # Flask app factory, blueprints, error handlers
│  ├─ config.py          # Database & environment configuration
│  ├─ db.py              # SQLAlchemy instance
│  ├─ models.py          # ORM model(s) — WeatherRecord
│  └─ routes/
│     └─ records.py      # CRUD + stats routes
│
├─ data/                 # SQLite database file (weather.db)
├─ logs/                 # Rotating logs (future)
├─ scripts/
│  └─ seed.py            # Seed example data
│
├─ .env / .env.example
├─ .gitignore
├─ requirements.txt
├─ run.py
└─ README.md
```

---

## ⚙️ Setup

```bash
python -m venv .venv
source .venv/bin/activate         # macOS/Linux
# .\.venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt
python run.py
```

Check health:

```bash
curl http://127.0.0.1:5000/health
```
→ `{"ok": true, "version": "0.1.0"}` ✅

---

## 🚀 Endpoints

Base: `http://127.0.0.1:5000`

### ➕ POST /records/
Create a record:
```bash
curl -X POST http://127.0.0.1:5000/records/   -H "Content-Type: application/json"   -d '{"city":"Seattle","temp":18,"humidity":70}'
```

### 📖 GET /records/
Read all:
```bash
curl http://127.0.0.1:5000/records/
```

Supports pagination:
```
/records?limit=10&offset=5
```

### 🔍 GET /records/<id>
Read one record:
```bash
curl http://127.0.0.1:5000/records/1
```

### 🧩 PUT /records/<id>
Update existing:
```bash
curl -X PUT http://127.0.0.1:5000/records/1   -H "Content-Type: application/json"   -d '{"city":"Seattle (Updated)","temp":19}'
```

### 🗑️ DELETE /records/<id>
Delete a record:
```bash
curl -X DELETE http://127.0.0.1:5000/records/2
```

### 📊 GET /records/stats
Grouped averages:
```bash
curl http://127.0.0.1:5000/records/stats
```
→
```json
[
  {"city":"Seattle","avg_temp":18.5,"count":3},
  {"city":"Tokyo","avg_temp":24.0,"count":2}
]
```

---

## ⚠️ Validation & Error Contract (Day 2–3)

Every endpoint returns **JSON** responses — even errors.

### Common 4xx responses
```json
{"error": "field `city` is required as a string"}
{"error": "`limit` must be an integer between 1 and 100"}
{"error": "record not found"}
{"error": "Not Found"}   // from global 404 handler
```

### Global 404 handler (in `app/__init__.py`)
```python
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not Found"), 404
```

Ensures consistent JSON for any missing route or resource.

---

## 🧠 Key Concepts (Day 3)

| Concept | Description |
|----------|--------------|
| **Idempotence** | `PUT` and `DELETE` can be repeated without side effects |
| **Commit** | `db.session.commit()` makes database changes permanent |
| **Predictable Errors** | Clients can parse JSON 404s consistently |
| **Git Analogy** | PUT/DELETE changes mirror editing/removing files + commits |
| **Flask Error Handling** | Global handler ensures a consistent contract |

---

## 🧪 Example Tests

```python
def test_put_and_delete(client):
    r = client.post("/records/", json={"city": "TestCity", "temp": 20})
    rid = r.get_json()["id"]

    # Update existing
    u = client.put(f"/records/{rid}", json={"temp": 25})
    assert u.status_code == 200

    # Delete existing
    d = client.delete(f"/records/{rid}")
    assert d.status_code == 200

    # Missing
    miss = client.delete(f"/records/999999")
    assert miss.status_code == 404
```

Run with:
```bash
pytest -q
```

---

## 🧭 Instructor Notes — Day 3 Milestone

✅ `PUT` & `DELETE` endpoints operational  
✅ Global JSON 404 handler implemented  
✅ End-to-end CRUD now consistent  
✅ Ready for Day 4 (Stats + Seeding + Testing)

---

## 🧩 Reflection Prompts

1. What’s the difference between *route not found* and *resource not found*?  
2. Why is idempotence valuable in REST design?  
3. Why should APIs always return JSON instead of HTML for errors?  
4. How does `commit()` in SQLAlchemy resemble `git commit`?

---

## 🏁 End of Week 5 — Day 3 Milestone

✅ Flask + SQLAlchemy persistence  
✅ POST/GET/PUT/DELETE working  
✅ Validation and error handling  
✅ Predictable JSON error contract  
✅ Tests passing
