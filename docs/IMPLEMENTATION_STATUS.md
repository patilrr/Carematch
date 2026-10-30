# Implementation status

## Included in the initial scaffold

- FastAPI application and health endpoint
- Environment-based configuration
- SQLAlchemy entities for patients, specialties, hospitals, doctors, doctor languages, fixed slots, and appointments
- Patient registration/login and JWT bearer authentication
- Structured provider search and available-slot listing
- Appointment booking with explicit confirmation, idempotency key support, database constraints, and cancellation
- Synthetic Pune seed data
- Starter password-hashing test

## Not implemented yet

- LangGraph and OpenAI tool calling
- Rescheduling and transactional replacement-slot handling
- Admin authentication and admin dashboard APIs/UI
- Insurance-plan schema and filtering
- Chat session/message persistence and multilingual orchestration
- Clinical safety escalation workflow
- Reminder worker and notification logs
- Alembic migrations
- React frontend
- Full integration, concurrency, security, and end-to-end tests

## Known prototype caveats

- Local SQLite is intended for easy development. Concurrency behavior must be verified against PostgreSQL before considering the scheduling layer complete.
- Slot generation is demo-only and uses a fixed India timezone offset; production-quality scheduling should use `ZoneInfo('Asia/Kolkata')` and validated working-hour rules.
- The current cancellation route is a starter implementation; appointment events and audit logging still need to be added.
- No real patient data should be entered.
