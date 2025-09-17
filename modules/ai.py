"""AI provider management module for AIVA."""

import asyncio
import aiohttp
import logging
from typing import List, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, name, config):
        self.name = name
        self.config = config

    @abstractmethod
    async def generate(self, message: str, history: List[Dict] = None) -> str:
        """Generate response from AI provider.

        Args:
            message: User message to process
            history: Optional conversation history

        Returns:
            Generated response string
        """
        pass

class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self, api_key, config):
        super().__init__("openai", config)
        self.api_key = api_key

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        """Generate response using OpenAI API."""
        import openai
        client = openai.AsyncOpenAI(api_key=self.api_key)

        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=self.config.get("model", "gpt-4o-mini"),
            messages=messages,
            temperature=self.config.get("temperature", 0.7)
        )
        return response.choices[0].message.content

class GeminiProvider(AIProvider):
    def __init__(self, api_key, config):
        super().__init__("gemini", config)
        self.api_key = api_key

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(
            self.config.get("model", "gemini-2.5-pro"),
            system_instruction=self.config.get("system_prompt")
        )

        response = await asyncio.get_event_loop().run_in_executor(None, model.generate_content, message)
        return response.text

class OllamaProvider(AIProvider):
    def __init__(self, host, config):
        super().__init__("ollama", config)
        self.host = host
        self.session = aiohttp.ClientSession()

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        async with self.session.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.config.get("model", "llama3.2"),
                    "messages": messages,
                    "stream": False
                }
        ) as resp:
            data = await resp.json()
            try:
                return data["message"]["content"]
            except KeyError:
                logger.error(f"Ollama ERROR: {data}")
                raise

    async def cleanup(self):
        await self.session.close()

class AIManager:
    def __init__(self, config):
        self.config = config
        self.providers = {}
        self.current = None

    async def initialize(self):
        if self.config.openai_key:
            self.providers["openai"] = OpenAIProvider(
                self.config.openai_key,
                self.config.get_ai_config("openai")
            )

        if self.config.gemini_key:
            self.providers["gemini"] = GeminiProvider(
                self.config.gemini_key,
                self.config.get_ai_config("gemini")
            )

        self.providers["ollama"] = OllamaProvider(
            self.config.ollama_host,
            self.config.get_ai_config("ollama")
        )

        self.current = self.config.default_ai
        if self.current not in self.providers and self.providers:
            self.current = list(self.providers.keys())[0]

    async def generate(self, message: str, provider: str = None, history: List[Dict] = None) -> str:
        provider = provider or self.current
        if provider not in self.providers:
            raise Exception(f"Provider {provider} not available")
        return await self.providers[provider].generate(message, history)

    def switch_provider(self, provider: str):
        if provider in self.providers:
            self.current = provider
            return True
        return False

    def list_providers(self):
        return list(self.providers.keys())

    async def cleanup(self):
        for provider in self.providers.values():
            if hasattr(provider, 'cleanup'):
                await provider.cleanup()