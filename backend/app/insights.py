"""
Spend insights engine.

Compares current month vs. previous month spending per category and flags
any category where spend increased by more than the configured threshold.
"""

from datetime import date, timedelta
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models import Expense
from app.schemas import CategoryInsight, InsightsResponse


THRESHOLD_PERCENT = 20.0


def _get_month_bounds(ref_date: date) -> tuple[date, date]:
    """Return (first_day, last_day) of the month containing ref_date."""
    first_day = ref_date.replace(day=1)
    # Last day: go to next month's 1st, subtract a day
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1)
    last_day = next_month - timedelta(days=1)
    return first_day, last_day


def _get_previous_month(ref_date: date) -> date:
    """Return a date in the previous month relative to ref_date."""
    first_of_current = ref_date.replace(day=1)
    return first_of_current - timedelta(days=1)


def _category_totals(
    db: Session, start: date, end: date
) -> dict[str, float]:
    """Sum expense amounts grouped by category within a date range."""
    rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.date >= start, Expense.date <= end)
        .group_by(Expense.category)
        .all()
    )
    return {category: float(total) for category, total in rows}


def generate_insights(
    db: Session,
    reference_date: date | None = None,
    threshold: float = THRESHOLD_PERCENT,
) -> InsightsResponse:
    """
    Compare spending in the current month vs. the previous month.

    Flags categories where spend increased by more than `threshold` percent.
    If `reference_date` is not given, uses today's date.
    """
    ref = reference_date or date.today()

    current_start, current_end = _get_month_bounds(ref)
    prev_date = _get_previous_month(ref)
    prev_start, prev_end = _get_month_bounds(prev_date)

    current_totals = _category_totals(db, current_start, current_end)
    previous_totals = _category_totals(db, prev_start, prev_end)

    # Merge all categories seen in either month
    all_categories = set(current_totals.keys()) | set(previous_totals.keys())

    flagged: list[CategoryInsight] = []
    for category in sorted(all_categories):
        current = current_totals.get(category, 0.0)
        previous = previous_totals.get(category, 0.0)

        # Only flag increases; skip if there was no prior spend
        if previous <= 0:
            continue

        increase_pct = ((current - previous) / previous) * 100
        if increase_pct > threshold:
            flagged.append(
                CategoryInsight(
                    category=category,
                    current_month=current_start.strftime("%Y-%m"),
                    previous_month=prev_start.strftime("%Y-%m"),
                    current_spend=round(current, 2),
                    previous_spend=round(previous, 2),
                    increase_percent=round(increase_pct, 1),
                )
            )

    return InsightsResponse(
        flagged_categories=flagged,
        threshold_percent=threshold,
    )
