from fastapi import APIRouter, Depends, Response, Cookie
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserRead,
)
import app.services.auth_service as auth_svc

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new account and send a verification email."""
    user = auth_svc.register(db, data)
    return user


@router.get("/verify-email", response_model=UserRead)
def verify_email(token: str, db: Session = Depends(get_db)):
    """Mark the account as verified using the emailed token."""
    return auth_svc.verify_email(db, token)


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate and return tokens. Refresh token is set in an HttpOnly cookie."""
    tokens = auth_svc.login(db, data)
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=tokens["access_token"])


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    """Issue a new access token using the HttpOnly refresh cookie."""
    if not refresh_token:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    return auth_svc.refresh_access_token(db, refresh_token)


@router.post("/logout", status_code=204)
def logout(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie("refresh_token")


@router.post("/forgot-password", status_code=204)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Trigger a password-reset email (always 204)."""
    auth_svc.forgot_password(db, data.email)


@router.post("/reset-password", status_code=204)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Consume the reset token and update the password."""
    auth_svc.reset_password(db, data.token, data.new_password)
