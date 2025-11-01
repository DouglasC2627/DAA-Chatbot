"""
Base database models and configuration for SQLAlchemy.
"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Provides common functionality and timestamp tracking.
    """
    pass


def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime | None) -> str | None:
    """
    Format datetime to ISO 8601 string with UTC timezone.

    Ensures timezone-aware formatting for consistent frontend parsing.
    If datetime is naive (no timezone), treats it as local time and converts to UTC.

    Args:
        dt: Datetime object to format (can be None)

    Returns:
        ISO 8601 formatted string with 'Z' suffix or None if input is None
    """
    if dt is None:
        return None

    # If datetime is naive (no timezone info), treat as local time
    # SQLite stores timezone-aware datetimes as naive local time
    if dt.tzinfo is None:
        # Assume naive datetime is in local timezone and convert to UTC
        import time
        from datetime import timedelta

        # Get local UTC offset in seconds
        if time.daylight:
            utc_offset = -time.altzone
        else:
            utc_offset = -time.timezone

        # Convert local naive time to UTC
        dt_utc = dt - timedelta(seconds=utc_offset)
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if it's in a different timezone
        dt_utc = dt.astimezone(timezone.utc)

    # Format with 'Z' suffix for UTC (more compatible than +00:00)
    return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    Timestamps are stored as UTC timezone-aware datetime objects.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality via deleted_at column.
    """
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = utc_now()

    @property
    def is_deleted(self) -> bool:
        """Check if this record is soft deleted."""
        return self.deleted_at is not None


def to_dict(obj: Any, exclude: list[str] | None = None) -> dict:
    """
    Convert a SQLAlchemy model instance to a dictionary.

    Args:
        obj: The SQLAlchemy model instance
        exclude: List of column names to exclude from the result

    Returns:
        Dictionary representation of the model
    """
    exclude = exclude or []
    result = {}

    for column in obj.__table__.columns:
        if column.name not in exclude:
            value = getattr(obj, column.name)
            # Convert datetime objects to ISO format strings
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value

    return result
