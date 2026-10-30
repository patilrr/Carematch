# CareMatch AI

Healthcare Provider Matching & Smart Scheduling Agent — implementation starter.

This repository begins with the backend foundation. It is a prototype using synthetic data only; it is not intended for clinical use or real patient information.

## Initial scope

- FastAPI application and configuration
- SQLAlchemy models for patients, providers, locations, slots, and appointments
- Patient registration/login with password hashing and JWT access tokens
- Provider search and slot availability APIs
- Transactional appointment booking and cancellation endpoints
- Seed data for a small synthetic Pune provider directory
- LangGraph and frontend integration are planned next, after the backend foundations are tested

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; on macOS/Linux use: cp .env.example .env
uvicorn app.main:app --reload --app-dir backend
```

Open `http://127.0.0.1:8000/docs` for Swagger UI and `http://127.0.0.1:8000/health` for the health check.

The default database is a local SQLite file for easy development. To use PostgreSQL, set `DATABASE_URL` in `.env` to a PostgreSQL SQLAlchemy URL, for example `postgresql+psycopg://carematch:change-me@localhost:5432/carematch`.

## Seed synthetic providers

With the API dependencies installed and `.env` configured:

```bash
python seed_data/seed_demo.py
```

This creates demo doctors, specialties, hospitals, doctor-language records, and future fixed-duration slots. It does not create real patient accounts.

## Authentication

Register with `POST /api/v1/auth/register`, then log in with `POST /api/v1/auth/login`. Use the returned bearer token in Swagger's **Authorize** control as `Bearer <token>`.

## Important limitations

- The initial backend is a foundation, not the complete CareMatch AI release.
- Provider matching currently uses structured filters, not the LLM.
- Appointment slots are synthetic and booking is simulated in the local database.
- No live insurance verification, hospital integration, SMS, email, or WhatsApp delivery is included.
- The urgent-care logic is not yet implemented; do not use this prototype to triage real symptoms.
- The first migration approach uses SQLAlchemy `create_all` for local development. Alembic migrations and production deployment hardening remain planned work.
- Use synthetic data only. Configure a strong `JWT_SECRET_KEY` before sharing or deploying the app.
