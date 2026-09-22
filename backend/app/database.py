"""
Database configuration — SQLAlchemy engine, session factory, and table creation.

Uses SQLite for simplicity. The database file lives alongside the backend code.
For production / Lambda deployment, swap the URL to point at RDS/DynamoDB or
mount an EFS volume.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./spend_tracker.db",
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def create_tables() -> None:
    """Create all tables defined by ORM models (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
