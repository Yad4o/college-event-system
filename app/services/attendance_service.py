"""
Attendance business logic — QR scan, event attendance list, personal history.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.event import EventAttendance, EventRSVP, RSVPStatus
from app.models.club import ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.attendance import AttendanceRead
from app.utils.event_repo import get_event_by_id
from app.utils.qr import decode_event_qr_token


def _assert_club_admin(db: Session, user: User, club_id: int) -> None:
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
            detail="Only the club president or college admin can view attendance",
        )


def scan_qr(db: Session, qr_token: str, current_user: User) -> AttendanceRead:
    """
    Validate a QR token and mark attendance for the current user.

    Guards:
    - 401 if token invalid / expired
    - 404 if the event does not exist
    - 403 if the user has no confirmed RSVP for this event
    - 409 if attendance already recorded (unique constraint)
    """
    payload = decode_event_qr_token(qr_token)
    event_id: int = payload["event_id"]

    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Must have a confirmed RSVP
    rsvp = (
        db.query(EventRSVP)
        .filter(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == current_user.id,
            EventRSVP.status == RSVPStatus.confirmed,
        )
        .first()
    )
    if not rsvp:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No confirmed RSVP found for this event",
        )

    record = EventAttendance(event_id=event_id, user_id=current_user.id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already marked",
        )

    db.refresh(record)
    return AttendanceRead.model_validate(record)


def get_event_attendance(
    db: Session, event_id: int, current_user: User
) -> list[AttendanceRead]:
    """List all attendance records for an event — club admin / college admin only."""
    event = get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _assert_club_admin(db, current_user, event.club_id)

    records = (
        db.query(EventAttendance)
        .filter(EventAttendance.event_id == event_id)
        .order_by(EventAttendance.marked_at.asc())
        .all()
    )
    return [AttendanceRead.model_validate(r) for r in records]


def get_my_attendance(db: Session, current_user: User) -> list[AttendanceRead]:
    """Return the current user's full attendance history, newest first."""
    records = (
        db.query(EventAttendance)
        .filter(EventAttendance.user_id == current_user.id)
        .order_by(EventAttendance.marked_at.desc())
        .all()
    )
    return [AttendanceRead.model_validate(r) for r in records]
