# 🧱 Week 5 — Flask CRUD + Persistence  
### *Learning APIs Project*

---

## 📚 Overview

This week marks your transition from *API consumer* to *API creator*.

You’ve already built stateless APIs that fetched external data.  
Now, you’re building **persistent**, **database-backed** APIs that own and manage their own data using:

- **Flask** — a lightweight Python web framework for routes and requests.  
- **SQLite** — a local relational database that stores data as a single `.db` file.  
- **SQLAlchemy** — an ORM (Object Relational Mapper) that translates Python objects ↔ SQL tables.  
- **CRUD pattern** — Create, Read, Update, Delete routes to manage records.  

By the end of Week 5, you’ll have:
✅ A functioning Flask + SQLite backend  
✅ Real CRUD endpoints  
✅ Error handling & logging  
✅ Basic tests  
✅ A mental model for migrating to **FastAPI** next week.

---

## 🗂️ Folder Structure

```bash
week5-flask-crud/
├─ app/
│  ├─ __init__.py        # Flask app factory, blueprint registration
│  ├─ config.py          # Database & environment configuration
│  ├─ db.py              # SQLAlchemy instance
│  ├─ models.py          # ORM model(s) — WeatherRecord
│  └─ routes/
│     └─ records.py      # CRUD + stats routes
│
├─ data/                 # Local SQLite database file (weather.db)
├─ logs/                 # Rotating logs will live here
├─ scripts/
│  └─ seed.py            # Script to seed example data
│
├─ .env                  # Local config file (ignored by git)
├─ .env.example          # Example config for teammates
├─ .gitignore            # Ignore venv, logs, DB, etc.
├─ requirements.txt      # Python dependencies
├─ run.py                # Entrypoint for Flask app
└─ README.md             # (This file)
```

---

## ⚙️ Setup & Installation

### 1. Create & activate virtual environment
```bash
python -m venv .venv
. .venv\Scripts\Activate.ps1   # (PowerShell on Windows)
# OR: source .venv/bin/activate (macOS/Linux)
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Flask runs
```bash
python run.py
```

Open your browser or run:
```bash
curl http://127.0.0.1:5000/health
```

✅ Expected:
```json
{"ok": true, "version": "0.1.0"}
```

This confirms Flask + SQLite + SQLAlchemy are working.

---

## 🧩 Configuration

`app/config.py` dynamically creates your SQLite path using absolute references, so you’ll never hit the common “unable to open database file” error.

Environment variables (optional):

```bash
# .env.example
# DATABASE_URL=sqlite:///C:/full/path/to/weather.db
# FLASK_ENV=development
# FLASK_DEBUG=1
```

The app defaults to storing the database at:
```
project_root/data/weather.db
```

---

## 🧠 Concept Recap — Persistence

Until now, your APIs were **stateless** — data disappeared between runs.  
By adding a database, your API gains **state** and can permanently store records.

**Stack interaction:**

```
Client → Flask (routes) → SQLAlchemy (ORM) → SQLite (storage)
```

SQLAlchemy handles the translation between Python and SQL.

---

## 🚀 Usage — CRUD Endpoints

Base URL: `http://127.0.0.1:5000`

### 1. Create Record (`POST /records/`)
Create a new weather record.

```bash
curl.exe -X POST "http://127.0.0.1:5000/records/" ^
  -H "Content-Type: application/json" ^
  -d "{\"city\":\"Seattle\",\"temp\":18,\"humidity\":70}"
```

**Response:**
```json
{
  "id": 1,
  "city": "Seattle",
  "temp": 18.0,
  "humidity": 70.0,
  "created_at": "2025-10-14T03:50:00.000Z"
}
```

---

### 2. Read All Records (`GET /records/`)
```bash
curl.exe "http://127.0.0.1:5000/records/"
```

**Response:**
```json
[
  {"id":1,"city":"Seattle","temp":18.0,"humidity":70.0,"created_at":"..."}
]
```

---

### 3. Read One (`GET /records/<id>`)
```bash
curl.exe "http://127.0.0.1:5000/records/1"
```

---

### 4. Update (`PUT /records/<id>`)
```bash
curl.exe -X PUT "http://127.0.0.1:5000/records/1" ^
  -H "Content-Type: application/json" ^
  -d "{\"temp\":22,\"humidity\":60}"
```

---

### 5. Delete (`DELETE /records/<id>`)
```bash
curl.exe -X DELETE "http://127.0.0.1:5000/records/1"
```

---

### 6. Stats (`GET /records/stats`)
Aggregates data grouped by city.

```bash
curl.exe "http://127.0.0.1:5000/records/stats"
```

**Response:**
```json
[
  {"city":"Seattle","avg_temp":18.5,"count":3},
  {"city":"Tokyo","avg_temp":24.0,"count":2}
]
```

---

## 🧑‍💻 Running the Seed Script

You can preload the database with sample data:

```bash
python -m scripts.seed
```

If you run it again, it will skip reseeding if data already exists.

---

## 🧰 Common PowerShell Tips

PowerShell aliases `curl` → `Invoke-WebRequest`, which doesn’t support `-H` or `-d`.

Use one of:
```bash
Invoke-RestMethod -Uri "http://127.0.0.1:5000/records/" -Method Get
Invoke-RestMethod -Uri "http://127.0.0.1:5000/records/" -Method Post -Body '{"city":"Austin"}' -ContentType "application/json"
# or
curl.exe ...
```

---

## 🧪 Testing (pytest)

Sample test (`tests/test_api.py`):

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_health(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    assert rv.get_json()["ok"]

def test_create_record(client):
    r = client.post("/records/", json={"city": "Testville", "temp": 20})
    assert r.status_code == 201
    data = r.get_json()
    assert data["city"] == "Testville"
```

Run:
```bash
pytest -q
```

---

## 🪵 Logging & Error Handling (Preview)

Logging will rotate automatically when implemented:

```python
from logging.handlers import RotatingFileHandler
import logging

handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

Common error responses:
```json
{"error": "Not Found"}
{"error": "Internal Server Error"}
```

---

## 🧭 Instructor Notes — Day 1 Summary

| Concept | Why It Matters |
|----------|----------------|
| **Persistence** | Keeps data across restarts; makes APIs stateful |
| **SQLite** | Lightweight, self-contained database (perfect for local dev) |
| **ORM (SQLAlchemy)** | Translates Python objects ↔ SQL tables |
| **App Factory Pattern** | Enables modularity, testability, and multiple environments |
| **Blueprints** | Organize routes logically |
| **Absolute DB Paths** | Avoids Windows path errors |

---

## 🧩 Reflection Prompts

1. What does “persistence” mean in the context of APIs?  
2. Why do we need to `commit()` after adding records?  
3. What are the advantages of using an ORM instead of raw SQL?  
4. Why do `/records` and `/records/` both work after adding `app.url_map.strict_slashes = False`?

---

## 📤 Deployment Prep (Stretch)

- Add Dockerfile for containerized runs  
- Add `.env` configuration for production  
- Replace SQLite with PostgreSQL for cloud environments  

---

## 🏁 End of Week 5, Day 1 Milestone

✅ Flask + SQLAlchemy configured  
✅ Database auto-creates and persists data  
✅ `/health` endpoint live  
✅ `/records` CRUD routes available  
✅ Seed script functioning  
✅ Ready for Day 2 (Validation + Read/Write logic deep dive)

---