"""
Ollama API Client for Music DLP.

This module provides a client for communicating with the local Ollama instance
to generate clean titles from messy YouTube metadata.

The client handles:
- Connection management
- Model availability checking
- Chat API requests
- Error handling and retries
- Response parsing
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
import requests


class OllamaClient:
    """
    Client for interacting with the Ollama API.

    This class provides methods to:
    - Check if Ollama is running
    - List available models
    - Generate chat completions
    - Parse JSON responses from models

    Attributes:
        base_url (str): The Ollama API base URL (default: http://localhost:11434)
        timeout (int): Request timeout in seconds (default: 60)
        logger: Logger instance for this client
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60, auto_unload: bool = True):
        """
        Initialize the Ollama client.

        Args:
            base_url: The Ollama API base URL
            timeout: Request timeout in seconds
            auto_unload: If True, unload models from VRAM immediately after use (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.auto_unload = auto_unload
        self.logger = logging.getLogger('music_dlp.ai.ollama_client')

        self.logger.info(f"Initialized OllamaClient with base_url={self.base_url}, auto_unload={auto_unload}")

    def is_available(self) -> bool:
        """
        Check if Ollama is running and accessible.

        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            self.logger.info("Ollama is available")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama is not available: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        List all available models in Ollama.

        Returns:
            List of model names (e.g., ['gemma3:12b', 'qwen3:14b'])
            Empty list if request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            models = [model['name'] for model in data.get('models', [])]

            self.logger.info(f"Found {len(models)} available models: {models}")
            return models

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to list models: {e}")
            return []
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse model list response: {e}")
            return []

    def model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model_name: Name of the model to check (e.g., 'gemma3:12b')

        Returns:
            True if the model is available, False otherwise
        """
        models = self.list_models()
        exists = model_name in models

        if exists:
            self.logger.debug(f"Model '{model_name}' is available")
        else:
            self.logger.warning(f"Model '{model_name}' is not available")

        return exists

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        format: str = "json",
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a chat request to Ollama.

        Args:
            model: The model name to use (e.g., 'gemma3:12b')
            messages: List of message dicts with 'role' and 'content' keys
                      Example: [
                          {'role': 'system', 'content': 'You are a helpful assistant'},
                          {'role': 'user', 'content': 'Hello'}
                      ]
            format: Response format ('json' or empty string for text)
            options: Optional model parameters (temperature, top_p, etc.)
            keep_alive: How long to keep model in VRAM after use
                       Examples: "5m" (5 minutes), "30s" (30 seconds), "0" (unload immediately)
                       If None and auto_unload=True, defaults to "0"

        Returns:
            Response dict containing:
                - 'model': The model that generated the response
                - 'message': The response message dict with 'role' and 'content'
                - 'done': Boolean indicating if generation is complete
                - 'total_duration': Total time in nanoseconds
            Returns None if the request fails
        """
        if not self.model_exists(model):
            self.logger.error(f"Cannot chat: model '{model}' not available")
            return None

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": False  # We want the complete response at once
        }

        if format == "json":
            payload["format"] = "json"

        if options:
            payload["options"] = options

        # Set keep_alive to unload model from VRAM after use
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        elif self.auto_unload:
            payload["keep_alive"] = "0"  # Unload immediately after response

        max_attempts = 2  # Original attempt + 1 retry on timeout
        for attempt_num in range(1, max_attempts + 1):
            current_timeout = self.timeout if attempt_num == 1 else self.timeout * 2

            try:
                self.logger.debug(f"Sending chat request to model '{model}' (attempt {attempt_num}, timeout={current_timeout}s)")
                start_time = time.time()

                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=current_timeout
                )
                response.raise_for_status()

                elapsed = time.time() - start_time
                result = response.json()

                if self.auto_unload:
                    self.logger.info(f"Chat request completed in {elapsed:.2f}s (model will be unloaded from VRAM)")
                else:
                    self.logger.info(f"Chat request completed in {elapsed:.2f}s")
                return result

            except requests.exceptions.Timeout:
                if attempt_num < max_attempts:
                    self.logger.warning(
                        f"Chat request timed out after {current_timeout}s, "
                        f"retrying with {current_timeout * 2}s timeout..."
                    )
                    continue
                self.logger.error(f"Chat request timed out after {current_timeout}s (no more retries)")
                return None
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Chat request failed: {e}")
                return None
            except ValueError as e:
                self.logger.error(f"Failed to parse chat response as JSON: {e}")
                return None

        return None

    def generate_title(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        keep_alive: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a clean title using an Ollama model.

        This is a convenience method specifically for title generation.

        Args:
            model: The model name to use
            system_prompt: The system prompt defining the task
            user_prompt: The user prompt with the messy title
            temperature: Model temperature (0.0-1.0, higher = more creative)
            keep_alive: How long to keep model in VRAM (if None, uses auto_unload setting)

        Returns:
            Parsed JSON response from the model containing:
                - title: Clean song title
                - artist: Artist name
                - tags: List of tags
                - confidence: Confidence score (0.0-1.0)
            Returns None if generation fails
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        options = {
            "temperature": temperature,
            "top_p": 0.9
        }

        try:
            response = self.chat(
                model=model,
                messages=messages,
                format="json",
                options=options,
                keep_alive=keep_alive
            )

            if not response:
                return None

            # Extract the content from the response
            content = response.get('message', {}).get('content', '')

            if not content:
                self.logger.error("Empty content in response")
                return None

            # Parse the JSON content
            result = json.loads(content)

            # Validate the response has required fields
            required_fields = ['title', 'artist', 'tags', 'confidence']
            if not all(field in result for field in required_fields):
                self.logger.warning(
                    f"Response missing required fields. Got: {list(result.keys())}"
                )

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse model response as JSON: {e}")
            self.logger.debug(f"Raw content: {content if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in generate_title: {e}")
            return None

    def batch_generate(
        self,
        model: str,
        system_prompt: str,
        user_prompts: List[str],
        temperature: float = 0.7,
        progress_callback: Optional[callable] = None,
        keep_loaded: bool = False
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Generate titles for multiple prompts sequentially.

        Note: This processes prompts one at a time. For parallel processing
        across multiple models, use TitleProcessor instead.

        Args:
            model: The model name to use
            system_prompt: The system prompt defining the task
            user_prompts: List of user prompts to process
            temperature: Model temperature (0.0-1.0)
            progress_callback: Optional callback function(current, total)
            keep_loaded: If True, keep model in VRAM during batch (faster)
                        If False, unload after each request (saves VRAM)

        Returns:
            List of parsed responses (None for failed requests)
        """
        results = []
        total = len(user_prompts)

        self.logger.info(f"Starting batch generation of {total} prompts with model '{model}'")
        if keep_loaded:
            self.logger.info("Keeping model loaded in VRAM for batch processing")

        for i, prompt in enumerate(user_prompts, 1):
            if progress_callback:
                progress_callback(i, total)

            # For batch processing, keep model loaded until the last request
            if keep_loaded and i < total:
                keep_alive = "5m"  # Keep loaded between requests
            else:
                keep_alive = None  # Use default (auto_unload setting)

            result = self.generate_title(
                model=model,
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=temperature,
                keep_alive=keep_alive
            )
            results.append(result)

            # Small delay between requests to avoid overwhelming Ollama
            if i < total:
                time.sleep(0.1)

        success_count = sum(1 for r in results if r is not None)
        self.logger.info(f"Batch generation complete: {success_count}/{total} successful")

        return results

    def unload_model(self, model: str) -> bool:
        """
        Manually unload a model from VRAM.

        This sends a request with keep_alive=0 to force unload.

        Args:
            model: The model name to unload

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Unloading model '{model}' from VRAM...")

            # Send a minimal request with keep_alive=0 to unload
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": "",
                    "keep_alive": "0"
                },
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Model '{model}' unloaded successfully")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to unload model '{model}': {e}")
            return False

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.

        Args:
            model: The model name to query

        Returns:
            Model information dict or None if request fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model},
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            self.logger.debug(f"Retrieved info for model '{model}'")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get model info for '{model}': {e}")
            return None
        except ValueError as e:
            self.logger.error(f"Failed to parse model info response: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    # Set up basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create client
    client = OllamaClient()

    # Check if Ollama is available
    print(f"Ollama available: {client.is_available()}")

    # List models
    models = client.list_models()
    print(f"Available models: {models}")

    # Check specific models
    for model in ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']:
        exists = client.model_exists(model)
        print(f"Model '{model}' exists: {exists}")

    # Test title generation (if models are available)
    if models:
        test_model = models[0]

        system_prompt = "You are a music metadata expert. Extract clean titles from messy YouTube titles. Respond in JSON format with fields: title, artist, tags (array), confidence (0.0-1.0)."
        user_prompt = "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】"

        print(f"\nTesting title generation with {test_model}...")
        result = client.generate_title(
            model=test_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        if result:
            print(f"Generated title: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("Title generation failed")
