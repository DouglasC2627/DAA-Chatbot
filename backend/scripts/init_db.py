#!/usr/bin/env python3
"""
Database initialization script.

Usage:
    python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import init_db


async def main():
    """Initialize the database with default data."""
    print("Initializing database...")
    try:
        await init_db()
        print("\n✓ Database initialization complete!")
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
