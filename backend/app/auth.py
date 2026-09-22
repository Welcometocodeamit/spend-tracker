"""
API key authentication dependency for FastAPI.

Usage:
    @app.get("/protected")
    def protected_route(api_key: str = Depends(require_api_key)):
        ...
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey


def require_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> str:
    """
    Validate the X-API-Key header against the database.

    Returns the API key string on success.
    Raises 401 if the key is missing, invalid, or deactivated.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    db_key = db.query(ApiKey).filter(
        ApiKey.key == x_api_key,
        ApiKey.is_active == True,  # noqa: E712 — SQLAlchemy requires == for filters
    ).first()

    if db_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key",
        )

    return x_api_key
