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
    _: User = Depends(get_current_user),
):
    return club_service.get_clubs(db, skip=skip, limit=limit, domain=domain)


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
    _: User = Depends(get_current_user),
):
    return club_service.get_club(db, club_id)


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
