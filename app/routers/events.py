from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventRead, EventUpdate, RsvpRead
from app.services import event_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])


# ── Event CRUD ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[EventRead])
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    club_id: int | None = Query(None),
    tags: list[str] | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return event_service.get_events(db, skip=skip, limit=limit, club_id=club_id, tags=tags)


@router.post("", response_model=EventRead, status_code=201)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.create_event(db, data, current_user)


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return event_service.get_event(db, event_id)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.update_event(db, event_id, data, current_user)


@router.patch("/{event_id}/cancel", response_model=EventRead)
def cancel_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return event_service.cancel_event(db, event_id, current_user)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event_service.delete_event(db, event_id, current_user)


# ── RSVP ─────────────────────────────────────────────────────────────────────

@router.post("/{event_id}/rsvp", response_model=RsvpRead, status_code=201)
def rsvp_to_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RSVP to an event.  Confirms directly if seats available, otherwise waitlists."""
    return event_service.rsvp(db, event_id, current_user)


@router.delete("/{event_id}/rsvp", status_code=204)
def cancel_rsvp(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel own RSVP.  Promotes the first waitlisted user automatically."""
    event_service.cancel_rsvp(db, event_id, current_user)


@router.get("/{event_id}/rsvps", response_model=list[RsvpRead])
def list_rsvps(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all RSVPs for an event — club admin / college admin only."""
    return event_service.list_rsvps(db, event_id, current_user)
