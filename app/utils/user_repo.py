from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.security import hash_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_token(db: Session, *, verify_token: str) -> User | None:
    """Fetch a user whose *email_verify_token* matches *verify_token*."""
    return (
        db.query(User)
        .filter(User.email_verify_token == verify_token)
        .first()
    )


def get_user_by_reset_token(db: Session, token: str) -> User | None:
    """Fetch a user whose *password_reset_token* matches *token*."""
    return (
        db.query(User)
        .filter(User.password_reset_token == token)
        .first()
    )


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    plain_password: str,
    role: UserRole = UserRole.student,
    branch: str | None = None,
    year: int | None = None,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(plain_password),
        role=role,
        branch=branch,
        year=year,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
