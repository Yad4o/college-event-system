"""
Event business logic — CRUD, QR token lifecycle, and RSVP / waitlist management.

Cloudinary upload is best-effort: if credentials are missing the poster URL
is simply left as None rather than crashing the request.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.event import Event, EventRSVP, RSVPStatus
from app.models.club import ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventRead, EventUpdate, RsvpRead
from app.utils.event_repo import (
    get_event_by_id,
    get_events as _get_events,
    count_confirmed_rsvps,
    count_waitlisted_rsvps,
    get_first_waitlisted,
    get_rsvp,
)
from app.utils.qr import generate_event_qr_token


# ── internal helpers ──────────────────────────────────────────────────────────

def _to_read(db: Session, event: Event) -> EventRead:
    rsvp_count = count_confirmed_rsvps(db, event.id)
    waitlist_count = count_waitlisted_rsvps(db, event.id)
    return EventRead(
        id=event.id,
        club_id=event.club_id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        tags=event.tags,
        venue=event.venue,
        poster_image_url=event.poster_image_url,
        start_at=event.start_at,
        end_at=event.end_at,
        seat_limit=event.seat_limit,
        is_cancelled=event.is_cancelled,
        is_hidden=event.is_hidden,
        qr_token=event.qr_token,
        rsvp_count=rsvp_count,
        waitlist_count=waitlist_count,
    )


def _assert_club_admin(db: Session, user: User, club_id: int) -> None:
    """Allow college_admin or the club president."""
    if user.role == UserRole.college_admin:
        return
    membership = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club president or college admin can manage events",
        )


def _upload_poster(image_bytes: bytes | None) -> str | None:
    """Best-effort Cloudinary upload.  Returns URL or None on any failure."""
    if not image_bytes:
        return None
    try:
        import cloudinary.uploader  # type: ignore
        result = cloudinary.uploader.upload(
            image_bytes,
            folder="event_posters",
            resource_type="image",
        )
        return result.get("secure_url")
    except Exception:
        return None


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    club_id: int | None = None,
    tags: list[str] | None = None,
) -> list[EventRead]:
    events = _get_events(db, skip=skip, limit=limit, club_id=club_id, tags=tags)
    return [_to_read(db, e) for e in events]


def get_event(db: Session, event_id: int) -> EventRead:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _to_read(db, event)


def create_event(
    db: Session,
    data: EventCreate,
    current_user: User,
    poster_bytes: bytes | None = None,
) -> EventRead:
    _assert_club_admin(db, current_user, data.club_id)

    poster_url = _upload_poster(poster_bytes)

    event = Event(
        club_id=data.club_id,
        title=data.title,
        description=data.description,
        event_type=data.event_type,
        tags=data.tags,
        venue=data.venue,
        poster_image_url=poster_url,
        start_at=data.start_at,
        end_at=data.end_at,
        seat_limit=data.seat_limit,
        is_hidden=data.is_hidden,
    )
    db.add(event)
    db.flush()  # need event.id before generating the QR token

    event.qr_token = generate_event_qr_token(event.id)
    db.commit()
    db.refresh(event)
    return _to_read(db, event)


def update_event(
    db: Session,
    event_id: int,
    data: EventUpdate,
    current_user: User,
) -> EventRead:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    update_data = data.model_dump(exclude_unset=True)
    start_at_changed = "start_at" in update_data

    for field, value in update_data.items():
        setattr(event, field, value)

    if start_at_changed:
        event.qr_token = generate_event_qr_token(event.id)

    db.commit()
    db.refresh(event)
    return _to_read(db, event)


def cancel_event(db: Session, event_id: int, current_user: User) -> EventRead:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    event.is_cancelled = True
    db.commit()
    db.refresh(event)
    return _to_read(db, event)


def delete_event(db: Session, event_id: int, current_user: User) -> None:
    """Hard delete — college_admin only."""
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    db.delete(event)
    db.commit()


# ── RSVP & waitlist ───────────────────────────────────────────────────────────

def rsvp(db: Session, event_id: int, current_user: User) -> RsvpRead:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.is_cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is cancelled")

    if get_rsvp(db, event_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already RSVPed")

    confirmed = count_confirmed_rsvps(db, event_id)

    if event.seat_limit is None or confirmed < event.seat_limit:
        rsvp_row = EventRSVP(
            event_id=event_id,
            user_id=current_user.id,
            status=RSVPStatus.confirmed,
        )
        waitlisted = False
    else:
        waitlisted_count = count_waitlisted_rsvps(db, event_id)
        rsvp_row = EventRSVP(
            event_id=event_id,
            user_id=current_user.id,
            status=RSVPStatus.waitlisted,
            waitlist_position=waitlisted_count + 1,
        )
        waitlisted = True

    db.add(rsvp_row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already RSVPed")

    # Notify user of their RSVP status (part of same transaction)
    try:
        from app.services.notification_service import (
            notify_rsvp_confirmed,
            notify_rsvp_waitlisted,
        )
        if waitlisted:
            notify_rsvp_waitlisted(db, current_user.id, event.title, event_id)
        else:
            notify_rsvp_confirmed(db, current_user.id, event.title, event_id)
    except Exception:
        pass  # notification failure must never abort the RSVP

    db.commit()
    db.refresh(rsvp_row)
    return RsvpRead.model_validate(rsvp_row)


def cancel_rsvp(db: Session, event_id: int, current_user: User) -> None:
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    rsvp_row = get_rsvp(db, event_id, current_user.id)
    if not rsvp_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSVP not found")

    was_confirmed = rsvp_row.status == RSVPStatus.confirmed
    db.delete(rsvp_row)
    db.flush()

    if was_confirmed:
        next_up = get_first_waitlisted(db, event_id)
        if next_up:
            next_up.status = RSVPStatus.confirmed
            next_up.waitlist_position = None

            # Notify promoted user
            try:
                from app.services.notification_service import notify_waitlist_promoted
                notify_waitlist_promoted(db, next_up.user_id, event.title, event_id)
            except Exception:
                pass

            # Dispatch promotion email
            try:
                from app.tasks.email import send_waitlist_promotion_email
                send_waitlist_promotion_email.delay(
                    next_up.user.email,
                    event.title,
                    event_id,
                )
            except Exception:
                pass

    db.commit()


def list_rsvps(db: Session, event_id: int, current_user: User) -> list[RsvpRead]:
    """Return all RSVPs for an event — club admin only."""
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    rows = db.query(EventRSVP).filter(EventRSVP.event_id == event_id).all()
    return [RsvpRead.model_validate(r) for r in rows]
