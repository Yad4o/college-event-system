"""
Auth business logic.
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.utils.security import verify_password, hash_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.user_repo import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_token,
    get_user_by_reset_token,
    create_user,
)


def register(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = create_user(
        db,
        email=data.email,
        full_name=data.full_name,
        plain_password=data.password,
        branch=data.branch,
        year=data.year,
    )

    token = secrets.token_urlsafe(32)
    user.email_verify_token = token
    db.commit()
    db.refresh(user)

    from app.tasks.email import send_verification_email
    send_verification_email.delay(user.email, token)

    return user


def verify_email(db: Session, token: str) -> User:
    user = get_user_by_token(db, verify_token=token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    user.is_email_verified = True
    user.email_verify_token = None
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, data: LoginRequest) -> dict:
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Check your inbox.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    sub = str(user.id)
    return {
        "access_token": create_access_token({"sub": sub}),
        "refresh_token": create_refresh_token({"sub": sub}),
        "token_type": "bearer",
    }


async def refresh_access_token(db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    jti = payload.get("jti")
    if jti:
        from app.utils.redis_client import get_redis
        redis = await get_redis()
        if await redis.get(f"blocklist:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

    user = get_user_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }


async def logout(refresh_token: str) -> None:
    """Blocklist the refresh token's jti in Redis so it cannot be reused."""
    try:
        payload = decode_token(refresh_token)
    except HTTPException:
        return  # already invalid — nothing to blocklist

    jti = payload.get("jti")
    if not jti:
        return

    exp = payload.get("exp")
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max((exp - now) if exp else 0, 1)

    from app.utils.redis_client import get_redis
    redis = await get_redis()
    await redis.setex(f"blocklist:{jti}", ttl, "1")


def forgot_password(db: Session, email: str) -> None:
    user = get_user_by_email(db, email)
    if not user:
        return

    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    from app.tasks.email import send_password_reset_email
    send_password_reset_email.delay(user.email, token)


def reset_password(db: Session, token: str, new_password: str) -> None:
    user = get_user_by_reset_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    expires = user.password_reset_expires
    if expires is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
