from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate
from app.services import club_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.get("", response_model=list[ClubRead])
def list_clubs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return club_service.get_clubs(db, skip=skip, limit=limit, domain=domain, current_user=current_user)


@router.post("", response_model=ClubRead, status_code=201)
def create_club(
    data: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return club_service.create_club(db, data, current_user)


@router.get("/{club_id}", response_model=ClubRead)
def get_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return club_service.get_club(db, club_id, current_user)


@router.patch("/{club_id}", response_model=ClubRead)
def update_club(
    club_id: int,
    data: ClubUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return club_service.update_club(db, club_id, data, current_user)


@router.patch("/{club_id}/suspend", response_model=ClubRead)
def suspend_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return club_service.suspend_club(db, club_id, current_user)


@router.delete("/{club_id}", status_code=204)
def delete_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    club_service.delete_club(db, club_id, current_user)


# ── Membership & Join Requests ────────────────────────────────────────────────

@router.post("/{club_id}/join", status_code=201)
def join_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join open club directly or submit a request for invite-only clubs."""
    return club_service.join_club(db, club_id, current_user)


@router.get("/{club_id}/join-requests")
def list_join_requests(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending join requests (club admin only)."""
    return club_service.list_join_requests(db, club_id, current_user)


@router.patch("/{club_id}/join-requests/{request_id}")
def decide_join_request(
    club_id: int,
    request_id: int,
    decision: str = Query(..., pattern="^(approved|rejected)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a join request (club admin only)."""
    return club_service.decide_join_request(db, club_id, request_id, decision, current_user)


@router.delete("/{club_id}/members/{user_id}", status_code=204)
def remove_member(
    club_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from the club."""
    club_service.remove_member(db, club_id, user_id, current_user)
