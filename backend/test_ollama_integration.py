"""
Test script for Ollama integration.

Tests:
1. Connection to Ollama server
2. Listing available models
3. Getting model information
4. Basic text generation
5. Streaming text generation
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm import ollama_client, OllamaClientError


async def test_connection():
    """Test connection to Ollama server"""
    print("\n" + "=" * 60)
    print("TEST 1: Connection Test")
    print("=" * 60)

    try:
        connected = await ollama_client.check_connection()
        if connected:
            print("✓ Successfully connected to Ollama")
            return True
        else:
            print("✗ Failed to connect to Ollama")
            return False
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
        return False


async def test_list_models():
    """Test listing available models"""
    print("\n" + "=" * 60)
    print("TEST 2: List Models")
    print("=" * 60)

    try:
        models = await ollama_client.list_models()
        print(f"✓ Found {len(models)} models:")
        for i, model in enumerate(models, 1):
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            size_mb = size / (1024 * 1024) if size else 0
            print(f"  {i}. {name} ({size_mb:.2f} MB)")
        return True
    except OllamaClientError as e:
        print(f"✗ Failed to list models: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


async def test_model_info():
    """Test getting model information"""
    print("\n" + "=" * 60)
    print("TEST 3: Get Model Info")
    print("=" * 60)

    try:
        model_name = ollama_client.default_model
        print(f"Getting info for: {model_name}")

        info = await ollama_client.get_model_info(model_name)
        print(f"✓ Retrieved model info:")
        print(f"  Model: {info.get('modelfile', 'N/A')[:100]}...")
        return True
    except OllamaClientError as e:
        print(f"✗ Failed to get model info: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


async def test_generate():
    """Test basic text generation"""
    print("\n" + "=" * 60)
    print("TEST 4: Basic Text Generation")
    print("=" * 60)

    try:
        prompt = "What is the capital of France? Answer in one sentence."
        print(f"Prompt: {prompt}")
        print("Generating...")

        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=50
        )

        print(f"✓ Response: {response}")
        return True
    except OllamaClientError as e:
        print(f"✗ Generation failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False


async def test_streaming():
    """Test streaming text generation"""
    print("\n" + "=" * 60)
    print("TEST 5: Streaming Text Generation")
    print("=" * 60)

    try:
        prompt = "Count from 1 to 5, one number per line."
        print(f"Prompt: {prompt}")
        print("Streaming response: ", end="", flush=True)

        chunks = []
        async for chunk in ollama_client.generate_stream(
            prompt=prompt,
            temperature=0.7,
            max_tokens=50
        ):
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        print()  # New line after streaming
        if chunks:
            print(f"✓ Received {len(chunks)} chunks")
            return True
        else:
            print("✗ No chunks received")
            return False

    except OllamaClientError as e:
        print(f"\n✗ Streaming failed: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        return False


async def test_model_switching():
    """Test model switching"""
    print("\n" + "=" * 60)
    print("TEST 6: Model Switching")
    print("=" * 60)

    try:
        original_model = ollama_client.default_model
        print(f"Original model: {original_model}")

        # Get list of models to switch to
        models = await ollama_client.list_models()
        if len(models) < 1:
            print("✗ No models available for switching test")
            return False

        # Switch to first available model (might be the same)
        test_model = models[0].get('name')
        print(f"Switching to: {test_model}")
        ollama_client.switch_model(test_model)
        print(f"New default model: {ollama_client.default_model}")

        # Switch back
        ollama_client.switch_model(original_model)
        print(f"Switched back to: {ollama_client.default_model}")
        print("✓ Model switching successful")
        return True

    except Exception as e:
        print(f"✗ Model switching failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OLLAMA INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Host: {ollama_client.host}")
    print(f"Default Model: {ollama_client.default_model}")

    results = []

    # Run tests
    results.append(("Connection", await test_connection()))

    if results[0][1]:  # Only continue if connected
        results.append(("List Models", await test_list_models()))
        results.append(("Model Info", await test_model_info()))
        results.append(("Text Generation", await test_generate()))
        results.append(("Streaming", await test_streaming()))
        results.append(("Model Switching", await test_model_switching()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
