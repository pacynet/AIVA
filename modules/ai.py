"""
AI provider management module for AIVA.

Provides abstract interface and implementations for various AI providers
including OpenAI, Google Gemini, and Ollama.
"""

import logging
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.

    Defines the interface that all AI providers must implement.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize base AI provider.

        Args:
            name: Provider identifier
            config: Provider-specific configuration
        """
        self.name = name
        self.config = config

    @abstractmethod
    async def generate(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Generate AI response for given message.

        Args:
            message: User message to respond to
            history: Conversation history for context

        Returns:
            Generated response text
        """
        pass

    async def cleanup(self) -> None:
        """
        Cleanup provider resources.

        Default implementation does nothing. Override if cleanup needed.
        """
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            config: Provider configuration including model and temperature
        """
        super().__init__("openai", config)
        self.api_key = api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def generate(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Generate response using OpenAI API.

        Args:
            message: User message
            history: Conversation history

        Returns:
            Generated response text

        Raises:
            openai.APIError: If API call fails
        """
        try:
            # Build message array with system prompt and history
            messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]

            if history:
                # Limit context to last 10 messages to avoid token limits
                messages.extend(history[-10:])

            messages.append({"role": "user", "content": message})

            # Make API call with configured parameters
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=messages,
                temperature=self.config.get("temperature", 0.7)
            )

            return response.choices[0].message.content

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider implementation."""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            config: Provider configuration
        """
        super().__init__("gemini", config)
        self.api_key = api_key
        genai.configure(api_key=api_key)

        # Initialize model with system instruction
        self.model = genai.GenerativeModel(
            self.config.get("model", "gemini-2.0-flash-exp"),
            system_instruction=self.config.get("system_prompt")
        )

    async def generate(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Generate response using Gemini API.

        Since Gemini SDK is synchronous, we run it directly without executor
        for simple text generation (not CPU-bound).

        Args:
            message: User message
            history: Conversation history (currently unused for Gemini)

        Returns:
            Generated response text
        """
        try:
            # Gemini SDK is synchronous, direct call is fine for I/O operation
            response = self.model.generate_content(message)
            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class OllamaProvider(BaseAIProvider):
    """Ollama local AI provider implementation."""

    def __init__(self, host: str, config: Dict[str, Any]):
        """
        Initialize Ollama provider.

        Args:
            host: Ollama server URL
            config: Provider configuration
        """
        super().__init__("ollama", config)
        self.host = host

    async def generate(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Generate response using Ollama API.

        Args:
            message: User message
            history: Conversation history

        Returns:
            Generated response text

        Raises:
            aiohttp.ClientError: If API call fails
        """
        # Build messages array with system prompt and history
        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]

        if history:
            # Limit context to prevent memory issues
            messages.extend(history[-10:])

        messages.append({"role": "user", "content": message})

        # Use context manager for proper session cleanup
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{self.host}/api/chat",
                        json={
                            "model": self.config.get("model", "llama3.2"),
                            "messages": messages,
                            "stream": False,
                            "options": {
                                "temperature": self.config.get("temperature", 0.7)
                            }
                        },
                        timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama API error: {resp.status} - {error_text}")

                    data = await resp.json()

                    # Extract message content from response
                    if "message" in data and "content" in data["message"]:
                        return data["message"]["content"]
                    else:
                        raise KeyError(f"Invalid Ollama response format: {data}")

            except aiohttp.ClientError as e:
                logger.error(f"Ollama connection error: {e}")
                raise
            except Exception as e:
                logger.error(f"Ollama provider error: {e}")
                raise


