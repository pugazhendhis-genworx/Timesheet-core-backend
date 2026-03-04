# base-rest-service-template

Email processing microservice with FastAPI, Celery workers, and Redis.

## Architecture

```
Celery Beat (scheduler)
   │
   ├─ every 30s ──► watch_emails task ──► Gmail History API
   │                    │
   │                    └── process_email.delay(gmail_message_id) → Celery processor queue
   │
   └─ Processor worker (event-driven, instant pickup)
         │
         ├── get_message_detail() ← Gmail API
         ├── ingest_email_sync()  → PostgreSQL (thread, message, attachment metadata)
         ├── save_attachments()   → disk (attachments/)
         └── mark_as_read()       → Gmail API
```

## Project Structure

```
src/
├── api/rest/          # FastAPI application & routes
├── core/services/     # Business logic (Gmail, email ingestion, whitelist)
├── data/
│   ├── clients/       # Database clients (async + sync engines)
│   └── models/postgres/ # SQLAlchemy models
├── config/            # Pydantic settings
└── workers/           # Celery app, beat schedule, task workers
```

## Quick Start

### Docker (recommended)

```bash
docker compose up -d --build
```

This starts 4 containers:

- `timeiq-redis` — Redis broker
- `timeiq-celery-watcher` — Polls Gmail every 30s
- `timeiq-celery-beat` — Celery Beat scheduler
- `timeiq-celery-processor` — Processes emails (concurrency=4)

### Local

```bash
# FastAPI
uvicorn src.api.rest.app:app --reload

# Celery watcher
celery -A src.workers.celery_app.celery_app worker -Q watcher -l info

# Celery processor
celery -A src.workers.celery_app.celery_app worker -Q processor -l info -c 4

# Celery beat
celery -A src.workers.celery_app.celery_app beat -l info
```
