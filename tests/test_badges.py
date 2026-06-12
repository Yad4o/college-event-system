"""
Tests for Phase 26 — Badges endpoints.
"""

import pytest
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

def _token(client, user, password="password123"):
    resp = client.post("/auth/login", json={"email": user.email, "password": password})
    return resp.json()["access_token"]


def _auth(client, user, password="password123"):
    return {"Authorization": f"Bearer {_token(client, user, password)}"}


def _create_badge(client, admin, name="Star Achiever"):
    resp = client.post(
        "/badges",
        json={"name": name, "description": "Awarded for outstanding achievement"},
        headers=_auth(client, admin, "adminpass123"),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Create badge ──────────────────────────────────────────────────────────────

def test_create_badge_as_admin(client: TestClient, test_admin):
    badge = _create_badge(client, test_admin, "Top Contributor")
    assert badge["name"] == "Top Contributor"
    assert badge["id"] is not None


def test_create_badge_as_student_forbidden(client: TestClient, test_user):
    resp = client.post(
        "/badges",
        json={"name": "Sneaky Badge"},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


def test_create_duplicate_badge_conflict(client: TestClient, test_admin):
    _create_badge(client, test_admin, "Unique Badge")
    resp = client.post(
        "/badges",
        json={"name": "Unique Badge"},
        headers=_auth(client, test_admin, "adminpass123"),
    )
    assert resp.status_code == 409


# ── List badges ───────────────────────────────────────────────────────────────

def test_list_badges(client: TestClient, test_admin, test_user):
    _create_badge(client, test_admin, "List Test Badge")
    resp = client.get("/badges", headers=_auth(client, test_user))
    assert resp.status_code == 200
    names = [b["name"] for b in resp.json()]
    assert "List Test Badge" in names


def test_list_badges_requires_auth(client: TestClient):
    resp = client.get("/badges")
    assert resp.status_code == 401


# ── Award badge ───────────────────────────────────────────────────────────────

def test_award_badge_as_admin(client: TestClient, test_admin, test_user):
    badge = _create_badge(client, test_admin, "Award Test Badge")
    resp = client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": badge["id"]},
        headers=_auth(client, test_admin, "adminpass123"),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["badge"]["name"] == "Award Test Badge"


def test_award_badge_as_student_forbidden(client: TestClient, test_admin, test_user):
    badge = _create_badge(client, test_admin, "Forbidden Award Badge")
    resp = client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": badge["id"]},
        headers=_auth(client, test_user),
    )
    assert resp.status_code == 403


def test_award_badge_duplicate_conflict(client: TestClient, test_admin, test_user):
    badge = _create_badge(client, test_admin, "Duplicate Award Badge")
    admin_headers = _auth(client, test_admin, "adminpass123")
    client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": badge["id"]},
        headers=admin_headers,
    )
    resp = client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": badge["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_award_badge_nonexistent_user(client: TestClient, test_admin):
    badge = _create_badge(client, test_admin, "Ghost User Badge")
    resp = client.post(
        "/badges/users/99999",
        params={"badge_id": badge["id"]},
        headers=_auth(client, test_admin, "adminpass123"),
    )
    assert resp.status_code == 404


def test_award_badge_nonexistent_badge(client: TestClient, test_admin, test_user):
    resp = client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": 99999},
        headers=_auth(client, test_admin, "adminpass123"),
    )
    assert resp.status_code == 404


# ── My badges ─────────────────────────────────────────────────────────────────

def test_get_my_badges_empty(client: TestClient, test_user):
    resp = client.get("/badges/me", headers=_auth(client, test_user))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_my_badges_after_award(client: TestClient, test_admin, test_user):
    badge = _create_badge(client, test_admin, "My Badge Test")
    client.post(
        f"/badges/users/{test_user.id}",
        params={"badge_id": badge["id"]},
        headers=_auth(client, test_admin, "adminpass123"),
    )
    resp = client.get("/badges/me", headers=_auth(client, test_user))
    assert resp.status_code == 200
    names = [ub["badge"]["name"] for ub in resp.json()]
    assert "My Badge Test" in names
