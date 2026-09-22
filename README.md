# 💰 Spend Tracker

A full-stack expense tracking application with a **FastAPI** backend, **SQLite** database, and a lightweight **HTML/CSS/JS** frontend. Includes API key authentication, real-time spend summaries, and intelligent spending insights.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
  - [Quick Start Walkthrough](#quick-start-walkthrough)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [POST /auth/generate-key](#post-authgenerate-key)
  - [POST /expenses](#post-expenses)
  - [GET /expenses](#get-expenses)
  - [GET /summary](#get-summary)
  - [GET /insights](#get-insights)
- [Input Validation Rules](#input-validation-rules)
- [Error Handling](#error-handling)
- [Frontend Overview](#frontend-overview)
- [Application Flow](#application-flow)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Test Coverage](#test-coverage)
- [Key Design Decisions](#key-design-decisions)
- [What I'd Do Differently With More Time](#what-id-do-differently-with-more-time)
- [Lambda Deployment Notes](#lambda-deployment-notes)

---

## Features

| Feature | Description |
|---------|-------------|
| **Expense CRUD** | Create and list expenses with amount, category, note, and date |
| **Smart Filtering** | Filter expenses by category and/or date range |
| **Spending Summary** | Total spend, category breakdown, and month-over-month trends |
| **Spend Insights** | Automatically flags categories with >20% month-over-month increase |
| **API Key Auth** | Generate and manage API keys; all protected endpoints require `X-API-Key` |
| **Input Validation** | Pydantic-powered validation with clear, structured error messages |
| **Automated Tests** | 31 tests covering happy paths, validation errors, auth, and edge cases |

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | 0.115.0 | Web framework — async-ready, auto-generates OpenAPI docs |
| **SQLAlchemy** | 2.0.35 | ORM — declarative models, database abstraction |
| **Pydantic** | 2.9.2 | Request/response validation and serialization |
| **SQLite** | Built-in | Lightweight relational database (file-based, zero config) |
| **Uvicorn** | 0.30.6 | ASGI server for running FastAPI |
| **Pytest** | 8.3.3 | Test framework |
| **HTTPX** | 0.27.2 | Async HTTP client (used by FastAPI's test client) |

### Frontend

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic page structure |
| **CSS3** | Dark theme with design tokens, gradients, and micro-animations |
| **Vanilla JavaScript** | API communication, DOM rendering, form handling |
| **Google Fonts (Inter)** | Modern typography |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Port 3000)                  │
│                                                         │
│   index.html ─── styles.css ─── app.js                  │
│       │                           │                     │
│       └─── User Interface ────────┘                     │
│                    │                                    │
│              HTTP REST calls                            │
│           (X-API-Key header)                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (Port 8000)                     │
│                                                         │
│   ┌─────────┐    ┌──────────┐    ┌──────────────┐       │
│   │  CORS   │───▶│  Routes  │───▶│  Auth Layer  │       │
│   │Middleware│    │ (main.py)│    │  (auth.py)   │       │
│   └─────────┘    └────┬─────┘    └──────┬───────┘       │
│                       │                 │               │
│              ┌────────┴────────┐        │               │
│              ▼                 ▼        ▼               │
│   ┌──────────────┐   ┌─────────────────────────┐       │
│   │   Schemas    │   │    SQLAlchemy ORM        │       │
│   │ (Pydantic)   │   │    (models.py)           │       │
│   │ (schemas.py) │   │         │                │       │
│   └──────────────┘   │    ┌────┴─────┐          │       │
│                      │    │ database │          │       │
│   ┌──────────────┐   │    │  .py     │          │       │
│   │  Insights    │   │    └────┬─────┘          │       │
│   │ (insights.py)│   └────────┼─────────────────┘       │
│   └──────────────┘            │                         │
│                               ▼                         │
│                    ┌─────────────────┐                  │
│                    │  SQLite DB      │                  │
│                    │ spend_tracker.db│                  │
│                    └─────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Request Flow

1. **User** interacts with the frontend (fills form, clicks button)
2. **Frontend JS** sends HTTP request with `X-API-Key` header to the backend
3. **CORS Middleware** validates the origin
4. **Auth Dependency** checks the API key against the `api_keys` table
5. **Pydantic Schema** validates and parses the request body/params
6. **Route Handler** executes business logic via SQLAlchemy ORM
7. **Response** is serialized back through Pydantic and returned as JSON

---

## Project Structure

```
Spend tracker/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Package init
│   │   ├── main.py              # FastAPI app — all routes, CORS config, startup
│   │   ├── database.py          # SQLAlchemy engine, session factory, get_db dependency
│   │   ├── models.py            # ORM models: Expense, ApiKey
│   │   ├── schemas.py           # Pydantic schemas for validation & serialization
│   │   ├── auth.py              # API key validation dependency
│   │   └── insights.py          # Spend insight engine (MoM comparison)
│   │
│   ├── tests/
│   │   ├── __init__.py          # Package init
│   │   ├── conftest.py          # Shared fixtures: in-memory DB, test client, auth
│   │   ├── test_expenses.py     # 15 tests — CRUD, validation, auth, filtering
│   │   ├── test_summary.py      # 6 tests — aggregation, MoM, edge cases
│   │   └── test_insights.py     # 10 tests — threshold detection, boundaries
│   │
│   └── requirements.txt         # Pinned Python dependencies
│
├── frontend/
│   ├── index.html               # Single-page app structure
│   ├── styles.css               # Dark theme, design tokens, micro-animations
│   └── app.js                   # API client, DOM rendering, state management
│
└── README.md                    # This file
```

### Module Responsibilities

| Module | What It Does |
|--------|-------------|
| `main.py` | Defines all API routes, configures CORS, wires up dependencies, runs table creation on startup |
| `database.py` | Creates the SQLAlchemy engine pointing to `spend_tracker.db`, provides the `get_db` session dependency that FastAPI injects into route handlers |
| `models.py` | Defines the `Expense` and `ApiKey` ORM models with column types, constraints, and indexes |
| `schemas.py` | Pydantic models that validate incoming requests (positive amounts, non-empty categories, valid dates) and shape outgoing responses |
| `auth.py` | A FastAPI dependency that reads the `X-API-Key` header, looks it up in the database, and rejects unauthorized requests with 401 |
| `insights.py` | Compares per-category spending between the current and previous month; flags any category with >20% increase |

---

## Getting Started

### Prerequisites

- **Python 3.11** or higher
- **pip** (Python package manager)
- A modern web browser (Chrome, Firefox, Edge, Safari)

### Installation

```bash
# 1. Clone or navigate to the project
cd "d:\Projects\Spend tracker"

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt
```

**Dependencies installed:**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pytest==8.3.3
httpx==0.27.2
```

### Running the Application

You need **two terminals** — one for the backend API, one for the frontend.

#### Terminal 1 — Backend API Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- The API is now live at **http://localhost:8000**
- Interactive Swagger docs at **http://localhost:8000/docs**
- ReDoc docs at **http://localhost:8000/redoc**
- The `--reload` flag enables hot-reload on code changes
- On first run, the SQLite database file (`spend_tracker.db`) is created automatically

#### Terminal 2 — Frontend Static Server

```bash
cd frontend
python -m http.server 3000
```

- The frontend UI is now live at **http://localhost:3000**

### Quick Start Walkthrough

1. **Open** http://localhost:3000 in your browser
2. **Generate an API key**: Click the **"+ New Key"** button in the header → enter a name (e.g. "My Key") → click **Generate**
3. The API key auto-fills in the header input and is saved to `localStorage`
4. **Add an expense**: Fill in amount, category, optional note, and date → click **Add Expense**
5. The **Expense List**, **Summary Cards**, **Category Breakdown**, and **Insights** all update automatically
6. **Filter expenses**: Use the category dropdown and date range inputs above the expense list → click **Filter**

---

## Database Schema

The application uses SQLite with two tables, created automatically on first startup.

### `expenses` Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `amount` | FLOAT | NOT NULL | Expense amount (positive) |
| `category` | VARCHAR(100) | NOT NULL, INDEXED | Expense category |
| `note` | VARCHAR(500) | NULLABLE | Optional description |
| `date` | DATE | NOT NULL, INDEXED | When the expense occurred |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | When the record was created |

### `api_keys` Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `key` | VARCHAR(64) | UNIQUE, NOT NULL, INDEXED | The API key string |
| `name` | VARCHAR(100) | NOT NULL | Human-readable label |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Can be deactivated |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | When the key was created |

**Indexes** are placed on `category`, `date`, and `key` columns since they are used in every filter, aggregation, and auth query.

---

## API Reference

### Authentication

All endpoints except `POST /auth/generate-key` require an `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

Missing or invalid keys return `401 Unauthorized`.

---

### POST /auth/generate-key

Generate a new API key. **No authentication required.**

**Request:**
```bash
curl -X POST http://localhost:8000/auth/generate-key \
  -H "Content-Type: application/json" \
  -d '{"name": "My Laptop"}'
```

**Response (201 Created):**
```json
{
  "key": "abc123...xyz",
  "name": "My Laptop",
  "created_at": "2026-09-22T10:00:00"
}
```

> ⚠️ The raw API key is returned **only once**. Save it immediately.

---

### POST /expenses

Create a new expense. **Requires authentication.**

**Request:**
```bash
curl -X POST http://localhost:8000/expenses \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "amount": 42.50,
    "category": "Food",
    "note": "Lunch at café",
    "date": "2026-09-15"
  }'
```

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `amount` | float | ✅ | Must be > 0 |
| `category` | string | ✅ | 1–100 characters, non-empty |
| `note` | string | ❌ | Max 500 characters |
| `date` | string | ✅ | ISO format: `YYYY-MM-DD` |

**Response (201 Created):**
```json
{
  "id": 1,
  "amount": 42.5,
  "category": "Food",
  "note": "Lunch at café",
  "date": "2026-09-15",
  "created_at": "2026-09-22T10:05:00"
}
```

---

### GET /expenses

List all expenses with optional filters. **Requires authentication.**

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | ❌ | Filter by exact category name |
| `start_date` | string | ❌ | Start of date range (inclusive), `YYYY-MM-DD` |
| `end_date` | string | ❌ | End of date range (inclusive), `YYYY-MM-DD` |

**Examples:**

```bash
# All expenses
curl -H "X-API-Key: your-key" http://localhost:8000/expenses

# Filter by category
curl -H "X-API-Key: your-key" "http://localhost:8000/expenses?category=Food"

# Filter by date range
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/expenses?start_date=2026-09-01&end_date=2026-09-30"

# Combined filters
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/expenses?category=Food&start_date=2026-09-01&end_date=2026-09-30"
```

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "amount": 100.0,
    "category": "Food",
    "note": "Groceries",
    "date": "2026-09-20",
    "created_at": "2026-09-20T14:30:00"
  },
  {
    "id": 1,
    "amount": 42.5,
    "category": "Food",
    "note": "Lunch at café",
    "date": "2026-09-15",
    "created_at": "2026-09-15T12:00:00"
  }
]
```

Results are sorted by **date descending** (newest first).

---

### GET /summary

Aggregated spending summary across all expenses. **Requires authentication.**

**Request:**
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/summary
```

**Response (200 OK):**
```json
{
  "total_spend": 2475.0,
  "by_category": [
    { "category": "Rent", "total": 2000.0 },
    { "category": "Food", "total": 350.0 },
    { "category": "Transport", "total": 125.0 }
  ],
  "month_over_month": [
    {
      "month": "2026-08",
      "total": 1250.0,
      "previous_total": 0.0,
      "change_amount": 1250.0,
      "change_percent": null
    },
    {
      "month": "2026-09",
      "total": 1225.0,
      "previous_total": 1250.0,
      "change_amount": -25.0,
      "change_percent": -2.0
    }
  ]
}
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `total_spend` | Sum of all expense amounts |
| `by_category` | Per-category totals, sorted by total descending |
| `month_over_month` | Monthly totals with change vs. previous month |
| `change_percent` | Percentage change; `null` when there's no prior month |

---

### GET /insights

Flags categories where spending increased >20% versus the previous month. **Requires authentication.**

**Request:**
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/insights
```

**Response (200 OK):**
```json
{
  "flagged_categories": [
    {
      "category": "Food",
      "current_month": "2026-09",
      "previous_month": "2026-08",
      "current_spend": 450.0,
      "previous_spend": 200.0,
      "increase_percent": 125.0
    }
  ],
  "threshold_percent": 20.0
}
```

**How it works:**
1. Sums expenses per category for the **current month** and the **previous month**
2. Calculates the percentage change: `((current - previous) / previous) × 100`
3. Flags any category where the increase exceeds **20%**
4. Categories with **no prior month data** or **decreased spending** are NOT flagged

---

## Input Validation Rules

The API validates all inputs using Pydantic schemas. Invalid requests return `422 Unprocessable Entity` with detailed error messages.

| Field | Rule | Example Error |
|-------|------|---------------|
| `amount` | Must be > 0 | `{"amount": -5}` → "Input should be greater than 0" |
| `amount` | Must be a number | `{"amount": "abc"}` → "Input should be a valid number" |
| `category` | Required, 1–100 chars | `{"category": ""}` → "String should have at least 1 character" |
| `note` | Optional, max 500 chars | (500+ chars) → "String should have at most 500 characters" |
| `date` | Required, ISO format | `{"date": "15/09/2026"}` → "Input should be a valid date" |
| `start_date` > `end_date` | Logical check | → `400: "start_date must be on or before end_date"` |

---

## Error Handling

The API returns consistent error responses:

| Status Code | Meaning | When It Happens |
|-------------|---------|-----------------|
| `201 Created` | Success | Expense or API key created |
| `200 OK` | Success | List, summary, or insights returned |
| `400 Bad Request` | Invalid logic | `start_date` after `end_date` |
| `401 Unauthorized` | Auth failed | Missing, invalid, or deactivated API key |
| `422 Unprocessable Entity` | Validation failed | Bad field values (negative amount, empty category, bad date) |

**Error Response Shape:**
```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), FastAPI returns a more detailed structure:
```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "input": -5,
      "ctx": {"gt": 0}
    }
  ]
}
```

---

## Frontend Overview

The frontend is a **single-page application** built with vanilla HTML, CSS, and JavaScript — no frameworks, no build step.

### UI Sections

| Section | Description |
|---------|-------------|
| **Header** | Logo, API key input (persisted in localStorage), key visibility toggle, "New Key" button |
| **Add Expense Form** | Amount, category dropdown (9 preset categories), optional note, date picker (defaults to today) |
| **Summary Cards** | Three metric cards: Total Spend, Number of Categories, This Month's Spend |
| **Category Breakdown** | Horizontal bar chart showing per-category totals (proportional to the highest) |
| **Month-over-Month Table** | Tabular view of monthly totals with color-coded percentage changes |
| **Expense List** | Scrollable list of expenses with category tags, notes, dates, and amounts |
| **Filter Bar** | Category dropdown + date range inputs to filter the expense list |
| **Insights Panel** | Warning cards for categories with >20% spending increase |
| **Key Generation Modal** | Modal dialog to generate a new API key with copy-to-clipboard |

### Frontend ↔ Backend Communication

- All API calls go through the `apiFetch()` wrapper in `app.js`
- The wrapper automatically injects the `X-API-Key` header from the input field
- API key is persisted in `localStorage` across sessions
- After adding an expense, all three views (expenses, summary, insights) refresh in parallel via `Promise.all()`

### Design

- **Dark theme** with HSL-based color palette
- **Card-based layout** with subtle border glow on hover
- **Category color system** — each category has a unique, consistent color
- **Micro-animations** — slide-down status banner, fade-in expense items, scale-in modal
- **Responsive** — two-column grid collapses to single column on mobile (< 900px)

---

## Application Flow

### End-to-End: Adding an Expense

```
User fills form → clicks "Add Expense"
        │
        ▼
app.js: handleAddExpense()
        │
        ├── Client-side validation (amount > 0, category selected, date present)
        │
        ▼
apiFetch("POST /expenses", { amount, category, note, date })
        │
        ├── Adds X-API-Key header from input field
        │
        ▼
FastAPI: create_expense()
        │
        ├── auth.py: require_api_key() → validates X-API-Key against DB
        ├── schemas.py: ExpenseCreate → Pydantic validates the body
        ├── models.py: Expense() → creates ORM instance
        ├── database.py: db.add() → inserts into SQLite
        │
        ▼
Returns ExpenseResponse (201 Created)
        │
        ▼
app.js: refreshes expenses + summary + insights
        │
        ▼
UI updates: new expense in list, summary cards recalculated,
            insights re-evaluated for 20% threshold alerts
```

### End-to-End: Viewing the Summary

```
Page loads (or after adding expense)
        │
        ▼
app.js: loadSummary() → GET /summary
        │
        ▼
FastAPI: get_summary()
        │
        ├── SELECT COALESCE(SUM(amount), 0) FROM expenses        → total_spend
        ├── SELECT category, SUM(amount) GROUP BY category       → by_category
        ├── SELECT strftime('%Y-%m', date), SUM(amount) GROUP BY → monthly totals
        ├── Loop: calculate change_amount and change_percent      → month_over_month
        │
        ▼
Returns SummaryResponse (200 OK)
        │
        ▼
app.js: renderSummary()
        │
        ├── Updates total spend card
        ├── Updates category count card
        ├── Updates "This Month" card
        ├── Renders category breakdown bars (proportional width)
        └── Renders month-over-month table with color-coded changes
```

### Insight Detection Logic

```
generate_insights(db, reference_date=today)
        │
        ├── Get current month bounds: e.g. 2026-09-01 to 2026-09-30
        ├── Get previous month bounds: e.g. 2026-08-01 to 2026-08-31
        │
        ├── Query: SUM(amount) GROUP BY category WHERE date IN current_month
        ├── Query: SUM(amount) GROUP BY category WHERE date IN previous_month
        │
        ├── For each category in UNION of both months:
        │   ├── Skip if previous_spend = 0 (no baseline to compare)
        │   ├── increase_pct = ((current - previous) / previous) × 100
        │   └── If increase_pct > 20% → ADD to flagged_categories
        │
        ▼
Returns InsightsResponse { flagged_categories, threshold_percent: 20.0 }
```

---

## Testing

### Running Tests

```bash
cd backend
pytest tests/ -v
```

Tests use an **in-memory SQLite database** with `StaticPool` — no file I/O, no cleanup needed.

### Test Coverage

**31 tests total — all passing**

#### Expense Tests (`test_expenses.py` — 15 tests)

| Test | Type | What It Verifies |
|------|------|------------------|
| `test_create_expense_success` | Happy path | Valid expense returns 201 with all fields |
| `test_create_expense_without_note` | Happy path | Optional note can be omitted |
| `test_negative_amount_rejected` | Validation | Negative amounts → 422 |
| `test_zero_amount_rejected` | Validation | Zero amount → 422 (must be > 0) |
| `test_missing_category_rejected` | Validation | Missing required field → 422 |
| `test_empty_category_rejected` | Validation | Empty string → 422 (min_length=1) |
| `test_missing_amount_rejected` | Validation | Missing required field → 422 |
| `test_invalid_date_format_rejected` | Validation | Non-ISO date → 422 |
| `test_missing_api_key_returns_401` | Auth | No header → 401 "Missing" |
| `test_invalid_api_key_returns_401` | Auth | Bogus key → 401 "Invalid" |
| `test_list_empty` | Happy path | Empty DB → empty list (not error) |
| `test_list_all` | Happy path | Returns all seeded expenses |
| `test_filter_by_category` | Filtering | Only matching category returned |
| `test_filter_by_date_range` | Filtering | Only expenses in range returned |
| `test_invalid_date_range_returns_400` | Validation | start > end → 400 |

#### Summary Tests (`test_summary.py` — 6 tests)

| Test | Type | What It Verifies |
|------|------|------------------|
| `test_summary_empty_database` | Edge case | Returns zeros, not errors |
| `test_summary_total_spend` | Aggregation | Total = sum of all expenses |
| `test_summary_by_category` | Aggregation | Category totals match |
| `test_summary_by_category_order` | Ordering | Sorted by total descending |
| `test_summary_month_over_month` | Calculation | Change amounts and percentages correct |
| `test_summary_requires_auth` | Auth | 401 without API key |

#### Insight Tests (`test_insights.py` — 10 tests)

| Test | Type | What It Verifies |
|------|------|------------------|
| `test_no_data_returns_empty` | Edge case | No expenses → no insights |
| `test_no_prior_month_not_flagged` | Edge case | New category NOT flagged |
| `test_stable_spend_not_flagged` | Logic | ≤20% increase → no flag |
| `test_exactly_20_percent_not_flagged` | Boundary | Exactly 20% → no flag (threshold is >20%) |
| `test_over_20_percent_increase_flagged` | Logic | >20% increase → flagged with correct data |
| `test_decrease_not_flagged` | Logic | Spending decrease → no flag |
| `test_multiple_categories_mixed` | Integration | Only exceeding categories flagged |
| `test_custom_threshold` | Config | Custom threshold overrides default |
| `test_insights_requires_auth` | Auth | 401 without API key |
| `test_insights_returns_structure` | Schema | Response has correct shape |

---

## Key Design Decisions

### Why FastAPI?
FastAPI provides automatic request validation (via Pydantic), auto-generated interactive API docs (Swagger UI + ReDoc), and native async support — all with minimal boilerplate. The dependency injection system (`Depends()`) keeps auth and database access clean and testable.

### Why SQLAlchemy ORM (not raw SQL)?
The ORM provides a self-documenting schema via model classes, type safety, and database portability. Swapping SQLite for PostgreSQL requires only changing the `DATABASE_URL` — no query rewrites needed.

### Why Pydantic for Validation?
Pydantic gives us:
- **Type coercion** — strings auto-converted to dates, numbers
- **Constraint enforcement** — `gt=0`, `min_length=1`, `max_length=500`
- **Error messages** — structured, machine-readable validation errors
- **Serialization** — ORM objects automatically converted to JSON via `from_attributes=True`

### Why API Key Auth (not JWT)?
For a lightweight expense tracker, API keys are simpler to implement and easier to demo. The `X-API-Key` header is checked against the database on every request. Keys can be deactivated by setting `is_active=False` without needing token revocation infrastructure.

### Why Separate `insights.py`?
The insight logic is isolated from route handlers for two reasons:
1. **Testability** — The `generate_insights()` function accepts an injectable `reference_date`, making it possible to write deterministic tests without mocking `date.today()`
2. **Reusability** — The same function could be used for scheduled email alerts, background jobs, etc.

### Why Database Indexes?
The `category` and `date` columns on the `expenses` table are indexed because they appear in:
- Every filter query (`WHERE category = ?`, `WHERE date >= ?`)
- Every aggregation query (`GROUP BY category`, `strftime('%Y-%m', date)`)
- The API key `key` column is indexed for fast auth lookups

### Frontend: Why Vanilla JS?
The requirements call for a lightweight UI to confirm end-to-end functionality. Vanilla JS avoids build tooling complexity (no Node.js, no bundler) while still providing a functional, responsive interface. The entire frontend is three files that can be served by any static file server.

---

## What I'd Do Differently With More Time

| Area | Improvement |
|------|-------------|
| **Pagination** | Add cursor-based pagination to `GET /expenses` — currently returns all rows |
| **Edit/Delete** | Add `PUT /expenses/{id}` and `DELETE /expenses/{id}` with ownership checks |
| **Rate Limiting** | Per-key rate limits via `slowapi` to prevent abuse |
| **PostgreSQL** | Replace SQLite for concurrent write safety and richer query support |
| **Key Hashing** | Hash API keys (bcrypt/argon2) instead of storing raw values |
| **Frontend Framework** | Move to React/Vue with proper state management for a growing feature set |
| **CI/CD** | GitHub Actions with linting (`ruff`), type checking (`mypy`), and automated tests |
| **Budgets** | Monthly budget per category with alerts when approaching the limit |
| **Export** | CSV/PDF export of expense data |
| **Multi-user** | Associate expenses with specific API keys for user isolation |

---

## Lambda Deployment Notes

**FastAPI on Lambda** works well via [Mangum](https://github.com/jordanahaines/mangum), an ASGI-to-Lambda adapter:

```python
from mangum import Mangum
from app.main import app

handler = Mangum(app)
```

**However, SQLite on Lambda is problematic:**

| Issue | Why It Matters |
|-------|---------------|
| Ephemeral `/tmp` | Data is lost on cold starts |
| Per-invocation isolation | Concurrent Lambda instances each have their own `/tmp` |
| 10 GB limit | `/tmp` has a maximum of 10 GB |

**Solutions for persistent storage on Lambda:**

1. **AWS EFS** — Mount an Elastic File System to Lambda for shared, persistent SQLite storage
2. **DynamoDB** — Swap to a serverless-native database (no file I/O)
3. **RDS / Aurora** — Use a managed PostgreSQL/MySQL instance

For this project, SQLite is ideal for local development and assessment. For production Lambda deployment, the recommended path is EFS mount or a swap to DynamoDB.
