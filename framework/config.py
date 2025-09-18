"""
AIVA (AI Virtual Assistant) - Configuration Module
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Any

from appdirs import user_config_dir, user_data_dir
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ================== Constants ==================
APP_NAME = "AIVA"
APP_AUTHOR = "AIVA-Team"

DEFAULT_CONFIG = {
    "default_ai": "ollama",
    "model": {
        "openai": {"model": "gpt-4o-mini", "temperature": 0.7},
        "gemini": {"model": "gemini-2.5-pro", "temperature": 0.7},
        "ollama": {"model": "llama3.2", "temperature": 0.7}
    }
}

DEFAULT_ENV_CONFIG = {
    "OPENAI_API_KEY": "NONE",
    "GEMINI_API_KEY": "NONE",
    "OLLAMA_HOST": "http://localhost:11434"
}

DEFAULT_PROMPT = """You are AIVA, a helpful AI assistant.

IMPORTANT: Only use tools when the user specifically requests an action that requires them.
Always respond with regular text unless a tool is absolutely necessary.

Available tools (use JSON format only when needed):
- bash: {"tool": "bash", "args": {"cmd": "command"}}
- read_file: {"tool": "read_file", "args": {"path": "file_path"}}
- write_file: {"tool": "write_file", "args": {"path": "file_path", "content": "text"}}
- list_dir: {"tool": "list_dir", "args": {"path": "directory_path", "recursive": false}}
- read_csv: {"tool": "read_csv", "args": {"path": "file_path"}}
- write_csv: {"tool": "write_csv", "args": {"path": "file_path", "data": [["row1"], ["row2"]]}}

IMPORTANT: Always use the exact parameter names shown above (path, content, cmd, data, recursive).

For general conversation, questions, or explanations, respond normally with text."""

# ================== Main Config Class ==================
class Config:
    """AIVA Configuration Manager"""

    def __init__(self):
        # Setup paths
        self.config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
        self.data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))

        self.env_file = self.config_dir / '.env'
        self.config_file = self.config_dir / 'settings.json'
        self.prompt_file = self.config_dir / 'system_prompt.txt'
        self.log_dir = self.data_dir / 'logs'

        # Initialize
        self._setup()

    def _setup(self):
        """Initialize configuration environment"""
        # Create directories
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load environment
        self._load_env()

        # Load config
        self.config = self._load_json(self.config_file, DEFAULT_CONFIG)

        # Load prompt
        self.system_prompt = self._load_text(self.prompt_file, DEFAULT_PROMPT)

        # Ensure Ollama
        self._setup_ollama()

    def _load_env(self):
        """Load environment variables"""
        load_dotenv(self.env_file)

        # Create .env if missing
        if not self.env_file.exists():
            with open(self.env_file, 'w') as f:
                for k, v in DEFAULT_ENV_CONFIG.items():
                    f.write(f'{k}="{v}"\n')

        # Load API keys
        self.openai_key = os.getenv("OPENAI_API_KEY", "NONE")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "NONE")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _load_json(self, path: Path, default: Dict) -> Dict:
        """Load or create JSON file"""
        if not path.exists():
            with open(path, 'w') as f:
                json.dump(default, f, indent=2)
            return default.copy()

        with open(path, 'r') as f:
            return json.load(f)

    def _load_text(self, path: Path, default: str) -> str:
        """Load or create text file"""
        if not path.exists():
            path.write_text(default)
            return default

        return path.read_text()

    def _setup_ollama(self):
        """Install Ollama and pull model if needed"""
        model = self.config.get("model", {}).get("ollama", {}).get("model", "llama3.2")

        # Check if Ollama installed
        if not shutil.which("ollama"):
            if sys.platform == "win32":
                try:
                    # Download and install
                    url = "https://ollama.com/download/OllamaSetup.exe"
                    installer = "OllamaSetup.exe"
                    urllib.request.urlretrieve(url, installer)
                    subprocess.run([installer, "/S"], check=True)
                    os.remove(installer)
                    logger.info("Ollama installed")
                except:
                    logger.warning("Failed to install Ollama automatically")
            else:
                logger.info("Please install Ollama manually: https://ollama.com/download")
                return

        # Check if model exists
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if model not in result.stdout:
                logger.info(f"Pulling {model}...")
                subprocess.run(["ollama", "pull", model], check=True)
        except:
            pass

    @property
    def default_ai(self) -> str:
        """Get default AI provider"""
        return self.config.get("default_ai", "ollama")

    def get_ai_config(self, provider: str) -> Dict[str, Any]:
        """Get AI provider configuration"""
        cfg = self.config["model"].get(provider, {}).copy()
        cfg["system_prompt"] = self.system_prompt

        # Add API keys
        if provider == "openai":
            cfg["api_key"] = self.openai_key
        elif provider == "gemini":
            cfg["api_key"] = self.gemini_key
        elif provider == "ollama":
            cfg["host"] = self.ollama_host

        return cfg

    def update_provider(self, provider: str):
        """Change default AI provider"""
        if provider in self.config["model"]:
            self.config["default_ai"] = provider
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
