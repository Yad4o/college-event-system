from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "college_event_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # ── Celery Beat periodic tasks ────────────────────────────────────────────
    beat_schedule={
        "send-event-reminders-hourly": {
            "task": "tasks.send_event_reminders",
            # Run at the top of every hour
            "schedule": crontab(minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
