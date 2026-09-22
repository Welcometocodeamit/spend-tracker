"""
Spend Tracker — FastAPI Application

Routes:
    POST /expenses       — Create an expense
    GET  /expenses       — List expenses (filterable)
    GET  /summary        — Aggregated spending summary
    GET  /insights       — Spend-increase alerts
    POST /auth/generate-key — Generate a new API key
"""

import secrets
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import create_tables, get_db
from app.models import Expense, ApiKey
from app.auth import require_api_key
from app.insights import generate_insights
from app.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    CategorySpend,
    ErrorResponse,
    ExpenseCreate,
    ExpenseResponse,
    InsightsResponse,
    MonthOverMonthChange,
    SummaryResponse,
)

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Spend Tracker API",
    version="1.0.0",
    description="Track expenses, view summaries, and get spend insights.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables on first launch."""
    create_tables()


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post(
    "/auth/generate-key",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Generate a new API key",
)
def generate_api_key(body: ApiKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key. The raw key is returned once and cannot be retrieved later."""
    raw_key = secrets.token_urlsafe(32)
    db_key = ApiKey(key=raw_key, name=body.name)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


# ── Expenses ─────────────────────────────────────────────────────────────────

@app.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["expenses"],
    summary="Create an expense",
    responses={401: {"model": ErrorResponse}},
)
def create_expense(
    body: ExpenseCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
):
    """Add a new expense record."""
    expense = Expense(
        amount=body.amount,
        category=body.category.strip(),
        note=body.note.strip() if body.note else None,
        date=body.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get(
    "/expenses",
    response_model=list[ExpenseResponse],
    tags=["expenses"],
    summary="List expenses",
    responses={401: {"model": ErrorResponse}},
)
def list_expenses(
    category: str | None = Query(None, description="Filter by category"),
    start_date: date | None = Query(None, description="Start of date range (inclusive)"),
    end_date: date | None = Query(None, description="End of date range (inclusive)"),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
):
    """
    Return all expenses, optionally filtered by category and/or date range.
    Results are ordered by date descending.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )

    query = db.query(Expense)

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    return query.order_by(Expense.date.desc(), Expense.id.desc()).all()


# ── Summary ──────────────────────────────────────────────────────────────────

@app.get(
    "/summary",
    response_model=SummaryResponse,
    tags=["summary"],
    summary="Spending summary",
    responses={401: {"model": ErrorResponse}},
)
def get_summary(
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
):
    """
    Returns:
    - Total spend across all expenses
    - Spend broken down by category
    - Month-over-month spend with change amounts and percentages
    """
    # Total spend
    total = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar()
    total_spend = float(total)

    # By category
    cat_rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    by_category = [
        CategorySpend(category=cat, total=round(float(amt), 2))
        for cat, amt in cat_rows
    ]

    # Monthly totals (use strftime for SQLite compatibility)
    month_rows = (
        db.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.sum(Expense.amount),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    # Compute month-over-month changes
    month_over_month: list[MonthOverMonthChange] = []
    for i, (month_str, total_amt) in enumerate(month_rows):
        current = round(float(total_amt), 2)
        if i == 0:
            prev = 0.0
        else:
            prev = round(float(month_rows[i - 1][1]), 2)

        change = round(current - prev, 2)
        change_pct = round((change / prev) * 100, 1) if prev > 0 else None

        month_over_month.append(
            MonthOverMonthChange(
                month=month_str,
                total=current,
                previous_total=prev,
                change_amount=change,
                change_percent=change_pct,
            )
        )

    return SummaryResponse(
        total_spend=round(total_spend, 2),
        by_category=by_category,
        month_over_month=month_over_month,
    )


# ── Insights ─────────────────────────────────────────────────────────────────

@app.get(
    "/insights",
    response_model=InsightsResponse,
    tags=["insights"],
    summary="Spend insights",
    responses={401: {"model": ErrorResponse}},
)
def get_insights(
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
):
    """Flag categories where spending increased >20% vs. the previous month."""
    return generate_insights(db)
