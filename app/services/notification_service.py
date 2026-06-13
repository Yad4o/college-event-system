"""
Notification service — Phase 32 / 34.

create_notification() is the single internal entry-point used by every other
module to insert a Notification row and push it over WebSocket (Phase 34).

Convenience wrappers keep call-sites clean:
  notify_rsvp_confirmed(db, user_id, event_title, event_id)
  notify_rsvp_waitlisted(db, user_id, event_title, event_id)
  notify_waitlist_promoted(db, user_id, event_title, event_id)
  notify_certificate_ready(db, user_id, event_title, cert_code)
  notify_recruitment_update(db, user_id, drive_title, new_status)
  notify_club_announcement(db, user_ids, club_name, ann_title, club_id)
"""

import asyncio

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    link_url: str | None = None,
) -> Notification:
    """
    Insert a Notification row for *user_id* and schedule a WebSocket push.

    The DB flush is done here so the notification is part of the same atomic
    transaction as the parent action.  The caller is responsible for db.commit().

    The WebSocket push is scheduled as a fire-and-forget asyncio task so it
    never blocks the HTTP response path and never raises to the caller even
    if no socket is connected.
    """
    notif = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link_url=link_url,
    )
    db.add(notif)
    db.flush()  # populate notif.id without committing

    # Phase 34 — push over WebSocket (best-effort, never raises)
    try:
        from app.utils.ws_manager import manager

        if manager.is_connected(user_id):
            payload = {
                "type": "notification",
                "id": notif.id,
                "notification_type": notification_type.value,
                "title": title,
                "message": message,
                "link_url": link_url,
                "is_read": False,
            }
            # Schedule without awaiting so sync callers work fine
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.send_to_user(user_id, payload))
            except RuntimeError:
                # No running event loop (e.g. Celery worker thread) — skip push
                pass
    except Exception:
        pass  # WS push failure must never affect the DB transaction

    return notif


# ── convenience wrappers ──────────────────────────────────────────────────────

def notify_rsvp_confirmed(
    db: Session, user_id: int, event_title: str, event_id: int
) -> None:
    create_notification(
        db,
        user_id=user_id,
        notification_type=NotificationType.rsvp_confirmed,
        title="RSVP Confirmed",
        message=f"You are confirmed for \"{event_title}\".",
        link_url=f"/events/{event_id}",
    )


def notify_rsvp_waitlisted(
    db: Session, user_id: int, event_title: str, event_id: int
) -> None:
    create_notification(
        db,
        user_id=user_id,
        notification_type=NotificationType.rsvp_waitlisted,
        title="Added to Waitlist",
        message=f"You are on the waitlist for \"{event_title}\". We will notify you if a spot opens.",
        link_url=f"/events/{event_id}",
    )


def notify_waitlist_promoted(
    db: Session, user_id: int, event_title: str, event_id: int
) -> None:
    create_notification(
        db,
        user_id=user_id,
        notification_type=NotificationType.rsvp_confirmed,
        title="Spot Available — You Are Confirmed!",
        message=f"A spot opened up for \"{event_title}\" and your RSVP is now confirmed.",
        link_url=f"/events/{event_id}",
    )


def notify_certificate_ready(
    db: Session, user_id: int, event_title: str, cert_code: str
) -> None:
    create_notification(
        db,
        user_id=user_id,
        notification_type=NotificationType.certificate_ready,
        title="Certificate Ready",
        message=f"Your certificate for \"{event_title}\" has been issued.",
        link_url=f"/certificates/{cert_code}/verify",
    )


def notify_recruitment_update(
    db: Session, user_id: int, drive_title: str, new_status: str
) -> None:
    create_notification(
        db,
        user_id=user_id,
        notification_type=NotificationType.recruitment_update,
        title="Application Status Updated",
        message=f"Your application for \"{drive_title}\" is now: {new_status}.",
    )


def notify_club_announcement(
    db: Session, user_ids: list[int], club_name: str, ann_title: str, club_id: int
) -> None:
    """Batch-insert one notification per member and push each over WebSocket."""
    for uid in user_ids:
        create_notification(
            db,
            user_id=uid,
            notification_type=NotificationType.club_announcement,
            title=f"New announcement in {club_name}",
            message=ann_title,
            link_url=f"/clubs/{club_id}/announcements",
        )
