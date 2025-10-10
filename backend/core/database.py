"""
Database session management and initialization.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from core.config import settings
from models import Base


# Sync engine for migrations and CLI tools
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Async engine for FastAPI
async_database_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
async_engine = create_async_engine(
    async_database_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
)

# Session factories
SessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database session.

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def create_tables():
    """
    Create all database tables (for development/testing).

    Note: In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=sync_engine)
    print("✓ Database tables created successfully")


def drop_tables():
    """
    Drop all database tables (for development/testing).

    Warning: This will delete all data!
    """
    Base.metadata.drop_all(bind=sync_engine)
    print("✓ Database tables dropped successfully")


async def init_db():
    """
    Initialize the database with default data.

    Creates default user settings if they don't exist.
    """
    from models import UserSettings

    async with SessionLocal() as session:
        try:
            # Check if default user settings exist
            from sqlalchemy import select
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == "default_user")
            )
            settings_obj = result.scalar_one_or_none()

            if not settings_obj:
                # Create default settings
                settings_obj = UserSettings(
                    user_id="default_user",
                    default_llm_model=settings.OLLAMA_MODEL,
                    default_embedding_model=settings.EMBEDDING_MODEL,
                    default_chunk_size=1000,
                    default_chunk_overlap=200,
                    default_retrieval_k=5,
                    theme="light"
                )
                session.add(settings_obj)
                await session.commit()
                print("✓ Default user settings created")
            else:
                print("✓ Default user settings already exist")

        except Exception as e:
            await session.rollback()
            print(f"✗ Error initializing database: {e}")
            raise


async def get_db_session() -> AsyncSession:
    """
    Get a new database session (for use outside of FastAPI).

    Returns:
        AsyncSession: Database session

    Usage:
        async with get_db_session() as db:
            # Use db session
            pass
    """
    return SessionLocal()


def get_sync_session() -> Session:
    """
    Get a synchronous database session (for CLI tools and migrations).

    Returns:
        Session: Synchronous database session
    """
    from sqlalchemy.orm import sessionmaker
    SyncSessionLocal = sessionmaker(
        sync_engine,
        autoflush=False,
        autocommit=False
    )
    return SyncSessionLocal()
