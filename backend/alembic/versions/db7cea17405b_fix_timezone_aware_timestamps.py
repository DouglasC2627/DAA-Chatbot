"""fix_timezone_aware_timestamps

Revision ID: db7cea17405b
Revises: 67184ec96883
Create Date: 2025-10-19 22:23:13.143133

This migration updates existing datetime values in the database to include
timezone information (UTC). SQLite stores datetimes as strings, so we append
'+00:00' to indicate UTC timezone for all existing timestamps.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db7cea17405b'
down_revision: Union[str, None] = '67184ec96883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add timezone information to existing datetime columns.

    SQLite's datetime('now') function returns UTC time, so existing timestamps
    are already in UTC. We just need to append the '+00:00' timezone suffix
    to make them timezone-aware.
    """
    # Get database connection
    conn = op.get_bind()

    # Tables and their timestamp columns
    tables_to_update = [
        ('projects', ['created_at', 'updated_at']),
        ('documents', ['created_at', 'updated_at']),
        ('chats', ['created_at', 'updated_at']),
        ('messages', ['created_at']),
    ]

    for table_name, columns in tables_to_update:
        for column_name in columns:
            # Check if table and column exist before updating
            try:
                # Add timezone suffix to existing UTC timestamps
                # SQLite format: '2025-10-19 14:10:01' (UTC) -> '2025-10-19 14:10:01+00:00' (UTC with timezone)
                conn.execute(
                    sa.text(f"""
                        UPDATE {table_name}
                        SET {column_name} = {column_name} || '+00:00'
                        WHERE {column_name} IS NOT NULL
                        AND {column_name} NOT LIKE '%+%'
                        AND {column_name} NOT LIKE '%Z'
                    """)
                )
            except Exception as e:
                # Table or column might not exist, continue
                print(f"Warning: Could not update {table_name}.{column_name}: {e}")
                continue


def downgrade() -> None:
    """
    Remove timezone information from datetime columns.

    This simply removes the '+00:00' suffix without any time conversion,
    since the original timestamps were already in UTC.
    """
    # Get database connection
    conn = op.get_bind()

    # Tables and their timestamp columns
    tables_to_update = [
        ('projects', ['created_at', 'updated_at']),
        ('documents', ['created_at', 'updated_at']),
        ('chats', ['created_at', 'updated_at']),
        ('messages', ['created_at']),
    ]

    for table_name, columns in tables_to_update:
        for column_name in columns:
            try:
                # Remove timezone suffix only
                # '2025-10-19 14:10:01+00:00' -> '2025-10-19 14:10:01'
                conn.execute(
                    sa.text(f"""
                        UPDATE {table_name}
                        SET {column_name} = REPLACE({column_name}, '+00:00', '')
                        WHERE {column_name} IS NOT NULL
                        AND {column_name} LIKE '%+00:00'
                    """)
                )
            except Exception as e:
                # Table or column might not exist, continue
                print(f"Warning: Could not downgrade {table_name}.{column_name}: {e}")
                continue
