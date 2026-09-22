"""
Tests for the /insights endpoint and the insights engine.
"""

from datetime import date
from app.models import Expense
from app.insights import generate_insights


class TestInsightsEngine:
    """Direct tests of the generate_insights() function."""

    def _add_expense(self, db, amount, category, expense_date):
        """Helper to insert an expense directly into the DB."""
        e = Expense(amount=amount, category=category, date=expense_date)
        db.add(e)
        db.commit()

    def test_no_data_returns_empty(self, db):
        """No expenses → no insights."""
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

    def test_no_prior_month_not_flagged(self, db):
        """Category with spend only in current month should NOT be flagged."""
        self._add_expense(db, 500, "Food", date(2026, 9, 5))
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

    def test_stable_spend_not_flagged(self, db):
        """Category with ≤20% increase should NOT be flagged."""
        self._add_expense(db, 100, "Food", date(2026, 8, 10))
        self._add_expense(db, 115, "Food", date(2026, 9, 10))  # +15%
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

    def test_exactly_20_percent_not_flagged(self, db):
        """Exactly 20% increase should NOT be flagged (threshold is >20%)."""
        self._add_expense(db, 100, "Food", date(2026, 8, 10))
        self._add_expense(db, 120, "Food", date(2026, 9, 10))  # exactly 20%
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

    def test_over_20_percent_increase_flagged(self, db):
        """Category with >20% increase SHOULD be flagged."""
        self._add_expense(db, 100, "Food", date(2026, 8, 10))
        self._add_expense(db, 150, "Food", date(2026, 9, 10))  # +50%
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert len(result.flagged_categories) == 1

        insight = result.flagged_categories[0]
        assert insight.category == "Food"
        assert insight.current_spend == 150.0
        assert insight.previous_spend == 100.0
        assert insight.increase_percent == 50.0

    def test_decrease_not_flagged(self, db):
        """Category where spend DECREASED should NOT be flagged."""
        self._add_expense(db, 200, "Food", date(2026, 8, 10))
        self._add_expense(db, 100, "Food", date(2026, 9, 10))  # -50%
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

    def test_multiple_categories_mixed(self, db):
        """Only categories exceeding threshold should appear in results."""
        # Food: 100 → 150 (+50%) — should flag
        self._add_expense(db, 100, "Food", date(2026, 8, 5))
        self._add_expense(db, 150, "Food", date(2026, 9, 5))

        # Transport: 80 → 85 (+6.25%) — should NOT flag
        self._add_expense(db, 80, "Transport", date(2026, 8, 10))
        self._add_expense(db, 85, "Transport", date(2026, 9, 10))

        # Rent: 1000 → 1300 (+30%) — should flag
        self._add_expense(db, 1000, "Rent", date(2026, 8, 1))
        self._add_expense(db, 1300, "Rent", date(2026, 9, 1))

        result = generate_insights(db, reference_date=date(2026, 9, 15))
        flagged_names = [c.category for c in result.flagged_categories]
        assert "Food" in flagged_names
        assert "Rent" in flagged_names
        assert "Transport" not in flagged_names

    def test_custom_threshold(self, db):
        """Custom threshold should override the default 20%."""
        self._add_expense(db, 100, "Food", date(2026, 8, 10))
        self._add_expense(db, 112, "Food", date(2026, 9, 10))  # +12%

        # Default 20% — should NOT flag
        result = generate_insights(db, reference_date=date(2026, 9, 15))
        assert result.flagged_categories == []

        # Custom 10% — SHOULD flag
        result = generate_insights(
            db, reference_date=date(2026, 9, 15), threshold=10.0
        )
        assert len(result.flagged_categories) == 1


class TestInsightsEndpoint:
    """GET /insights — integration tests via HTTP."""

    def test_insights_requires_auth(self, client):
        """Insights endpoint requires authentication."""
        resp = client.get("/insights")
        assert resp.status_code == 401

    def test_insights_returns_structure(self, client, auth_headers):
        """Authenticated request returns proper response shape."""
        resp = client.get("/insights", headers=auth_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert "flagged_categories" in data
        assert "threshold_percent" in data
        assert data["threshold_percent"] == 20.0
