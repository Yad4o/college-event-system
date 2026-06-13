from pydantic import BaseModel
from datetime import datetime
from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    link_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