class ProviderFactory:
    """
    Factory class for creating AI provider instances.

    Implements the Factory pattern for provider instantiation.
    """

    @staticmethod
    def create_provider(provider_type: str, config: Any) -> BaseAIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_type: Type of provider to create
            config: Application configuration object

        Returns:
            Instantiated AI provider

        Raises:
            ValueError: If provider type is unknown or not configured
        """
        # Provider creation mapping
        providers = {
            'openai': lambda: OpenAIProvider(
                config.openai_key,
                config.get_ai_config("openai")
            ),
            'gemini': lambda: GeminiProvider(
                config.gemini_key,
                config.get_ai_config("gemini")
            ),
            'ollama': lambda: OllamaProvider(
                config.ollama_host,
                config.get_ai_config("ollama")
            )
        }

        # Validate provider type
        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")

        # Check if provider is configured
        if provider_type == 'openai' and (not config.openai_key or config.openai_key == "NONE"):
            raise ValueError("OpenAI provider requested but OPENAI_API_KEY not set")

        if provider_type == 'gemini' and (not config.gemini_key or config.gemini_key == "NONE"):
            raise ValueError("Gemini provider requested but GEMINI_API_KEY not set")

        # Create and return provider instance
        return providers[provider_type]()


class AIManager:
    """
    Central manager for AI providers.

    Handles provider initialization, switching, and request routing.
    """

    def __init__(self, config: Any):
        """
        Initialize AI manager.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.providers: Dict[str, BaseAIProvider] = {}
        self.current: Optional[str] = None

    async def initialize(self) -> None:
        """
        Initialize available AI providers based on configuration.

        Creates provider instances for all configured providers.
        """
        factory = ProviderFactory()

        # Try to initialize each provider
        provider_configs = [
            ('openai', self.config.openai_key and self.config.openai_key != "NONE"),
            ('gemini', self.config.gemini_key and self.config.gemini_key != "NONE"),
            ('ollama', True)  # Ollama always available if host is configured
        ]

        for provider_name, is_configured in provider_configs:
            if is_configured:
                try:
                    provider = factory.create_provider(provider_name, self.config)
                    self.providers[provider_name] = provider
                    logger.info(f"Initialized {provider_name} provider")
                except ValueError as e:
                    logger.warning(f"Could not initialize {provider_name}: {e}")
                except Exception as e:
                    logger.error(f"Failed to initialize {provider_name}: {e}")

        # Set current provider
        if not self.providers:
            logger.error("Provider initialization details:")
            logger.error(f"OpenAI key: {'SET' if self.config.openai_key and self.config.openai_key != 'NONE' else 'NOT SET'}")
            logger.error(f"Gemini key: {'SET' if self.config.gemini_key and self.config.gemini_key != 'NONE' else 'NOT SET'}")
            logger.error(f"Ollama host: {self.config.ollama_host}")
            raise RuntimeError("No AI providers could be initialized. Please check your API keys or ensure Ollama is installed.")

        # Use configured default or first available provider
        self.current = self.config.default_ai
        if self.current not in self.providers:
            self.current = list(self.providers.keys())[0]
            logger.warning(f"Default provider '{self.config.default_ai}' not available, using '{self.current}'")

    async def generate(
            self,
            message: str,
            provider: Optional[str] = None,
            history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate AI response using specified or current provider.

        Args:
            message: User message
            provider: Optional provider name (uses current if not specified)
            history: Conversation history

        Returns:
            Generated response text

        Raises:
            ValueError: If provider is not available
            Exception: If generation fails
        """
        provider_name = provider or self.current

        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' is not available")

        try:
            return await self.providers[provider_name].generate(message, history)
        except Exception as e:
            logger.error(f"Generation failed with {provider_name}: {e}")
            raise

    def switch_provider(self, provider: str) -> bool:
        """
        Switch current AI provider.

        Args:
            provider: Name of provider to switch to

        Returns:
            True if switch successful, False otherwise
        """
        if provider in self.providers:
            self.current = provider
            logger.info(f"Switched to {provider} provider")
            return True

        logger.warning(f"Cannot switch to {provider}: not available")
        return False

    def list_providers(self) -> List[str]:
        """
        Get list of available providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    async def cleanup(self) -> None:
        """
        Cleanup all provider resources.

        Calls cleanup method on all initialized providers.
        """
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {provider.name}: {e}")
