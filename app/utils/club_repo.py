from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.club import Club, ClubMembership


def get_club_by_id(db: Session, club_id: int) -> Club | None:
    return db.query(Club).filter(Club.id == club_id).first()


def get_clubs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    domain: str | None = None,
) -> list[Club]:
    q = db.query(Club).filter(Club.is_active == True, Club.is_suspended == False)
    if domain:
        q = q.filter(Club.domain == domain)
    return q.offset(skip).limit(limit).all()


def create_club(db: Session, data, created_by_id: int) -> Club:
    """Create a club and add the creator as president."""
    club = Club(
        name=data.name,
        description=data.description,
        domain=data.domain,
        join_type=data.join_type,
        social_links=data.social_links,
    )
    db.add(club)
    db.flush()

    from app.models.club import ClubMemberRole
    membership = ClubMembership(
        user_id=created_by_id,
        club_id=club.id,
        role=ClubMemberRole.president,
    )
    db.add(membership)
    db.commit()
    db.refresh(club)
    return club


def get_member_count(db: Session, club_id: int) -> int:
    return db.query(func.count(ClubMembership.id)).filter(
        ClubMembership.club_id == club_id
    ).scalar() or 0


def is_member(db: Session, user_id: int, club_id: int) -> bool:
    return (
        db.query(ClubMembership)
        .filter(ClubMembership.user_id == user_id, ClubMembership.club_id == club_id)
        .first()
    ) is not None


def get_membership(db: Session, user_id: int, club_id: int) -> ClubMembership | None:
    return (
        db.query(ClubMembership)
        .filter(ClubMembership.user_id == user_id, ClubMembership.club_id == club_id)
        .first()
    )
