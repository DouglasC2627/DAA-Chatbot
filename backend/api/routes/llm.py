"""
LLM API routes for model management and inference.

Endpoints for:
- Listing available models
- Getting model information
- Testing model generation
- Model switching
- Health checks
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from core.llm import ollama_client, OllamaClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM"])


# Pydantic models for request/response
class ModelInfo(BaseModel):
    """Model information response"""
    name: str
    size: Optional[int] = None
    digest: Optional[str] = None
    modified_at: Optional[Any] = None  # Can be datetime or string
    details: Optional[Any] = None  # Can be dict or ModelDetails object

    class Config:
        arbitrary_types_allowed = True


class ModelsListResponse(BaseModel):
    """Response for listing models"""
    models: List[ModelInfo]
    count: int
    default_model: str


class ModelDetailsResponse(BaseModel):
    """Detailed model information response"""
    name: str
    details: Dict[str, Any]


class GenerateRequest(BaseModel):
    """Request for text generation"""
    prompt: str = Field(..., description="The prompt to generate from")
    model: Optional[str] = Field(None, description="Model to use (optional)")
    system: Optional[str] = Field(None, description="System prompt (optional)")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Temperature for sampling")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")


class GenerateResponse(BaseModel):
    """Response from text generation"""
    response: str
    model: str


class ModelSwitchRequest(BaseModel):
    """Request to switch default model"""
    model: str = Field(..., description="Name of model to switch to")


class StatusResponse(BaseModel):
    """LLM connection status response"""
    connected: bool
    host: str
    default_model: str
    message: str


@router.get("/status", response_model=StatusResponse)
async def get_llm_status():
    """
    Check LLM connection status.

    Returns connection status, host, and default model.
    """
    try:
        is_connected = await ollama_client.check_connection()
        return StatusResponse(
            connected=is_connected,
            host=ollama_client.host,
            default_model=ollama_client.default_model,
            message="Connected to Ollama" if is_connected else "Cannot connect to Ollama"
        )
    except Exception as e:
        logger.error(f"Error checking LLM status: {str(e)}")
        return StatusResponse(
            connected=False,
            host=ollama_client.host,
            default_model=ollama_client.default_model,
            message=f"Error: {str(e)}"
        )


@router.get("/models", response_model=ModelsListResponse)
async def list_models():
    """
    List all available Ollama models.

    Returns a list of models with their metadata.
    """
    try:
        models_data = await ollama_client.list_models()

        # Transform model data to ModelInfo format
        models = []
        for model in models_data:
            models.append(ModelInfo(
                name=model.get('name', ''),
                size=model.get('size'),
                digest=model.get('digest'),
                modified_at=model.get('modified_at'),
                details=model.get('details')
            ))

        return ModelsListResponse(
            models=models,
            count=len(models),
            default_model=ollama_client.default_model
        )

    except OllamaClientError as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to list models: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/models/{model_name}", response_model=ModelDetailsResponse)
async def get_model_info(model_name: str):
    """
    Get detailed information about a specific model.

    Args:
        model_name: Name of the model to get information about

    Returns:
        Detailed model information
    """
    try:
        model_info = await ollama_client.get_model_info(model_name)

        return ModelDetailsResponse(
            name=model_name,
            details=model_info
        )

    except OllamaClientError as e:
        logger.error(f"Error getting model info for {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text from a prompt (non-streaming).

    This is a test endpoint for basic LLM functionality.
    For production chat, use the chat endpoints with RAG.

    Args:
        request: Generation request with prompt and parameters

    Returns:
        Generated text response
    """
    try:
        logger.info(f"Generating text with prompt length: {len(request.prompt)}")

        response_text = await ollama_client.generate(
            prompt=request.prompt,
            model=request.model,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return GenerateResponse(
            response=response_text,
            model=request.model or ollama_client.default_model
        )

    except OllamaClientError as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """
    Switch the default model used for generation.

    Args:
        request: Model switch request with model name

    Returns:
        Success message with new default model
    """
    try:
        # Verify model exists
        models = await ollama_client.list_models()
        model_names = [model.get('name', '') for model in models]

        if request.model not in model_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model}' not found. Available models: {', '.join(model_names)}"
            )

        # Switch model
        ollama_client.switch_model(request.model)

        return {
            "message": f"Successfully switched to model: {request.model}",
            "default_model": ollama_client.default_model
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch model: {str(e)}"
        )


@router.post("/model/pull/{model_name}")
async def pull_model(model_name: str):
    """
    Pull/download a model from Ollama library.

    Args:
        model_name: Name of the model to pull

    Returns:
        Success or failure message
    """
    try:
        logger.info(f"Attempting to pull model: {model_name}")

        success = await ollama_client.pull_model(model_name)

        if success:
            return {
                "message": f"Successfully pulled model: {model_name}",
                "model": model_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pull model: {model_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull model: {str(e)}"
        )
