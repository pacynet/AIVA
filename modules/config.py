"""Configuration management module for AIVA."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from framework.constants import PATHS, CONFIG


class Config:
    """Manages application configuration including API keys, settings, and prompts."""

    def __init__(self):
        self.config_dir = Path(PATHS.CONFIG_DIR)
        self.config_dir.mkdir(exist_ok=True)

        self._load_env()
        self._load_config()
        self._load_prompt()

    def _load_env(self):
        """Load environment variables from .env file or create default one."""
        env_file = Path(PATHS.ENV_FILE)
        if not env_file.exists():
            env_file.write_text("""
OPENAI_API_KEY=
GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=
OLLAMA_HOST=http://localhost:11434
GOOGLE_CREDENTIALS=credentials.json
GOOGLE_TOKEN_PATH=token.json
""")
        load_dotenv(env_file)

        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.google_creds = self.config_dir / os.getenv("GOOGLE_CREDENTIALS", "credentials.json").replace("config/", "")
        self.google_token = self.config_dir / os.getenv("GOOGLE_TOKEN_PATH", "token.json").replace("config/", "")

    def _load_config(self):
        """Load application configuration from JSON file or create default."""
        config_file = Path(PATHS.CONFIG_FILE)

        if config_file.exists():
            self.config = json.loads(config_file.read_text())
        else:
            self.config = CONFIG.DEFAULT_CONFIG
            self.save()

    def _load_prompt(self):
        """Load system prompt from file or create default."""
        prompt_file = Path(PATHS.PROMPT_FILE)
        if not prompt_file.exists():
            prompt_file.write_text(CONFIG.DEFAULT_SYSTEM_PROMPT)
        self.system_prompt = prompt_file.read_text()

    def save(self):
        """Save current configuration to file."""
        Path(PATHS.CONFIG_FILE).write_text(json.dumps(self.config, indent=2))

    @property
    def default_ai(self):
        return self.config["default_ai"]

    @property
    def telegram_enabled(self):
        return bool(self.telegram_token)

    def get_ai_config(self, provider):
        """Get configuration for specified AI provider.

        Args:
            provider: Name of the AI provider (openai, gemini, ollama)

        Returns:
            dict: Configuration including model, temperature, and system prompt
        """
        cfg = self.config["ai"].get(provider, {}).copy()
        cfg["system_prompt"] = self.system_prompt
        return cfg