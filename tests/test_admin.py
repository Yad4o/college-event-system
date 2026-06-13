"""
Tests for Phase 35 & 36 — Admin stats and management endpoints.
"""

import pytest
from fastapi.testclient import TestClient


# ── auth helpers ──────────────────────────────────────────────────────────────

def _token_admin(client, admin):
    resp = client.post("/auth/login", json={"email": admin.email, "password": "adminpass123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _token_student(client, user):
    resp = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth_admin(client, admin):
    return {"Authorization": f"Bearer {_token_admin(client, admin)}"}


def _auth_student(client, user):
    return {"Authorization": f"Bearer {_token_student(client, user)}"}


# ── GET /admin/stats ──────────────────────────────────────────────────────────

def test_stats_as_admin(client: TestClient, test_admin):
    resp = client.get("/admin/stats", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 200
    body = resp.json()
    assert "total_users" in body
    assert "total_clubs" in body
    assert "active_clubs" in body
    assert "suspended_clubs" in body
    assert "total_events" in body
    assert "upcoming_events" in body
    assert "total_rsvps" in body
    assert "total_attendance" in body
    assert "total_certificates_issued" in body
    assert body["total_users"] >= 1


def test_stats_student_forbidden(client: TestClient, test_user):
    resp = client.get("/admin/stats", headers=_auth_student(client, test_user))
    assert resp.status_code == 403


def test_stats_unauthenticated(client: TestClient):
    resp = client.get("/admin/stats")
    assert resp.status_code == 401


# ── GET /admin/clubs ──────────────────────────────────────────────────────────

def test_list_all_clubs_includes_suspended(client: TestClient, test_admin):
    create = client.post(
        "/clubs",
        json={"name": "Suspended Club", "domain": "technical", "join_type": "open"},
        headers=_auth_admin(client, test_admin),
    )
    assert create.status_code == 201
    club_id = create.json()["id"]

    client.patch(f"/admin/clubs/{club_id}/suspend", headers=_auth_admin(client, test_admin))

    admin_resp = client.get("/admin/clubs", headers=_auth_admin(client, test_admin))
    assert admin_resp.status_code == 200
    admin_ids = [c["id"] for c in admin_resp.json()]
    assert club_id in admin_ids


def test_list_all_clubs_student_forbidden(client: TestClient, test_user):
    resp = client.get("/admin/clubs", headers=_auth_student(client, test_user))
    assert resp.status_code == 403


# ── PATCH /admin/clubs/{id}/suspend ──────────────────────────────────────────

def test_toggle_suspension(client: TestClient, test_admin):
    create = client.post(
        "/clubs",
        json={"name": "Toggle Me Club", "domain": "cultural", "join_type": "open"},
        headers=_auth_admin(client, test_admin),
    )
    club_id = create.json()["id"]

    resp = client.patch(f"/admin/clubs/{club_id}/suspend", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 200
    assert resp.json()["is_suspended"] is True

    resp2 = client.patch(f"/admin/clubs/{club_id}/suspend", headers=_auth_admin(client, test_admin))
    assert resp2.status_code == 200
    assert resp2.json()["is_suspended"] is False


def test_toggle_suspension_nonexistent(client: TestClient, test_admin):
    resp = client.patch("/admin/clubs/99999/suspend", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 404


# ── GET /admin/users ──────────────────────────────────────────────────────────

def test_list_all_users(client: TestClient, test_admin, test_user):
    resp = client.get("/admin/users", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert test_admin.email in emails
    assert test_user.email in emails


def test_list_users_filter_by_role(client: TestClient, test_admin, test_user):
    resp = client.get("/admin/users?role=student", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 200
    for u in resp.json():
        assert u["role"] == "student"


def test_list_users_invalid_role(client: TestClient, test_admin):
    resp = client.get("/admin/users?role=ghost", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 422


def test_list_users_student_forbidden(client: TestClient, test_user):
    resp = client.get("/admin/users", headers=_auth_student(client, test_user))
    assert resp.status_code == 403


# ── PATCH /admin/users/{id}/role ──────────────────────────────────────────────

def test_change_user_role(client: TestClient, test_admin, test_user):
    resp = client.patch(
        f"/admin/users/{test_user.id}/role",
        json={"role": "club_admin"},
        headers=_auth_admin(client, test_admin),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "club_admin"


def test_change_role_invalid(client: TestClient, test_admin, test_user):
    resp = client.patch(
        f"/admin/users/{test_user.id}/role",
        json={"role": "supervillain"},
        headers=_auth_admin(client, test_admin),
    )
    assert resp.status_code == 422


def test_cannot_demote_last_admin(client: TestClient, test_admin):
    resp = client.patch(
        f"/admin/users/{test_admin.id}/role",
        json={"role": "student"},
        headers=_auth_admin(client, test_admin),
    )
    assert resp.status_code == 400


def test_change_role_student_forbidden(client: TestClient, test_user):
    resp = client.patch(
        f"/admin/users/{test_user.id}/role",
        json={"role": "club_admin"},
        headers=_auth_student(client, test_user),
    )
    assert resp.status_code == 403


# ── GET /admin/budget-report ──────────────────────────────────────────────────

def test_budget_report(client: TestClient, test_admin):
    resp = client.get("/admin/budget-report", headers=_auth_admin(client, test_admin))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_budget_report_student_forbidden(client: TestClient, test_user):
    resp = client.get("/admin/budget-report", headers=_auth_student(client, test_user))
    assert resp.status_code == 403
