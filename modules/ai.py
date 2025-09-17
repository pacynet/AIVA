"""AI provider management module for AIVA."""

import asyncio
import aiohttp
import logging
from typing import List, Dict
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)



class OpenAIProvider:
    """OpenAI GPT provider implementation."""

    def __init__(self, api_key, config):
        self.name = "openai"
        self.config = config
        self.api_key = api_key

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        """Generate response using OpenAI API."""
        client = openai.AsyncOpenAI(api_key=self.api_key)

        # Build messages array with system prompt, recent history, and current message
        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]
        if history:
            messages.extend(history[-10:])  # Keep only last 10 messages for context
        messages.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=self.config.get("model", "gpt-4o-mini"),
            messages=messages,
            temperature=self.config.get("temperature", 0.7)
        )
        return response.choices[0].message.content

class GeminiProvider:
    def __init__(self, api_key, config):
        self.name = "gemini"
        self.config = config
        self.api_key = api_key

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(
            self.config.get("model", "gemini-2.5-pro"),
            system_instruction=self.config.get("system_prompt")
        )

        # Generate content synchronously (Gemini doesn't have native async support)
        response = await asyncio.get_event_loop().run_in_executor(None, model.generate_content, message)
        return response.text

class OllamaProvider:
    def __init__(self, host, config):
        self.name = "ollama"
        self.config = config
        self.host = host
        self.session = aiohttp.ClientSession()

    async def generate(self, message: str, history: List[Dict] = None) -> str:
        # Build messages for Ollama chat API
        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]
        if history:
            messages.extend(history[-10:])  # Limit context to last 10 messages
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