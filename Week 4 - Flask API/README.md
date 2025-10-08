# Week 4 — Flask API (Weather & History Microservice)

A simple Flask API project built as part of my API Learning Series (Week 4).
This week focuses on understanding how APIs work **from the server side** — building and running your own REST endpoints instead of just consuming them.

---

## Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup (Windows)](#setup-windows)
- [Run](#run)
- [Configuration (.env)](#configuration-env)
- [Endpoints](#endpoints)
- [Testing Examples (PowerShell-safe)](#testing-examples-powershell-safe)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Tips (PowerShell curl gotchas)](#tips-powershell-curl-gotchas)
- [Status / Roadmap](#status--roadmap)
- [License](#license)

---

## 📚 Overview

This project teaches **backend fundamentals with Flask**:

- Route basics (GET/POST)
- Path params (e.g., `/hello/<name>`, `/square/<int:n>`)
- Query params (e.g., `/add?a=5&b=9`)
- JSON body handling (e.g., `POST /echo`)
- Clean JSON error responses for `404` and `500` (optional global `400`)
- Request logging (rotating logs + simple access log)
- Safe configuration (no secrets in git; `.env.example` only)

This project replaces the earlier “Weather CLI” and “Node.js CLI” weeks by switching perspective: instead of calling APIs, you *build one.*

---

## 🧠 What You’ll Learn

| Concept               | Description                                                |
| --------------------- | ---------------------------------------------------------- |
| Flask setup           | Create and run a simple server with endpoints              |
| Routing               | Handle different HTTP methods and paths                    |
| Error handling        | Return clean JSON responses for 404 and 500s               |
| Environment variables | Use `.env` safely without committing secrets               |
| Logging               | Write rotating logs for API activity                       |
| Git hygiene           | Avoid leaking secrets and manage repo connections properly |

---

## ⚙️ Tech Stack

* **Language:** Python 3.13
* **Framework:** Flask
* **Logging:** `logging` + `RotatingFileHandler`
* **Environment:** `python-dotenv`
* **Version Control:** Git + GitHub (org: [James-api-lab](https://github.com/James-api-lab))

---

## 🗂️ Project Structure

```
Week 4 - Flask API/
│
├─ app.py # Flask app (routes, errors, logging hooks)
├─ config.py # Config object (VERSION, DEBUG, APP_NAME, OPENWEATHER_KEY, JSON_SORT_KEYS)
├─ README.md
├─ .gitignore # ignores .venv, pycache, logs, .env, data logs
├─ .env.example # placeholder env file (do not put real keys here)
├─ requirements.txt # optional; can also pip install directly
├─ logs/ # rotating file logs (created at runtime)
└─ data/
└─ access.log # simple text access log (appends per request)
```

---

## 🚀 Running Locally

```bash
# 1. Activate virtual environment (Windows)
.venv\Scripts\activate

# 2. Install dependencies
pip install flask python-dotenv

# 3. Run the app
python app.py
# Server: http://127.0.0.1:5000
'''

---

## 🧩 Example Routes

| Route             | Method   | Purpose               | Notes / Example                                                      |
| ----------------- | -------- | --------------------- | -------------------------------------------------------------------- |
| `/`               | GET      | Liveness JSON         | → `{"message":"Week 4 Flask API is live"}`                           |
| `/health`         | GET      | Uptime + version      | Uses app start time + `VERSION`                                      |
| `/meta`           | GET      | App metadata          | Includes `APP_NAME`, `VERSION`, server time, docs                    |
| `/demo`           | GET/POST | Simple method echo    | GET → ready, POST → received                                         |
| `/list`           | GET      | Array → JSON          | `{"numbers":[1,2,3], ...}`                                           |
| `/status`         | GET      | Custom status code    | Returns `201`                                                        |
| `/headers`        | GET      | Request headers (dev) | Debug only; consider guarding in prod                                |
| `/hello/<name>`   | GET      | **Path param** demo   | `/hello/James`                                                       |
| `/square/<int:n>` | GET      | **Typed** path param  | `/square/7` → `{"number":7,"squared":49}`                            |
| `/add`            | GET      | **Query** params demo | `/add?a=5&b=9` → `{"operation":"add","a":5.0,"b":9.0,"result":14.0}` |
| `/echo`           | POST     | **JSON body** echo    | Body: `{"msg":"hi"}` → echoes JSON                                   |

## Error Handling

404 → {"error":"Route not found", "hint":"Check your endpoint name"}
500 → {"error":"Internal server error"} (and logs the exception)
(Optional) 400 global handler for bad input:
If you add a global 400/BadRequest handler, invalid query/body parsing stays consistent as JSON.
---

## 🛡️ Security Practices

✅ `.env` is ignored by Git and only `.env.example` is shared
✅ Git history cleaned of API keys using `git-filter-repo`
✅ Repository now uses GitHub push protection for secrets
✅ Safe logging enabled (no sensitive data written to logs)

---

## 🧱️ Next Steps

✅ Day 1: Base Flask app, JSON 404/500, logging, metadata
✅ Day 2: Path params, query params, POST JSON echo
🔜 Day 3: /weather/<city> using OpenWeather + .env
🔜 Day 4: Serve CSV history (/history, filters)
🔜 Day 5: POST validation & schema-style responses

---

## 🔹 Repository

🔗 [https://github.com/James-api-lab/week4-flask-api](https://github.com/James-api-lab/week4-flask-api)
