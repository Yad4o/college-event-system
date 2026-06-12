from pydantic import BaseModel
from datetime import datetime


class AttendanceScanRequest(BaseModel):
    qr_token: str


class AttendanceRead(BaseModel):
    id: int
    event_id: int
    user_id: int
    marked_at: datetime

    model_config = {"from_attributes": True}
