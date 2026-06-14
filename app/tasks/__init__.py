"""Task package imports to ensure Celery registers all task modules."""

from app.tasks import certificate  # noqa: F401
from app.tasks import email  # noqa: F401
from app.tasks import reminders  # noqa: F401
