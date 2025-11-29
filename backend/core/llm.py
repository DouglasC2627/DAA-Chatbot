"""
LLM integration module for Ollama.

This module provides a wrapper around the Ollama API for:
- Model listing and management
- Basic text generation
- Streaming responses
- Error handling and connection management
"""

import logging
from typing import Optional, Dict, List, AsyncGenerator, Any
import ollama
from ollama import AsyncClient, Client
from core.config import settings

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Custom exception for Ollama client errors"""
    pass


class OllamaClient:
    """
    Wrapper class for Ollama API operations.

    Provides both synchronous and asynchronous methods for:
    - Model listing and information
    - Text generation (blocking and streaming)
    - Connection health checks
    - Model switching
    """

    def __init__(
        self,
        host: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        """
        Initialize Ollama client.

        Args:
            host: Ollama server URL. Defaults to settings.OLLAMA_HOST
            default_model: Default model to use. Defaults to settings.OLLAMA_MODEL
        """
        self.host = host or settings.OLLAMA_HOST
        self.default_model = default_model or settings.OLLAMA_MODEL

        # Initialize sync and async clients
        self._client: Optional[Client] = None
        self._async_client: Optional[AsyncClient] = None

        logger.info(f"OllamaClient initialized with host={self.host}, model={self.default_model}")

    @property
    def client(self) -> Client:
        """Get or create synchronous Ollama client"""
        if self._client is None:
            self._client = Client(host=self.host)
        return self._client

    @property
    def async_client(self) -> AsyncClient:
        """Get or create asynchronous Ollama client"""
        if self._async_client is None:
            self._async_client = AsyncClient(host=self.host)
        return self._async_client

    async def check_connection(self) -> bool:
        """
        Check if Ollama server is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.async_client.list()
            model_count = len(response.models) if hasattr(response, 'models') else 0
            logger.info(f"Successfully connected to Ollama. Found {model_count} models.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama at {self.host}: {str(e)}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models.

        Returns:
            List of model information dictionaries

        Raises:
            OllamaClientError: If unable to fetch models
        """
        try:
            response = await self.async_client.list()
            # Access models attribute directly from ListResponse object
            models_list = response.models

            # Convert model objects to dictionaries
            models = []
            for model in models_list:
                models.append({
                    'name': model.model,
                    'size': model.size,
                    'modified_at': str(model.modified_at) if model.modified_at else None,
                    'digest': getattr(model, 'digest', None)
                })

            logger.info(f"Retrieved {len(models)} models from Ollama")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            raise OllamaClientError(f"Failed to list models: {str(e)}")

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model information dictionary

        Raises:
            OllamaClientError: If model not found or error occurs
        """
        try:
            response = await self.async_client.show(model_name)
            logger.info(f"Retrieved info for model: {model_name}")
            return response
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {str(e)}")
            raise OllamaClientError(f"Failed to get model info: {str(e)}")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM (non-streaming).

        Args:
            prompt: User prompt/question
            model: Model to use (defaults to self.default_model)
            system: System prompt to set context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Ollama API

        Returns:
            Generated text response

        Raises:
            OllamaClientError: If generation fails
        """
        model = model or self.default_model

        try:
            logger.info(f"Generating response with model={model}, temp={temperature}")

            # Prepare options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            # Merge with additional kwargs
            options.update(kwargs)

            # Call Ollama API
            response = await self.async_client.generate(
                model=model,
                prompt=prompt,
                system=system,
                options=options,
                stream=False
            )

            generated_text = response.get('response', '')
            logger.info(f"Generated {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise OllamaClientError(f"Generation failed: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.

        Args:
            prompt: User prompt/question
            model: Model to use (defaults to self.default_model)
            system: System prompt to set context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Ollama API

        Yields:
            Text chunks as they are generated

        Raises:
            OllamaClientError: If generation fails
        """
        model = model or self.default_model

        try:
            logger.info(f"Starting streaming generation with model={model}, temp={temperature}")

            # Prepare options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            # Merge with additional kwargs
            options.update(kwargs)

            # Stream from Ollama API
            stream = await self.async_client.generate(
                model=model,
                prompt=prompt,
                system=system,
                options=options,
                stream=True
            )

            # Yield chunks as they arrive
            async for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']

            logger.info("Streaming generation completed")

        except Exception as e:
            logger.error(f"Streaming generation failed: {str(e)}")
            raise OllamaClientError(f"Streaming generation failed: {str(e)}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Chat completion using message history (non-streaming).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Ollama API

        Returns:
            Generated response text

        Raises:
            OllamaClientError: If chat fails
        """
        model = model or self.default_model

        try:
            logger.info(f"Chat completion with model={model}, {len(messages)} messages")

            # Prepare options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            # Merge with additional kwargs
            options.update(kwargs)

            # Call Ollama chat API
            response = await self.async_client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=False
            )

            message_content = response.get('message', {}).get('content', '')
            logger.info(f"Chat completed, generated {len(message_content)} characters")
            return message_content

        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise OllamaClientError(f"Chat failed: {str(e)}")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion with streaming response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for Ollama API

        Yields:
            Text chunks as they are generated

        Raises:
            OllamaClientError: If chat fails
        """
        model = model or self.default_model

        try:
            logger.info(f"Starting streaming chat with model={model}, {len(messages)} messages")

            # Prepare options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            # Merge with additional kwargs
            options.update(kwargs)

            # Stream from Ollama chat API
            stream = await self.async_client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=True
            )

            # Yield chunks as they arrive
            async for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

            logger.info("Streaming chat completed")

        except Exception as e:
            logger.error(f"Streaming chat failed: {str(e)}")
            raise OllamaClientError(f"Streaming chat failed: {str(e)}")

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            await self.async_client.pull(model_name)
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {str(e)}")
            return False

    def switch_model(self, model_name: str) -> None:
        """
        Switch the default model.

        Args:
            model_name: Name of the model to switch to
        """
        logger.info(f"Switching default model from {self.default_model} to {model_name}")
        self.default_model = model_name


# Create global instance
ollama_client = OllamaClient()


# Convenience functions for direct access
async def generate_response(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Convenience function for generating a response.

    Args:
        prompt: User prompt
        model: Model to use
        system: System prompt
        temperature: Sampling temperature
        **kwargs: Additional parameters

    Returns:
        Generated text
    """
    return await ollama_client.generate(
        prompt=prompt,
        model=model,
        system=system,
        temperature=temperature,
        **kwargs
    )


async def generate_response_stream(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function for streaming generation.

    Args:
        prompt: User prompt
        model: Model to use
        system: System prompt
        temperature: Sampling temperature
        **kwargs: Additional parameters

    Yields:
        Text chunks
    """
    async for chunk in ollama_client.generate_stream(
        prompt=prompt,
        model=model,
        system=system,
        temperature=temperature,
        **kwargs
    ):
        yield chunk
