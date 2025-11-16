"""
Ollama service management utility.

This module provides functionality for:
- Checking Ollama service status
- Automatically starting Ollama if not running
- Handling permission errors gracefully
- Waiting for Ollama to be ready
"""

import logging
import subprocess
import time
import platform
import shutil
from typing import Tuple, Optional
import requests
from core.config import settings

logger = logging.getLogger(__name__)


class OllamaServiceManager:
    """Manager for Ollama service lifecycle operations."""

    def __init__(self, host: Optional[str] = None, timeout: int = 30):
        """
        Initialize Ollama service manager.

        Args:
            host: Ollama server URL (defaults to settings.OLLAMA_HOST)
            timeout: Seconds to wait for Ollama to start (defaults to settings.OLLAMA_STARTUP_TIMEOUT)
        """
        self.host = host or settings.OLLAMA_HOST
        self.timeout = timeout or settings.OLLAMA_STARTUP_TIMEOUT
        self.ollama_binary = self._find_ollama_binary()

    def _find_ollama_binary(self) -> Optional[str]:
        """
        Find the Ollama binary in the system PATH.

        Returns:
            Path to Ollama binary if found, None otherwise
        """
        ollama_path = shutil.which("ollama")
        if ollama_path:
            logger.debug(f"Found Ollama binary at: {ollama_path}")
        else:
            logger.warning("Ollama binary not found in system PATH")
        return ollama_path

    def check_status(self) -> bool:
        """
        Check if Ollama service is running and accessible.

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Ollama is running at {self.host}")
                return True
            else:
                logger.warning(f"Ollama returned unexpected status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.debug(f"Cannot connect to Ollama at {self.host}")
            return False
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout connecting to Ollama at {self.host}")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama status: {e}")
            return False

    def start_service(self) -> Tuple[bool, str]:
        """
        Attempt to start Ollama service.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.ollama_binary:
            return False, "Ollama binary not found in system PATH. Please install Ollama first."

        try:
            logger.info("🚀 Attempting to start Ollama service...")

            # Determine the appropriate command based on OS
            system = platform.system()

            if system == "Darwin":  # macOS
                # Try to start Ollama as a background service
                process = subprocess.Popen(
                    [self.ollama_binary, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Detach from parent process
                )
            elif system == "Linux":
                # On Linux, try to start as a background service
                process = subprocess.Popen(
                    [self.ollama_binary, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
            elif system == "Windows":
                # On Windows, use different approach
                process = subprocess.Popen(
                    [self.ollama_binary, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                return False, f"Unsupported operating system: {system}"

            logger.info(f"Started Ollama process (PID: {process.pid})")

            # Wait for Ollama to become available
            logger.info(f"⏳ Waiting for Ollama to be ready (timeout: {self.timeout}s)...")

            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.check_status():
                    elapsed = time.time() - start_time
                    logger.info(f"✅ Ollama started successfully in {elapsed:.1f}s")
                    return True, f"Ollama started successfully in {elapsed:.1f}s"

                time.sleep(1)

            # Timeout reached
            logger.warning(f"⏰ Timeout waiting for Ollama to start after {self.timeout}s")
            return False, f"Ollama process started but didn't respond within {self.timeout}s. It may still be initializing."

        except PermissionError as e:
            error_msg = f"Permission denied when trying to start Ollama: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except FileNotFoundError as e:
            error_msg = f"Ollama binary not found: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to start Ollama: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def ensure_running(self, auto_start: bool = True) -> Tuple[bool, str]:
        """
        Ensure Ollama is running, optionally starting it if not.

        Args:
            auto_start: Whether to automatically start Ollama if not running

        Returns:
            Tuple of (is_running: bool, message: str)
        """
        # First check if already running
        if self.check_status():
            return True, "Ollama is already running"

        # If not running and auto-start is disabled
        if not auto_start:
            return False, "Ollama is not running. Auto-start is disabled."

        # Try to start Ollama
        logger.info("Ollama is not running. Attempting to start...")
        success, message = self.start_service()

        if not success:
            return False, f"Failed to start Ollama: {message}"

        return True, message

    def get_models(self) -> Tuple[bool, list, str]:
        """
        Get list of available models from Ollama.

        Returns:
            Tuple of (success: bool, models: list, message: str)
        """
        if not self.check_status():
            return False, [], "Ollama is not running"

        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return True, models, f"Found {len(models)} model(s)"
            else:
                return False, [], f"Unexpected response: {response.status_code}"
        except Exception as e:
            return False, [], f"Error fetching models: {e}"


# Global instance for convenience
ollama_service = OllamaServiceManager()


def check_ollama_on_startup() -> Tuple[bool, str]:
    """
    Check Ollama status on application startup.

    This function:
    1. Checks if Ollama is running
    2. Attempts to start it if enabled in settings
    3. Returns status and user-friendly message

    Returns:
        Tuple of (is_available: bool, message: str)
    """
    logger.info("🔍 Checking Ollama service status...")

    # Check current status
    is_running = ollama_service.check_status()

    if is_running:
        # Check for available models
        success, models, msg = ollama_service.get_models()
        if success and len(models) > 0:
            model_names = [m.get('name', 'unknown') for m in models[:3]]
            return True, f"Ollama is running with {len(models)} model(s): {', '.join(model_names)}"
        elif success and len(models) == 0:
            return True, "Ollama is running but no models are installed. Run 'ollama pull llama3.2' to install a model."
        else:
            return True, "Ollama is running"

    # Ollama is not running - try to start if enabled
    if settings.OLLAMA_AUTO_START:
        logger.info("🚀 Ollama auto-start is enabled. Attempting to start Ollama...")
        success, message = ollama_service.start_service()

        if success:
            # Verify models are available
            has_models, models, _ = ollama_service.get_models()
            if has_models and len(models) == 0:
                return True, f"{message} Note: No models installed. Run 'ollama pull llama3.2' to install a model."
            return True, message
        else:
            return False, f"Failed to auto-start Ollama: {message}. Please start it manually with 'ollama serve'"
    else:
        return False, "Ollama is not running. Please start it with 'ollama serve' or enable auto-start in settings."
