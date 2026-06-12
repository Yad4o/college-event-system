from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.event import Event, EventRSVP, RSVPStatus


def get_event_by_id(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id).first()


def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    club_id: int | None = None,
    tags: list[str] | None = None,
) -> list[Event]:
    q = db.query(Event).filter(
        Event.is_cancelled == False,
        Event.is_hidden == False,
    )
    if club_id:
        q = q.filter(Event.club_id == club_id)
    if tags:
        # Return events whose tags JSON array contains ANY of the requested tags
        for tag in tags:
            q = q.filter(Event.tags.contains([tag]))
    return q.order_by(Event.start_at.asc()).offset(skip).limit(limit).all()


def count_confirmed_rsvps(db: Session, event_id: int) -> int:
    return (
        db.query(func.count(EventRSVP.id))
        .filter(EventRSVP.event_id == event_id, EventRSVP.status == RSVPStatus.confirmed)
        .scalar()
        or 0
    )


def count_waitlisted_rsvps(db: Session, event_id: int) -> int:
    return (
        db.query(func.count(EventRSVP.id))
        .filter(EventRSVP.event_id == event_id, EventRSVP.status == RSVPStatus.waitlisted)
        .scalar()
        or 0
    )


def get_first_waitlisted(db: Session, event_id: int) -> EventRSVP | None:
    return (
        db.query(EventRSVP)
        .filter(EventRSVP.event_id == event_id, EventRSVP.status == RSVPStatus.waitlisted)
        .order_by(EventRSVP.waitlist_position.asc())
        .first()
    )


def get_rsvp(db: Session, event_id: int, user_id: int) -> EventRSVP | None:
    return (
        db.query(EventRSVP)
        .filter(EventRSVP.event_id == event_id, EventRSVP.user_id == user_id)
        .first()
    )
