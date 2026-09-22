"""
Tests for the /summary endpoint — aggregation correctness.
"""


class TestSummary:
    """GET /summary"""

    def _seed(self, client, auth_headers):
        """Seed expenses across two months and multiple categories."""
        expenses = [
            # August
            {"amount": 200, "category": "Food", "date": "2026-08-05"},
            {"amount": 50, "category": "Transport", "date": "2026-08-10"},
            {"amount": 1000, "category": "Rent", "date": "2026-08-01"},
            # September
            {"amount": 150, "category": "Food", "date": "2026-09-05"},
            {"amount": 75, "category": "Transport", "date": "2026-09-12"},
            {"amount": 1000, "category": "Rent", "date": "2026-09-01"},
        ]
        for e in expenses:
            client.post("/expenses", json=e, headers=auth_headers)

    def test_summary_empty_database(self, client, auth_headers):
        """Summary with no expenses returns zero totals."""
        resp = client.get("/summary", headers=auth_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_spend"] == 0.0
        assert data["by_category"] == []
        assert data["month_over_month"] == []

    def test_summary_total_spend(self, client, auth_headers):
        """Total spend should equal the sum of all expenses."""
        self._seed(client, auth_headers)
        resp = client.get("/summary", headers=auth_headers)
        data = resp.json()

        expected_total = 200 + 50 + 1000 + 150 + 75 + 1000
        assert data["total_spend"] == expected_total

    def test_summary_by_category(self, client, auth_headers):
        """Category breakdown should match summed amounts."""
        self._seed(client, auth_headers)
        resp = client.get("/summary", headers=auth_headers)
        data = resp.json()

        cat_map = {c["category"]: c["total"] for c in data["by_category"]}
        assert cat_map["Rent"] == 2000.0
        assert cat_map["Food"] == 350.0
        assert cat_map["Transport"] == 125.0

    def test_summary_by_category_order(self, client, auth_headers):
        """Categories should be ordered by total spend descending."""
        self._seed(client, auth_headers)
        resp = client.get("/summary", headers=auth_headers)
        data = resp.json()

        totals = [c["total"] for c in data["by_category"]]
        assert totals == sorted(totals, reverse=True)

    def test_summary_month_over_month(self, client, auth_headers):
        """Month-over-month data should have correct change calculations."""
        self._seed(client, auth_headers)
        resp = client.get("/summary", headers=auth_headers)
        data = resp.json()

        mom = data["month_over_month"]
        assert len(mom) == 2

        aug = mom[0]
        assert aug["month"] == "2026-08"
        assert aug["total"] == 1250.0
        assert aug["previous_total"] == 0.0
        assert aug["change_percent"] is None  # No prior month

        sep = mom[1]
        assert sep["month"] == "2026-09"
        assert sep["total"] == 1225.0
        assert sep["previous_total"] == 1250.0
        assert sep["change_amount"] == -25.0
        assert sep["change_percent"] == -2.0

    def test_summary_requires_auth(self, client):
        """Summary endpoint requires authentication."""
        resp = client.get("/summary")
        assert resp.status_code == 401
