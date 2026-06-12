from pydantic import BaseModel
from datetime import datetime
from app.models.certificate import CertificateType


class CertificateRead(BaseModel):
    id: int
    event_id: int
    user_id: int
    certificate_type: CertificateType
    pdf_url: str | None = None
    unique_code: str | None = None
    issued_at: datetime

    model_config = {"from_attributes": True}


class CertificateIssueRequest(BaseModel):
    event_id: int
    certificate_type: CertificateType = CertificateType.participation
