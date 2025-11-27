"""
Settings service for managing system configuration.

This service handles:
- Model configuration (LLM and embedding models)
- RAG settings (chunk size, overlap, retrieval count)
- Model installation and validation
- Persistence of settings to database
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user_settings import user_settings as crud_user_settings
from models.user_settings import UserSettings
from core.llm import ollama_client
from core.embeddings import embedding_service

logger = logging.getLogger(__name__)


# Popular models configuration
POPULAR_MODELS = {
    "llm": [
        {"name": "llama3.2", "size": "2.0GB", "description": "Fast and capable, great for general use"},
        {"name": "llama3.1", "size": "4.7GB", "description": "More powerful, better reasoning"},
        {"name": "mistral", "size": "4.1GB", "description": "Fast and efficient"},
        {"name": "mixtral", "size": "26GB", "description": "Mixture of experts, very capable"},
        {"name": "qwen2.5", "size": "4.7GB", "description": "Strong multilingual capabilities"},
        {"name": "phi3", "size": "2.3GB", "description": "Small but powerful"},
    ],
    "embedding": [
        {"name": "nomic-embed-text", "size": "274MB", "description": "High quality embeddings"},
        {"name": "mxbai-embed-large", "size": "669MB", "description": "Larger, more accurate"},
        {"name": "all-minilm", "size": "23MB", "description": "Lightweight and fast"},
    ]
}


class SettingsService:
    """Service for managing system settings and model configuration."""

    @staticmethod
    async def get_settings(db: AsyncSession) -> UserSettings:
        """
        Get current system settings.

        Args:
            db: Database session

        Returns:
            UserSettings instance
        """
        settings = await crud_user_settings.get_or_create_default(db)
        await db.commit()
        return settings

    @staticmethod
    async def update_llm_model(db: AsyncSession, model_name: str) -> UserSettings:
        """
        Update the default LLM model.

        This method:
        1. Validates that the model is installed
        2. Updates the database
        3. Updates the global ollama_client singleton

        Args:
            db: Database session
            model_name: Name of the LLM model

        Returns:
            Updated UserSettings instance

        Raises:
            ValueError: If model is not installed
        """
        # Validate model exists
        try:
            installed_models = await ollama_client.list_models()
            model_names = [
                model.get('name', '').split(':')[0]
                for model in installed_models
                if model.get('name', '').split(':')[0].strip() != ''
            ]

            if model_name not in model_names:
                raise ValueError(f"Model '{model_name}' is not installed. Please install it first.")

        except Exception as e:
            logger.error(f"Failed to validate LLM model '{model_name}': {e}")
            raise ValueError(f"Failed to validate model: {str(e)}")

        # Update database
        settings = await crud_user_settings.update_model_settings(
            db,
            llm_model=model_name
        )
        await db.commit()

        # Update global singleton (for immediate effect)
        ollama_client.switch_model(model_name)

        logger.info(f"Successfully updated LLM model to '{model_name}'")
        return settings

    @staticmethod
    async def update_embedding_model(db: AsyncSession, model_name: str) -> UserSettings:
        """
        Update the default embedding model.

        This method:
        1. Validates that the model is installed
        2. Updates the database
        3. Updates the global embedding_service singleton

        Args:
            db: Database session
            model_name: Name of the embedding model

        Returns:
            Updated UserSettings instance

        Raises:
            ValueError: If model is not installed
        """
        # Validate model exists
        try:
            installed_models = await ollama_client.list_models()
            model_names = [
                model.get('name', '').split(':')[0]
                for model in installed_models
                if model.get('name', '').split(':')[0].strip() != ''
            ]

            if model_name not in model_names:
                raise ValueError(f"Model '{model_name}' is not installed. Please install it first.")

        except Exception as e:
            logger.error(f"Failed to validate embedding model '{model_name}': {e}")
            raise ValueError(f"Failed to validate model: {str(e)}")

        # Update database
        settings = await crud_user_settings.update_model_settings(
            db,
            embedding_model=model_name
        )
        await db.commit()

        # Update global singleton (for immediate effect)
        embedding_service.switch_model(model_name)

        logger.info(f"Successfully updated embedding model to '{model_name}'")
        return settings

    @staticmethod
    async def get_installed_models() -> Dict[str, Any]:
        """
        Get all installed models categorized by type.

        Models are categorized as:
        - LLM models: Models without 'embed' in name
        - Embedding models: Models with 'embed' in name

        Returns:
            Dictionary with llm_models, embedding_models, current_llm, current_embedding
        """
        try:
            all_models = await ollama_client.list_models()

            llm_models = []
            embedding_models = []

            for model in all_models:
                model_name = model.get('name', '').split(':')[0]

                # Skip models with empty names
                if not model_name or model_name.strip() == '':
                    continue

                model_size = model.get('size', 0)
                modified_at = model.get('modified_at', '')

                # Convert datetime to string if needed
                if hasattr(modified_at, 'isoformat'):
                    modified_at = modified_at.isoformat()

                model_info = {
                    "name": model_name,
                    "size": model_size,
                    "modified_at": modified_at
                }

                # Categorize based on name
                if 'embed' in model_name.lower():
                    embedding_models.append(model_info)
                else:
                    llm_models.append(model_info)

            return {
                "llm_models": llm_models,
                "embedding_models": embedding_models,
                "current_llm": ollama_client.default_model,
                "current_embedding": embedding_service.model
            }

        except Exception as e:
            logger.error(f"Failed to get installed models: {e}")
            return {
                "llm_models": [],
                "embedding_models": [],
                "current_llm": ollama_client.default_model,
                "current_embedding": embedding_service.model
            }

    @staticmethod
    async def get_popular_models() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get popular models with installation status.

        Returns:
            Dictionary with llm_models and embedding_models lists,
            each with name, size, description, and installed status
        """
        try:
            # Get installed models
            all_models = await ollama_client.list_models()
            installed_names = {
                model.get('name', '').split(':')[0]
                for model in all_models
                if model.get('name', '').split(':')[0].strip() != ''
            }

            # Add installation status to popular models
            llm_models = []
            for model in POPULAR_MODELS["llm"]:
                llm_models.append({
                    **model,
                    "installed": model["name"] in installed_names
                })

            embedding_models = []
            for model in POPULAR_MODELS["embedding"]:
                embedding_models.append({
                    **model,
                    "installed": model["name"] in installed_names
                })

            return {
                "llm_models": llm_models,
                "embedding_models": embedding_models
            }

        except Exception as e:
            logger.error(f"Failed to get popular models: {e}")
            # Return popular models without installation status
            return {
                "llm_models": [
                    {**model, "installed": False} for model in POPULAR_MODELS["llm"]
                ],
                "embedding_models": [
                    {**model, "installed": False} for model in POPULAR_MODELS["embedding"]
                ]
            }

    @staticmethod
    async def pull_model(model_name: str) -> bool:
        """
        Pull/download a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If pull fails
        """
        try:
            logger.info(f"Pulling model '{model_name}'...")
            success = await ollama_client.pull_model(model_name)

            if success:
                logger.info(f"Successfully pulled model '{model_name}'")
            else:
                logger.error(f"Failed to pull model '{model_name}'")

            return success

        except Exception as e:
            logger.error(f"Error pulling model '{model_name}': {e}")
            raise Exception(f"Failed to pull model: {str(e)}")


# Create service instance
settings_service = SettingsService()
