"""
Signed JWT tokens used for QR-based event attendance scanning.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import settings


def generate_event_qr_token(event_id: int) -> str:
    """Issue a token valid from 1 hour before event start until 4 hours after."""
    payload = {
        "event_id": event_id,
        "type": "attendance",
        "exp": datetime.now(timezone.utc) + timedelta(hours=5),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_event_qr_token(token: str) -> dict:
    """Decode and verify a QR attendance token. Raises 401 on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "attendance":
            raise ValueError("wrong type")
        return payload
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired QR token",
        )
