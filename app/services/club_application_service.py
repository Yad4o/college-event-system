"""
New-club application business logic.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.club import ClubApplication, ClubApplicationStatus, ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.club import ClubCreate
from app.schemas.club_application import (
    NewClubApplicationCreate,
    NewClubApplicationRead,
    NewClubApplicationReview,
)
from app.utils.club_repo import create_club


def apply_new_club(
    db: Session, data: NewClubApplicationCreate, current_user: User
) -> NewClubApplicationRead:
    app = ClubApplication(
        applicant_id=current_user.id,
        club_name=data.club_name,
        description=data.description,
        domain=data.domain,
        faculty_advisor_email=data.faculty_advisor_email,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return NewClubApplicationRead.model_validate(app)


def list_applications(
    db: Session, current_user: User, status_filter: str | None = None
) -> list[NewClubApplicationRead]:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    q = db.query(ClubApplication)
    if status_filter:
        try:
            q = q.filter(ClubApplication.status == ClubApplicationStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status filter")
    apps = q.order_by(ClubApplication.created_at.desc()).all()
    return [NewClubApplicationRead.model_validate(a) for a in apps]


def review_application(
    db: Session, app_id: int, review: NewClubApplicationReview, current_user: User
) -> NewClubApplicationRead:
    if current_user.role != UserRole.college_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if review.decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="decision must be approved or rejected",
        )

    app = db.query(ClubApplication).filter(ClubApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if app.status != ClubApplicationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application already reviewed")

    app.status = ClubApplicationStatus(review.decision)
    app.admin_remarks = review.admin_remarks
    app.reviewed_by = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)

    if review.decision == "approved":
        # Create the club; add applicant as president
        from app.schemas.club import ClubCreate
        from app.models.club import JoinType
        club_data = ClubCreate(
            name=app.club_name,
            description=app.description,
            domain=app.domain,
            join_type=JoinType.open,
        )
        create_club(db, club_data, app.applicant_id)
        # create_club already commits; refresh app after
        db.refresh(app)
    else:
        db.commit()
        db.refresh(app)

    return NewClubApplicationRead.model_validate(app)
