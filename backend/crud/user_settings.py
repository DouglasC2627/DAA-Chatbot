"""
CRUD operations for UserSettings model.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_settings import UserSettings
from crud.base import CRUDBase


class CRUDUserSettings(CRUDBase[UserSettings]):
    """CRUD operations for UserSettings model."""

    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Optional[UserSettings]:
        """
        Get user settings by user_id.

        Args:
            db: Database session
            user_id: User identifier

        Returns:
            UserSettings instance or None
        """
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_default_user_settings(self, db: AsyncSession) -> Optional[UserSettings]:
        """
        Get settings for the default user.

        For single-user local deployment, this returns the main settings.

        Args:
            db: Database session

        Returns:
            UserSettings instance or None
        """
        return await self.get_by_user_id(db, "default_user")

    async def get_or_create_default(self, db: AsyncSession) -> UserSettings:
        """
        Get or create default user settings.

        If default user settings don't exist, creates them with default values.

        Args:
            db: Database session

        Returns:
            UserSettings instance
        """
        settings = await self.get_default_user_settings(db)

        if not settings:
            # Create default settings
            settings = UserSettings(
                user_id="default_user",
                default_llm_model="llama3.2",
                default_embedding_model="nomic-embed-text",
                default_chunk_size=1000,
                default_chunk_overlap=200,
                default_retrieval_k=5,
                theme="light"
            )
            db.add(settings)
            await db.flush()
            await db.refresh(settings)

        return settings

    async def update_model_settings(
        self,
        db: AsyncSession,
        *,
        llm_model: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> UserSettings:
        """
        Update model settings for default user.

        Args:
            db: Database session
            llm_model: New default LLM model (optional)
            embedding_model: New default embedding model (optional)

        Returns:
            Updated UserSettings instance
        """
        settings = await self.get_or_create_default(db)

        # Use the model's update method
        settings.update_model_defaults(
            llm_model=llm_model,
            embedding_model=embedding_model
        )

        await db.flush()
        await db.refresh(settings)
        return settings

    async def update_rag_settings(
        self,
        db: AsyncSession,
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        retrieval_k: Optional[int] = None
    ) -> UserSettings:
        """
        Update RAG configuration settings for default user.

        Args:
            db: Database session
            chunk_size: New default chunk size (optional)
            chunk_overlap: New default chunk overlap (optional)
            retrieval_k: New default retrieval count (optional)

        Returns:
            Updated UserSettings instance
        """
        settings = await self.get_or_create_default(db)

        # Use the model's update method
        settings.update_rag_defaults(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            retrieval_k=retrieval_k
        )

        await db.flush()
        await db.refresh(settings)
        return settings


# Create instance
user_settings = CRUDUserSettings(UserSettings)
