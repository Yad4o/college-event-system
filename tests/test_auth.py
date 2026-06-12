"""
Tests for Phase 1 — Auth endpoints.

The conftest.py fixtures (client, db_session, test_user, test_admin) are used
directly; no additional setup needed here.
"""

import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


# ── /auth/register ───────────────────────────────────────────────────────────

def test_register_success(client: TestClient):
    resp = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert body["is_email_verified"] is False


def test_register_duplicate_email(client: TestClient, test_user):
    resp = client.post("/auth/register", json={
        "email": test_user.email,
        "full_name": "Duplicate",
        "password": "securepassword",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_register_short_password(client: TestClient):
    resp = client.post("/auth/register", json={
        "email": "short@example.com",
        "full_name": "Short Pass",
        "password": "abc",
    })
    assert resp.status_code == 422


# ── /auth/verify-email ────────────────────────────────────────────────────────

def test_verify_email_valid_token(client: TestClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    token = secrets.token_urlsafe(32)
    user = User(
        email="verify@example.com",
        full_name="Verify Me",
        password_hash=hash_password("password123"),
        role=UserRole.student,
        is_email_verified=False,
        email_verify_token=token,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.get(f"/auth/verify-email?token={token}")
    assert resp.status_code == 200
    assert resp.json()["is_email_verified"] is True


def test_verify_email_invalid_token(client: TestClient):
    resp = client.get("/auth/verify-email?token=doesnotexist")
    assert resp.status_code == 400


def test_verify_email_token_cleared_after_use(client: TestClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    token = secrets.token_urlsafe(32)
    user = User(
        email="verify2@example.com",
        full_name="Verify Twice",
        password_hash=hash_password("password123"),
        role=UserRole.student,
        is_email_verified=False,
        email_verify_token=token,
    )
    db_session.add(user)
    db_session.commit()

    client.get(f"/auth/verify-email?token={token}")
    # Second use should fail
    resp = client.get(f"/auth/verify-email?token={token}")
    assert resp.status_code == 400


# ── /auth/login ───────────────────────────────────────────────────────────────

def test_login_success(client: TestClient, test_user):
    resp = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "password123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient, test_user):
    resp = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_nonexistent_email(client: TestClient):
    resp = client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


def test_login_unverified_email(client: TestClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    user = User(
        email="unverified@example.com",
        full_name="Unverified",
        password_hash=hash_password("password123"),
        role=UserRole.student,
        is_email_verified=False,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/login", json={
        "email": "unverified@example.com",
        "password": "password123",
    })
    assert resp.status_code == 403
    assert "not verified" in resp.json()["detail"]


# ── /auth/forgot-password and /auth/reset-password ───────────────────────────

def test_forgot_password_always_204(client: TestClient):
    # Even for non-existent email, returns 204 (no user enumeration)
    resp = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 204


def test_reset_password_valid_token(client: TestClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    token = secrets.token_urlsafe(32)
    user = User(
        email="reset@example.com",
        full_name="Reset User",
        password_hash=hash_password("oldpassword"),
        role=UserRole.student,
        is_email_verified=True,
        password_reset_token=token,
        password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "newpassword123",
    })
    assert resp.status_code == 204

    # Should now be able to log in with new password
    login_resp = client.post("/auth/login", json={
        "email": "reset@example.com",
        "password": "newpassword123",
    })
    assert login_resp.status_code == 200


def test_reset_password_invalid_token(client: TestClient):
    resp = client.post("/auth/reset-password", json={
        "token": "badtoken",
        "new_password": "newpassword123",
    })
    assert resp.status_code == 400


def test_reset_password_expired_token(client: TestClient, db_session):
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    token = secrets.token_urlsafe(32)
    user = User(
        email="expired@example.com",
        full_name="Expired Token",
        password_hash=hash_password("oldpassword"),
        role=UserRole.student,
        is_email_verified=True,
        password_reset_token=token,
        password_reset_expires=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "newpassword123",
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"]


# ── /auth/refresh ─────────────────────────────────────────────────────────────

def test_refresh_no_cookie(client: TestClient):
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_with_valid_cookie(client: TestClient, test_user):
    # Login first to set the cookie
    login_resp = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "password123",
    })
    assert login_resp.status_code == 200

    # Refresh endpoint reads the cookie set by TestClient
    refresh_resp = client.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


# ── /users/me ─────────────────────────────────────────────────────────────────

def _get_token(client: TestClient, user) -> str:
    resp = client.post("/auth/login", json={
        "email": user.email,
        "password": "password123",
    })
    return resp.json()["access_token"]


def test_get_me(client: TestClient, test_user):
    token = _get_token(client, test_user)
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user.email


def test_get_me_no_token(client: TestClient):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_patch_me(client: TestClient, test_user):
    token = _get_token(client, test_user)
    resp = client.patch(
        "/users/me",
        json={"bio": "Hello world", "branch": "CS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bio"] == "Hello world"
    assert body["branch"] == "CS"


def test_get_other_user(client: TestClient, test_user, test_admin):
    token = _get_token(client, test_user)
    resp = client.get(
        f"/users/{test_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == test_admin.id


def test_get_nonexistent_user(client: TestClient, test_user):
    token = _get_token(client, test_user)
    resp = client.get("/users/99999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ── security utils unit tests ─────────────────────────────────────────────────

def test_hash_and_verify_password():
    from app.utils.security import hash_password, verify_password
    h = hash_password("mysecret")
    assert h != "mysecret"
    assert verify_password("mysecret", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_round_trip():
    from app.utils.jwt import create_access_token, decode_token
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_jwt_tampered_raises():
    from app.utils.jwt import create_access_token, decode_token
    import pytest
    from fastapi import HTTPException
    token = create_access_token({"sub": "42"})
    tampered = token[:-4] + "xxxx"
    with pytest.raises(HTTPException) as exc:
        decode_token(tampered)
    assert exc.value.status_code == 401
