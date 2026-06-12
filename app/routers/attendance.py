from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.attendance import AttendanceScanRequest, AttendanceRead
from app.services import attendance_service
from app.utils.deps import get_current_user

router = APIRouter(tags=["Attendance"])


@router.post("/attendance/scan", response_model=AttendanceRead, status_code=201)
def scan_attendance(
    body: AttendanceScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a QR token to mark attendance.
    The token is the signed JWT stored on the event row.
    """
    return attendance_service.scan_qr(db, body.qr_token, current_user)


@router.get("/events/{event_id}/attendance", response_model=list[AttendanceRead])
def event_attendance(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List every attendee who scanned in — club admin / college admin only."""
    return attendance_service.get_event_attendance(db, event_id, current_user)


@router.get("/users/me/attendance", response_model=list[AttendanceRead])
def my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's personal attendance history."""
    return attendance_service.get_my_attendance(db, current_user)
