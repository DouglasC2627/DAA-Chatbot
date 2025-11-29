"""
Settings API routes.

This module provides REST API endpoints for system settings management:
- Get current settings
- Update model configuration (LLM and embedding)
- List installed models
- Get popular models
- Pull/install models
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.settings_service import settings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Pydantic models for request/response

class SettingsResponse(BaseModel):
    """Response model for system settings."""
    default_llm_model: str
    default_embedding_model: str
    default_chunk_size: int
    default_chunk_overlap: int
    default_retrieval_k: int
    theme: str

    class Config:
        from_attributes = True


class ModelUpdateRequest(BaseModel):
    """Request model for updating models."""
    llm_model: Optional[str] = Field(None, description="LLM model name")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    size: int
    modified_at: Optional[str] = None


class InstalledModelsResponse(BaseModel):
    """Response model for installed models."""
    llm_models: List[ModelInfo]
    embedding_models: List[ModelInfo]
    current_llm: str
    current_embedding: str


class PopularModel(BaseModel):
    """Popular model information."""
    name: str
    size: str
    description: str
    installed: bool


class PopularModelsResponse(BaseModel):
    """Response model for popular models."""
    llm_models: List[PopularModel]
    embedding_models: List[PopularModel]


class ModelPullRequest(BaseModel):
    """Request model for pulling a model."""
    model_name: str = Field(..., min_length=1, description="Name of model to pull")


class ModelPullResponse(BaseModel):
    """Response model for model pull operation."""
    success: bool
    model_name: str
    message: str


class SearchModelRequest(BaseModel):
    """Request model for searching models."""
    query: str = Field(..., min_length=1, description="Search query")
    model_type: Optional[str] = Field(None, description="Filter by type: 'llm' or 'embedding'")


class SearchResultModel(BaseModel):
    """Search result model."""
    name: str
    size: str
    description: str
    type: str
    installed: bool
    featured: Optional[bool] = False


# API Endpoints

@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db)
) -> SettingsResponse:
    """
    Get current system settings.

    Returns the current configuration including model selections and RAG settings.
    """
    try:
        settings = await settings_service.get_settings(db)

        return SettingsResponse(
            default_llm_model=settings.default_llm_model,
            default_embedding_model=settings.default_embedding_model,
            default_chunk_size=settings.default_chunk_size,
            default_chunk_overlap=settings.default_chunk_overlap,
            default_retrieval_k=settings.default_retrieval_k,
            theme=settings.theme
        )

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}"
        )


@router.put("/models", response_model=SettingsResponse)
async def update_models(
    request: ModelUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> SettingsResponse:
    """
    Update model configuration.

    Updates the default LLM and/or embedding model. Models must be installed first.

    Args:
        request: Model update request with optional llm_model and embedding_model

    Returns:
        Updated settings

    Raises:
        400: If neither llm_model nor embedding_model is provided
        404: If specified model is not installed
        500: If update fails
    """
    if not request.llm_model and not request.embedding_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one of llm_model or embedding_model"
        )

    try:
        # Update LLM model if provided
        if request.llm_model:
            settings = await settings_service.update_llm_model(db, request.llm_model)

        # Update embedding model if provided
        if request.embedding_model:
            settings = await settings_service.update_embedding_model(db, request.embedding_model)

        # Get final settings
        settings = await settings_service.get_settings(db)

        return SettingsResponse(
            default_llm_model=settings.default_llm_model,
            default_embedding_model=settings.default_embedding_model,
            default_chunk_size=settings.default_chunk_size,
            default_chunk_overlap=settings.default_chunk_overlap,
            default_retrieval_k=settings.default_retrieval_k,
            theme=settings.theme
        )

    except ValueError as e:
        # Model not installed
        logger.warning(f"Model validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update models: {str(e)}"
        )


@router.get("/models/installed", response_model=InstalledModelsResponse)
async def get_installed_models() -> InstalledModelsResponse:
    """
    Get all installed models categorized by type.

    Returns models organized into LLM and embedding categories based on model names.

    Returns:
        Installed models with current model selections
    """
    try:
        models = await settings_service.get_installed_models()

        return InstalledModelsResponse(
            llm_models=[ModelInfo(**model) for model in models["llm_models"]],
            embedding_models=[ModelInfo(**model) for model in models["embedding_models"]],
            current_llm=models["current_llm"],
            current_embedding=models["current_embedding"]
        )

    except Exception as e:
        import traceback
        logger.error(f"Failed to get installed models: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get installed models: {str(e)}"
        )


@router.get("/models/popular", response_model=PopularModelsResponse)
async def get_popular_models() -> PopularModelsResponse:
    """
    Get popular models available for installation.

    Returns a curated list of recommended models with installation status.

    Returns:
        Popular models with installation status
    """
    try:
        models = await settings_service.get_popular_models()

        return PopularModelsResponse(
            llm_models=[PopularModel(**model) for model in models["llm_models"]],
            embedding_models=[PopularModel(**model) for model in models["embedding_models"]]
        )

    except Exception as e:
        logger.error(f"Failed to get popular models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular models: {str(e)}"
        )


@router.post("/models/pull", response_model=ModelPullResponse)
async def pull_model(request: ModelPullRequest) -> ModelPullResponse:
    """
    Pull/download a model from Ollama library.

    Downloads the specified model from Ollama's model library.
    This may take several minutes depending on model size and network speed.

    Args:
        request: Model pull request with model_name

    Returns:
        Result of the pull operation

    Raises:
        500: If pull fails
    """
    try:
        success = await settings_service.pull_model(request.model_name)

        if success:
            return ModelPullResponse(
                success=True,
                model_name=request.model_name,
                message=f"Successfully pulled model '{request.model_name}'"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pull model '{request.model_name}'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling model '{request.model_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull model: {str(e)}"
        )


@router.get("/models/search", response_model=List[SearchResultModel])
async def search_models(
    query: str = Query(..., min_length=1, description="Search query"),
    model_type: Optional[str] = Query(None, description="Filter by type: 'llm' or 'embedding'")
) -> List[SearchResultModel]:
    """
    Search for models in Ollama library.

    Searches through available models by name and description.

    Args:
        query: Search query string
        model_type: Optional filter ('llm' or 'embedding')

    Returns:
        List of matching models with installation status

    Raises:
        400: If invalid model_type provided
        500: If search fails
    """
    if model_type and model_type not in ["llm", "embedding"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_type must be 'llm' or 'embedding'"
        )

    try:
        results = await settings_service.search_models(query, model_type)

        return [
            SearchResultModel(**result)
            for result in results
        ]

    except Exception as e:
        logger.error(f"Error searching models with query '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search models: {str(e)}"
        )
