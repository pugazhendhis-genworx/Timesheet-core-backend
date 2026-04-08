import os

from celery import Celery  # type: ignore
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://10.125.46.155:6379/0")
from src.data.models.postgres.client_model import Client  # noqa: E402, F401
from src.data.models.postgres.email_model import (  # noqa: E402, F401
    EmailAttachment,
    EmailMessage,
    EmailThread,
    EmailWhitelist,
)

print("Database tables created/verified.")

celery_app = Celery(
    "email_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.workers.tasks.email_watcher", "src.workers.tasks.email_processor"],
)

# Celery Beat schedule — only the watcher is periodic
celery_app.conf.beat_schedule = {
    "watch-new-emails": {
        "task": "src.workers.tasks.email_watcher.watch_emails",
        "schedule": float(os.getenv("WATCH_INTERVAL_SECONDS", 30)),
    },
}

# Route processor tasks to a dedicated 'processor' queue
celery_app.conf.task_routes = {
    "src.workers.tasks.email_watcher.watch_emails": {
        "queue": "pugazh_timeguard_watcher_queue"
    },
    "src.workers.tasks.email_processor.process_email": {
        "queue": "pugazh_timeguard_processor_queue"
    },
}
celery_app.conf.timezone = "UTC"

# Serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
