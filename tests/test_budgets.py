"""
Tests for Phase 30 — Budget CRUD and line item management.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone


# ── helpers ───────────────────────────────────────────────────────────────────

def _token(client, user, password="password123"):
    resp = client.post("/auth/login", json={"email": user.email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(client, user, password="password123"):
    return {"Authorization": f"Bearer {_token(client, user, password)}"}


def _admin_h(client, admin):
    return _auth(client, admin, "adminpass123")


def _make_club(client, admin, name="Budget Club"):
    resp = client.post(
        "/clubs",
        json={"name": name, "domain": "technical", "join_type": "open"},
        headers=_admin_h(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_event(client, admin, club_id, title="Budget Event"):
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = client.post(
        "/events",
        json={
            "club_id": club_id,
            "title": title,
            "event_type": "open",
            "start_at": future,
            "seat_limit": 50,
        },
        headers=_admin_h(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_budget(client, admin, *, event_id=None, club_id=None, allocated=10000.0):
    payload = {"total_allocated": allocated}
    if event_id:
        payload["event_id"] = event_id
    if club_id:
        payload["club_id"] = club_id
    resp = client.post("/budgets", json=payload, headers=_admin_h(client, admin))
    assert resp.status_code == 201, resp.text
    return resp.json()


def _add_item(client, admin, budget_id, amount=500.0, desc="Venue hire"):
    resp = client.post(
        f"/budgets/{budget_id}/items",
        json={"category": "venue", "description": desc, "amount": amount},
        headers=_admin_h(client, admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Budget creation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBudgetCreate:

    def test_create_event_budget(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Create Event Budget Club")
        event = _make_event(client, test_admin, club["id"])
        budget = _create_budget(client, test_admin, event_id=event["id"], allocated=5000.0)
        assert budget["event_id"] == event["id"]
        assert budget["total_allocated"] == 5000.0
        assert budget["total_spent"] == 0.0
        assert budget["items"] == []

    def test_create_club_budget(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Create Club Budget Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=20000.0)
        assert budget["club_id"] == club["id"]
        assert budget["total_allocated"] == 20000.0

    def test_duplicate_event_budget_rejected(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Dup Budget Club")
        event = _make_event(client, test_admin, club["id"])
        _create_budget(client, test_admin, event_id=event["id"])
        resp = client.post(
            "/budgets",
            json={"total_allocated": 999.0, "event_id": event["id"]},
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 409

    def test_missing_target_rejected(self, client: TestClient, test_admin):
        resp = client.post(
            "/budgets",
            json={"total_allocated": 500.0},
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 422

    def test_both_targets_rejected(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Both Target Club")
        event = _make_event(client, test_admin, club["id"])
        resp = client.post(
            "/budgets",
            json={"total_allocated": 500.0, "event_id": event["id"], "club_id": club["id"]},
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 422

    def test_student_cannot_create(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Student Budget Club")
        resp = client.post(
            "/budgets",
            json={"total_allocated": 500.0, "club_id": club["id"]},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# Budget retrieval and update
# ═══════════════════════════════════════════════════════════════════════════════

class TestBudgetGetUpdate:

    def test_get_budget_by_id(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Get Budget Club")
        event = _make_event(client, test_admin, club["id"])
        budget = _create_budget(client, test_admin, event_id=event["id"])
        resp = client.get(f"/budgets/{budget['id']}", headers=_admin_h(client, test_admin))
        assert resp.status_code == 200
        assert resp.json()["id"] == budget["id"]

    def test_get_budget_by_event(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Get Event Budget Club")
        event = _make_event(client, test_admin, club["id"])
        _create_budget(client, test_admin, event_id=event["id"])
        resp = client.get(
            f"/budgets/events/{event['id']}", headers=_admin_h(client, test_admin)
        )
        assert resp.status_code == 200
        assert resp.json()["event_id"] == event["id"]

    def test_get_budgets_by_club(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Get Club Budgets Club")
        _create_budget(client, test_admin, club_id=club["id"], allocated=1000.0)
        resp = client.get(
            f"/budgets/clubs/{club['id']}", headers=_admin_h(client, test_admin)
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_nonexistent_budget(self, client: TestClient, test_admin):
        resp = client.get("/budgets/99999", headers=_admin_h(client, test_admin))
        assert resp.status_code == 404

    def test_update_allocated(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Update Budget Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=1000.0)
        resp = client.patch(
            f"/budgets/{budget['id']}",
            json={"total_allocated": 2000.0},
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["total_allocated"] == 2000.0

    def test_student_cannot_get_budget(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Student Get Budget Club")
        budget = _create_budget(client, test_admin, club_id=club["id"])
        resp = client.get(f"/budgets/{budget['id']}", headers=_auth(client, test_user))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# Line items and total_spent
# ═══════════════════════════════════════════════════════════════════════════════

class TestBudgetItems:

    def test_add_item_updates_total_spent(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Item Total Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=10000.0)
        result = _add_item(client, test_admin, budget["id"], amount=1500.0, desc="Printing")
        assert result["total_spent"] == 1500.0
        assert len(result["items"]) == 1

    def test_multiple_items_sum_correctly(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Multi Item Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=10000.0)
        _add_item(client, test_admin, budget["id"], amount=1000.0, desc="Item A")
        result = _add_item(client, test_admin, budget["id"], amount=2500.0, desc="Item B")
        assert result["total_spent"] == 3500.0
        assert len(result["items"]) == 2

    def test_add_item_with_receipt_url(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Receipt Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=5000.0)
        resp = client.post(
            f"/budgets/{budget['id']}/items",
            json={
                "category": "food",
                "description": "Catering",
                "amount": 800.0,
                "receipt_url": "https://res.cloudinary.com/demo/image/upload/receipt.jpg",
            },
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 201
        item = resp.json()["items"][0]
        assert item["receipt_url"].startswith("https://")

    def test_update_item_recomputes_total(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Update Item Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=10000.0)
        result = _add_item(client, test_admin, budget["id"], amount=1000.0, desc="Venue")
        item_id = result["items"][0]["id"]

        resp = client.patch(
            f"/budgets/{budget['id']}/items/{item_id}",
            json={"amount": 2000.0},
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["total_spent"] == 2000.0

    def test_delete_item_recomputes_total(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Delete Item Club")
        budget = _create_budget(client, test_admin, club_id=club["id"], allocated=10000.0)
        result = _add_item(client, test_admin, budget["id"], amount=500.0, desc="Prizes")
        item_id = result["items"][0]["id"]

        resp = client.delete(
            f"/budgets/{budget['id']}/items/{item_id}",
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 200
        assert resp.json()["total_spent"] == 0.0
        assert resp.json()["items"] == []

    def test_delete_nonexistent_item(self, client: TestClient, test_admin):
        club = _make_club(client, test_admin, "Delete NE Item Club")
        budget = _create_budget(client, test_admin, club_id=club["id"])
        resp = client.delete(
            f"/budgets/{budget['id']}/items/99999",
            headers=_admin_h(client, test_admin),
        )
        assert resp.status_code == 404

    def test_student_cannot_add_item(self, client: TestClient, test_admin, test_user):
        club = _make_club(client, test_admin, "Student Item Club")
        budget = _create_budget(client, test_admin, club_id=club["id"])
        resp = client.post(
            f"/budgets/{budget['id']}/items",
            json={"category": "food", "description": "Sneaky", "amount": 100.0},
            headers=_auth(client, test_user),
        )
        assert resp.status_code == 403
