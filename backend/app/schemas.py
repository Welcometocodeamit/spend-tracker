"""
Pydantic schemas for request validation and response serialization.
"""

import datetime as _dt
from pydantic import BaseModel, Field, ConfigDict


# ── Expense Schemas ──────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    """Validated input for creating an expense."""

    amount: float = Field(..., gt=0, description="Must be a positive number")
    category: str = Field(
        ..., min_length=1, max_length=100, description="Expense category"
    )
    note: str | None = Field(
        None, max_length=500, description="Optional note about the expense"
    )
    date: _dt.date = Field(..., description="Date the expense occurred (YYYY-MM-DD)")


class ExpenseResponse(BaseModel):
    """Full expense record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    category: str
    note: str | None
    date: _dt.date
    created_at: _dt.datetime


# ── Summary Schemas ──────────────────────────────────────────────────────────

class CategorySpend(BaseModel):
    """Spend total for a single category."""

    category: str
    total: float


class MonthlySpend(BaseModel):
    """Spend total for a single month."""

    month: str  # "YYYY-MM"
    total: float


class MonthOverMonthChange(BaseModel):
    """Month-over-month change between two consecutive months."""

    month: str  # "YYYY-MM"
    total: float
    previous_total: float
    change_amount: float
    change_percent: float | None  # None when previous_total is 0


class SummaryResponse(BaseModel):
    """Aggregated spending summary."""

    total_spend: float
    by_category: list[CategorySpend]
    month_over_month: list[MonthOverMonthChange]


# ── Insight Schemas ──────────────────────────────────────────────────────────

class CategoryInsight(BaseModel):
    """A flagged category where spend increased significantly."""

    category: str
    current_month: str
    previous_month: str
    current_spend: float
    previous_spend: float
    increase_percent: float


class InsightsResponse(BaseModel):
    """Collection of spend insights / alerts."""

    flagged_categories: list[CategoryInsight]
    threshold_percent: float = 20.0


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    """Input for generating a new API key."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Label for this API key"
    )


class ApiKeyResponse(BaseModel):
    """Newly generated API key (shown once)."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    name: str
    created_at: _dt.datetime


# ── Generic ──────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
