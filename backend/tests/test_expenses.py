"""
Tests for expense CRUD operations — happy paths AND error cases.
"""

import pytest


# ── Happy Path ───────────────────────────────────────────────────────────────

class TestCreateExpense:
    """POST /expenses"""

    def test_create_expense_success(self, client, auth_headers):
        """Creating an expense with valid data returns 201."""
        payload = {
            "amount": 42.50,
            "category": "Food",
            "note": "Lunch at café",
            "date": "2026-09-15",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        data = resp.json()
        assert data["amount"] == 42.50
        assert data["category"] == "Food"
        assert data["note"] == "Lunch at café"
        assert data["date"] == "2026-09-15"
        assert "id" in data
        assert "created_at" in data

    def test_create_expense_without_note(self, client, auth_headers):
        """Note is optional — omitting it should succeed."""
        payload = {
            "amount": 10.0,
            "category": "Transport",
            "date": "2026-09-10",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note"] is None


# ── Validation Errors ────────────────────────────────────────────────────────

class TestCreateExpenseValidation:
    """POST /expenses — input validation error cases."""

    def test_negative_amount_rejected(self, client, auth_headers):
        """Negative amounts should fail validation."""
        payload = {
            "amount": -5.0,
            "category": "Food",
            "date": "2026-09-15",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_zero_amount_rejected(self, client, auth_headers):
        """Zero amounts should fail validation (amount must be > 0)."""
        payload = {
            "amount": 0,
            "category": "Food",
            "date": "2026-09-15",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_category_rejected(self, client, auth_headers):
        """Missing required field 'category' returns 422."""
        payload = {"amount": 10.0, "date": "2026-09-15"}
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_empty_category_rejected(self, client, auth_headers):
        """Empty string category fails min_length validation."""
        payload = {
            "amount": 10.0,
            "category": "",
            "date": "2026-09-15",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_amount_rejected(self, client, auth_headers):
        """Missing required field 'amount' returns 422."""
        payload = {"category": "Food", "date": "2026-09-15"}
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_invalid_date_format_rejected(self, client, auth_headers):
        """Non-ISO date formats should be rejected."""
        payload = {
            "amount": 10.0,
            "category": "Food",
            "date": "15/09/2026",
        }
        resp = client.post("/expenses", json=payload, headers=auth_headers)
        assert resp.status_code == 422


# ── Auth Errors ──────────────────────────────────────────────────────────────

class TestCreateExpenseAuth:
    """POST /expenses — authentication error cases."""

    def test_missing_api_key_returns_401(self, client):
        """Request without X-API-Key header should be rejected."""
        payload = {
            "amount": 10.0,
            "category": "Food",
            "date": "2026-09-15",
        }
        resp = client.post("/expenses", json=payload)
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    def test_invalid_api_key_returns_401(self, client):
        """Request with a bogus API key should be rejected."""
        payload = {
            "amount": 10.0,
            "category": "Food",
            "date": "2026-09-15",
        }
        resp = client.post(
            "/expenses", json=payload, headers={"X-API-Key": "bogus-key"}
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]


# ── List / Filter ────────────────────────────────────────────────────────────

class TestListExpenses:
    """GET /expenses"""

    def _seed(self, client, auth_headers):
        """Seed a few expenses for filter tests."""
        expenses = [
            {"amount": 50, "category": "Food", "date": "2026-08-01"},
            {"amount": 30, "category": "Transport", "date": "2026-08-15"},
            {"amount": 25, "category": "Food", "date": "2026-09-01"},
            {"amount": 100, "category": "Rent", "date": "2026-09-10"},
        ]
        for e in expenses:
            client.post("/expenses", json=e, headers=auth_headers)

    def test_list_empty(self, client, auth_headers):
        """Empty database returns an empty list, not an error."""
        resp = client.get("/expenses", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_all(self, client, auth_headers):
        """Returns all seeded expenses."""
        self._seed(client, auth_headers)
        resp = client.get("/expenses", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_filter_by_category(self, client, auth_headers):
        """Filtering by category returns only matching expenses."""
        self._seed(client, auth_headers)
        resp = client.get(
            "/expenses", params={"category": "Food"}, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(e["category"] == "Food" for e in data)

    def test_filter_by_date_range(self, client, auth_headers):
        """Filtering by date range returns only expenses in that window."""
        self._seed(client, auth_headers)
        resp = client.get(
            "/expenses",
            params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_invalid_date_range_returns_400(self, client, auth_headers):
        """start_date after end_date should return 400."""
        resp = client.get(
            "/expenses",
            params={"start_date": "2026-09-30", "end_date": "2026-09-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "start_date" in resp.json()["detail"]
