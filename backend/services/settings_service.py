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


# Popular models configuration - Expanded database for search
POPULAR_MODELS = {
    "llm": [
        # Featured/Popular models
        {"name": "llama3.2", "size": "2.0GB", "description": "Fast and capable, great for general use", "featured": True},
        {"name": "llama3.1", "size": "4.7GB", "description": "More powerful, better reasoning", "featured": True},
        {"name": "mistral", "size": "4.1GB", "description": "Fast and efficient", "featured": True},
        {"name": "mixtral", "size": "26GB", "description": "Mixture of experts, very capable", "featured": True},
        {"name": "qwen2.5", "size": "4.7GB", "description": "Strong multilingual capabilities", "featured": True},
        {"name": "phi3", "size": "2.3GB", "description": "Small but powerful", "featured": True},

        # Llama family
        {"name": "llama3", "size": "4.7GB", "description": "Meta's Llama 3 model"},
        {"name": "llama2", "size": "3.8GB", "description": "Meta's Llama 2 model"},
        {"name": "codellama", "size": "3.8GB", "description": "Code-specialized Llama model"},

        # Mistral family
        {"name": "mistral-nemo", "size": "7.1GB", "description": "12B model with 128k context"},
        {"name": "mistral-small", "size": "12GB", "description": "22B parameter model"},
        {"name": "dolphin-mistral", "size": "4.1GB", "description": "Uncensored Mistral variant"},

        # Qwen family
        {"name": "qwen2.5-coder", "size": "4.7GB", "description": "Code-specialized Qwen model"},
        {"name": "qwen2", "size": "4.4GB", "description": "Alibaba's Qwen 2 model"},

        # Phi family
        {"name": "phi3.5", "size": "2.2GB", "description": "Improved Phi 3.5 model"},

        # Gemma family
        {"name": "gemma2", "size": "5.4GB", "description": "Google's Gemma 2 9B model"},
        {"name": "gemma", "size": "5.0GB", "description": "Google's Gemma model"},
        {"name": "codegemma", "size": "5.0GB", "description": "Code-specialized Gemma"},

        # DeepSeek family
        {"name": "deepseek-coder", "size": "6.7GB", "description": "Excellent code model"},
        {"name": "deepseek-r1", "size": "3.9GB", "description": "DeepSeek reasoning model"},
        {"name": "deepseek-llm", "size": "6.7GB", "description": "DeepSeek general model"},

        # Chat models
        {"name": "openchat", "size": "4.1GB", "description": "Fine-tuned for chat"},
        {"name": "starling-lm", "size": "4.1GB", "description": "RLAIF trained chat model"},
        {"name": "neural-chat", "size": "4.1GB", "description": "Fine-tuned chat model"},
        {"name": "vicuna", "size": "3.8GB", "description": "ChatGPT-style model"},

        # Instruction models
        {"name": "nous-hermes2", "size": "4.1GB", "description": "Instruction-tuned model"},
        {"name": "wizardlm2", "size": "4.7GB", "description": "Instruction following model"},

        # Yi models
        {"name": "yi", "size": "6.7GB", "description": "01.AI's Yi model"},
        {"name": "yi-coder", "size": "6.7GB", "description": "Yi code model"},

        # Small/Efficient models
        {"name": "orca-mini", "size": "1.9GB", "description": "Lightweight Orca model"},
        {"name": "stablelm2", "size": "1.6GB", "description": "Stability AI's model"},

        # Other notable models
        {"name": "solar", "size": "6.1GB", "description": "Upstage Solar model"},
        {"name": "falcon", "size": "3.8GB", "description": "TII's Falcon model"},

        # Newest models (2025)
        {"name": "gpt-oss", "size": "3.0GB", "description": "Open source GPT implementation"},
        {"name": "llama3.3", "size": "42GB", "description": "Latest Llama 3.3 model"},
        {"name": "qwen2.5-instruct", "size": "4.7GB", "description": "Qwen 2.5 instruction-tuned"},
    ],
    "embedding": [
        # Featured/Popular embeddings
        {"name": "nomic-embed-text", "size": "274MB", "description": "High quality embeddings, 8k context", "featured": True},
        {"name": "mxbai-embed-large", "size": "669MB", "description": "Larger, more accurate embeddings", "featured": True},
        {"name": "all-minilm", "size": "23MB", "description": "Lightweight and fast", "featured": True},

        # Additional embeddings
        {"name": "bge-large", "size": "1.3GB", "description": "BAAI general embedding, high quality"},
        {"name": "bge-m3", "size": "2.2GB", "description": "Multi-lingual, multi-functional"},
        {"name": "snowflake-arctic-embed", "size": "335MB", "description": "Snowflake's embedding model"},
        {"name": "gte-large", "size": "670MB", "description": "Alibaba's GTE embedding"},

        # Newest embeddings (2025)
        {"name": "embeddinggemma", "size": "274MB", "description": "Google's Gemma-based embedding model"},
        {"name": "jina-embeddings-v3", "size": "570MB", "description": "Jina AI's latest embedding model"},
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
        Get popular/featured models with installation status.

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

            # Filter only featured models
            llm_models = []
            for model in POPULAR_MODELS["llm"]:
                if model.get("featured", False):
                    llm_models.append({
                        **model,
                        "installed": model["name"] in installed_names
                    })

            embedding_models = []
            for model in POPULAR_MODELS["embedding"]:
                if model.get("featured", False):
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
            # Return featured models without installation status
            return {
                "llm_models": [
                    {**model, "installed": False}
                    for model in POPULAR_MODELS["llm"]
                    if model.get("featured", False)
                ],
                "embedding_models": [
                    {**model, "installed": False}
                    for model in POPULAR_MODELS["embedding"]
                    if model.get("featured", False)
                ]
            }

    @staticmethod
    async def search_models(query: str, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for models in the Ollama library.

        Args:
            query: Search query (model name)
            model_type: Optional filter - 'llm' or 'embedding'

        Returns:
            List of matching models with installation status
        """
        try:
            query_lower = query.lower().strip()

            # Get installed models
            all_models = await ollama_client.list_models()
            installed_names = {
                model.get('name', '').split(':')[0]
                for model in all_models
                if model.get('name', '').split(':')[0].strip() != ''
            }

            results = []

            # Search in LLM models
            if model_type is None or model_type == "llm":
                for model in POPULAR_MODELS["llm"]:
                    if query_lower in model["name"].lower() or query_lower in model["description"].lower():
                        results.append({
                            **model,
                            "type": "llm",
                            "installed": model["name"] in installed_names
                        })

            # Search in embedding models
            if model_type is None or model_type == "embedding":
                for model in POPULAR_MODELS["embedding"]:
                    if query_lower in model["name"].lower() or query_lower in model["description"].lower():
                        results.append({
                            **model,
                            "type": "embedding",
                            "installed": model["name"] in installed_names
                        })

            return results

        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []

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
