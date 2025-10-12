"""
Tests for Ollama integration.

This test suite tests:
1. Connection to Ollama server
2. Listing available models
3. Getting model information
4. Basic text generation
5. Streaming text generation
6. Model switching
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.llm import ollama_client, OllamaClientError


@pytest.fixture(scope="module")
def check_ollama():
    """Check if Ollama is available before running tests."""
    import asyncio
    try:
        connected = asyncio.run(ollama_client.check_connection())
        if not connected:
            pytest.skip("Ollama server not available")
    except Exception:
        pytest.skip("Ollama server not available")


class TestConnection:
    """Test connection to Ollama server."""

    @pytest.mark.asyncio
    async def test_check_connection(self, check_ollama):
        """Test connection to Ollama."""
        connected = await ollama_client.check_connection()
        assert connected is True


class TestListModels:
    """Test listing available models."""

    @pytest.mark.asyncio
    async def test_list_models(self, check_ollama):
        """Test listing available models."""
        models = await ollama_client.list_models()

        assert isinstance(models, list)
        assert len(models) > 0

        # Verify model structure
        for model in models:
            assert 'name' in model
            assert 'size' in model


class TestModelInfo:
    """Test getting model information."""

    @pytest.mark.asyncio
    async def test_get_model_info(self, check_ollama):
        """Test getting model information."""
        model_name = ollama_client.default_model

        info = await ollama_client.get_model_info(model_name)

        assert info is not None
        assert isinstance(info, dict)

    @pytest.mark.asyncio
    async def test_get_nonexistent_model_info(self, check_ollama):
        """Test getting info for non-existent model."""
        with pytest.raises(OllamaClientError):
            await ollama_client.get_model_info("nonexistent-model-12345")


class TestTextGeneration:
    """Test basic text generation."""

    @pytest.mark.asyncio
    async def test_generate_basic(self, check_ollama):
        """Test basic text generation."""
        prompt = "What is the capital of France? Answer in one sentence."

        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=50
        )

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, check_ollama):
        """Test text generation with custom parameters."""
        prompt = "Count from 1 to 3."

        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.1,  # Lower temperature for more deterministic output
            max_tokens=20
        )

        assert response is not None
        assert len(response) > 0


class TestStreamingGeneration:
    """Test streaming text generation."""

    @pytest.mark.asyncio
    async def test_generate_stream(self, check_ollama):
        """Test streaming text generation."""
        prompt = "Count from 1 to 3, one number per line."

        chunks = []
        async for chunk in ollama_client.generate_stream(
            prompt=prompt,
            temperature=0.7,
            max_tokens=50
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

        # Verify we can reconstruct the full response
        full_response = ''.join(chunks)
        assert len(full_response) > 0

    @pytest.mark.asyncio
    async def test_stream_handles_errors(self, check_ollama):
        """Test that streaming handles errors gracefully."""
        # Use an empty prompt which might cause issues
        try:
            chunks = []
            async for chunk in ollama_client.generate_stream(
                prompt="",
                temperature=0.7,
                max_tokens=10
            ):
                chunks.append(chunk)

            # If it doesn't error, that's fine too
            assert True
        except OllamaClientError:
            # Expected error for empty prompt
            assert True


class TestChatInterface:
    """Test chat interface."""

    @pytest.mark.asyncio
    async def test_chat_basic(self, check_ollama):
        """Test basic chat functionality."""
        messages = [
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ]

        response = await ollama_client.chat(
            messages=messages,
            temperature=0.1
        )

        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_history(self, check_ollama):
        """Test chat with conversation history."""
        messages = [
            {"role": "user", "content": "My favorite color is blue."},
            {"role": "assistant", "content": "That's nice! Blue is a calming color."},
            {"role": "user", "content": "What did I say my favorite color was?"}
        ]

        response = await ollama_client.chat(
            messages=messages,
            temperature=0.7
        )

        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_stream(self, check_ollama):
        """Test streaming chat."""
        messages = [
            {"role": "user", "content": "Count from 1 to 3."}
        ]

        chunks = []
        async for chunk in ollama_client.chat_stream(
            messages=messages,
            temperature=0.7
        ):
            chunks.append(chunk)

        assert len(chunks) > 0


class TestModelSwitching:
    """Test model switching functionality."""

    @pytest.mark.asyncio
    async def test_switch_model(self, check_ollama):
        """Test switching between models."""
        original_model = ollama_client.default_model

        # Get list of available models
        models = await ollama_client.list_models()
        assert len(models) >= 1

        # Switch to first available model
        test_model = models[0].get('name')
        ollama_client.switch_model(test_model)

        assert ollama_client.default_model == test_model

        # Switch back
        ollama_client.switch_model(original_model)
        assert ollama_client.default_model == original_model

    def test_get_available_models(self, check_ollama):
        """Test getting list of model names."""
        # This is a synchronous method
        models = ollama_client.get_available_models()

        assert isinstance(models, list)
        # Can't guarantee any models, but default model should exist
        assert ollama_client.default_model is not None


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_generation_with_invalid_model(self, check_ollama):
        """Test that invalid model raises error."""
        original_model = ollama_client.default_model

        try:
            ollama_client.switch_model("invalid-model-name-12345")

            with pytest.raises(OllamaClientError):
                await ollama_client.generate(
                    prompt="Test",
                    temperature=0.7
                )
        finally:
            # Restore original model
            ollama_client.switch_model(original_model)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
