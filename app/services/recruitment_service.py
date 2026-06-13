"""
Recruitment drive service — Phase 29.

Drive lifecycle  (club president / college_admin):
  create_drive, get_drives, get_drive, update_drive, close_drive

Student application:
  apply            — submit answers within the open window
  get_applications — club president sees all; applicant sees own

Status update (club president / college_admin):
  update_application_status — shortlisted | selected | rejected
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.club import ClubMembership, ClubMemberRole
from app.models.recruitment import (
    RecruitmentApplication,
    RecruitmentApplicationStatus,
    RecruitmentDrive,
)
from app.models.user import User, UserRole
from app.schemas.recruitment import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusUpdate,
    DriveCreate,
    DriveRead,
    DriveUpdate,
)
from app.utils.club_repo import get_club_by_id


# ── guards ────────────────────────────────────────────────────────────────────

def _assert_president(db: Session, user: User, club_id: int) -> None:
    if user.role == UserRole.college_admin:
        return
    mem = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club president or college admin can manage recruitment drives",
        )


def _get_drive_or_404(db: Session, drive_id: int) -> RecruitmentDrive:
    drive = db.get(RecruitmentDrive, drive_id)
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
    return drive


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── drive CRUD ────────────────────────────────────────────────────────────────

def create_drive(db: Session, club_id: int, data: DriveCreate, current_user: User) -> DriveRead:
    club = get_club_by_id(db, club_id)
    if not club or club.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    _assert_president(db, current_user, club_id)

    drive = RecruitmentDrive(
        club_id=club_id,
        title=data.title,
        description=data.description,
        open_roles=data.open_roles,
        form_questions=data.form_questions,
        opens_at=data.opens_at,
        closes_at=data.closes_at,
        is_active=True,
    )
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return _drive_read(drive)


def get_drives(db: Session, club_id: int, active_only: bool = False) -> list[DriveRead]:
    q = db.query(RecruitmentDrive).filter(RecruitmentDrive.club_id == club_id)
    if active_only:
        q = q.filter(RecruitmentDrive.is_active == True)
    drives = q.order_by(RecruitmentDrive.opens_at.desc()).all()
    return [_drive_read(d) for d in drives]


def get_drive(db: Session, drive_id: int) -> DriveRead:
    return _drive_read(_get_drive_or_404(db, drive_id))


def update_drive(
    db: Session, drive_id: int, data: DriveUpdate, current_user: User
) -> DriveRead:
    drive = _get_drive_or_404(db, drive_id)
    _assert_president(db, current_user, drive.club_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(drive, field, value)

    db.commit()
    db.refresh(drive)
    return _drive_read(drive)


def close_drive(db: Session, drive_id: int, current_user: User) -> DriveRead:
    drive = _get_drive_or_404(db, drive_id)
    _assert_president(db, current_user, drive.club_id)
    drive.is_active = False
    db.commit()
    db.refresh(drive)
    return _drive_read(drive)


# ── applications ──────────────────────────────────────────────────────────────

def apply(
    db: Session, drive_id: int, data: ApplicationCreate, current_user: User
) -> ApplicationRead:
    drive = _get_drive_or_404(db, drive_id)
    now = _now()

    if not drive.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This recruitment drive is closed",
        )
    if now < drive.opens_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruitment has not opened yet",
        )
    if now > drive.closes_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruitment window has closed",
        )

    # Validate answer count matches question count (if questions exist)
    q_count = len(drive.form_questions or [])
    if q_count and len(data.answers) != q_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected {q_count} answer(s), got {len(data.answers)}",
        )

    app_row = RecruitmentApplication(
        drive_id=drive_id,
        applicant_id=current_user.id,
        desired_role=data.desired_role,
        answers=data.answers,
        status=RecruitmentApplicationStatus.applied,
    )
    db.add(app_row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this drive",
        )
    db.refresh(app_row)
    return _app_read(app_row)


def get_applications(
    db: Session, drive_id: int, current_user: User
) -> list[ApplicationRead]:
    drive = _get_drive_or_404(db, drive_id)

    # Club president / college_admin sees everyone; student sees only their own
    is_admin = current_user.role == UserRole.college_admin
    is_president = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == current_user.id,
            ClubMembership.club_id == drive.club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    ) is not None

    q = db.query(RecruitmentApplication).filter(
        RecruitmentApplication.drive_id == drive_id
    )
    if not (is_admin or is_president):
        q = q.filter(RecruitmentApplication.applicant_id == current_user.id)

    return [_app_read(a) for a in q.all()]


def update_application_status(
    db: Session,
    drive_id: int,
    app_id: int,
    data: ApplicationStatusUpdate,
    current_user: User,
) -> ApplicationRead:
    drive = _get_drive_or_404(db, drive_id)
    _assert_president(db, current_user, drive.club_id)

    app_row = (
        db.query(RecruitmentApplication)
        .filter(
            RecruitmentApplication.id == app_id,
            RecruitmentApplication.drive_id == drive_id,
        )
        .first()
    )
    if not app_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )

    app_row.status = data.status
    if data.reviewer_notes is not None:
        app_row.reviewer_notes = data.reviewer_notes
    app_row.reviewed_at = _now()

    db.commit()
    db.refresh(app_row)
    return _app_read(app_row)


# ── serialisers ───────────────────────────────────────────────────────────────

def _drive_read(drive: RecruitmentDrive) -> DriveRead:
    return DriveRead(
        id=drive.id,
        club_id=drive.club_id,
        title=drive.title,
        description=drive.description,
        open_roles=drive.open_roles or [],
        form_questions=drive.form_questions or [],
        opens_at=drive.opens_at,
        closes_at=drive.closes_at,
        is_active=drive.is_active,
    )


def _app_read(app: RecruitmentApplication) -> ApplicationRead:
    return ApplicationRead(
        id=app.id,
        drive_id=app.drive_id,
        applicant_id=app.applicant_id,
        desired_role=app.desired_role,
        answers=app.answers or [],
        status=app.status,
        applied_at=app.applied_at,
    )
