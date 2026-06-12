"""
Celery Beat periodic task — sends 24-hour reminder emails for upcoming events.

Scheduled to run every hour in app/worker.py.
For each non-cancelled event whose start_at falls between now+23h and now+25h,
it fans out one send_reminder_email task per confirmed RSVP holder.
"""

from datetime import datetime, timedelta, timezone

from app.worker import celery_app
from app.database import SessionLocal
from app.models.event import Event, EventRSVP, RSVPStatus


@celery_app.task(name="tasks.send_event_reminders")
def send_event_reminders() -> dict:
    """
    Find events starting in ~24 hours and dispatch per-user reminder emails.

    Returns a summary dict so Celery Beat logs show meaningful output.
    """
    from app.tasks.email import send_reminder_email  # local import avoids circular deps

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(hours=23)
        window_end   = now + timedelta(hours=25)

        events = (
            db.query(Event)
            .filter(
                Event.is_cancelled == False,
                Event.start_at >= window_start,
                Event.start_at <= window_end,
            )
            .all()
        )

        dispatched = 0
        for event in events:
            confirmed_rsvps = (
                db.query(EventRSVP)
                .filter(
                    EventRSVP.event_id == event.id,
                    EventRSVP.status == RSVPStatus.confirmed,
                )
                .all()
            )

            # Format start_at as a human-readable UTC string for the email body
            start_str = event.start_at.strftime("%A, %d %B %Y at %H:%M UTC")

            for rsvp in confirmed_rsvps:
                send_reminder_email.delay(
                    rsvp.user.email,
                    event.title,
                    start_str,
                    event.id,
                )
                dispatched += 1

        return {"events_processed": len(events), "emails_dispatched": dispatched}
    finally:
        db.close()
