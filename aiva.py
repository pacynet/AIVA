"""
AIVA (AI Virtual Assistant) - Main Application Module

This is the main entry point for the AIVA project, an AI-powered virtual assistant
that supports multiple interfaces (console, Telegram) and AI providers.
"""

import asyncio
import os
import signal
import logging
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Import core modules
from modules.ai import AIManager
from modules.router import Router
from modules.interfaces.console import Console
from modules.interfaces.telegram_bot import TelegramBot

# File paths
PATHS = {
    'CONFIG_DIR': './config',
    'LOGS_DIR': './logs',
    'ENV_FILE': './config/.env',
    'CONFIG_FILE': './config/settings.json',
    'PROMPT_FILE': './config/system_prompt.txt',
    'LOG_FILE': './logs/aiva.log'
}

# Configuration defaults
DEFAULT_CONFIG = {
    "default_ai": "ollama",
    "ai": {
        "openai": {"model": "gpt-4o-mini", "temperature": 0.7},
        "gemini": {"model": "gemini-2.5-pro", "temperature": 0.7},
        "ollama": {"model": "llama3.2", "temperature": 0.7}
    }
}

DEFAULT_SYSTEM_PROMPT = """You are AIVA, a helpful AI assistant.
You can use tools to perform actions. When you need to use a tool, respond with a JSON object in the following format. Do not add any other text outside the JSON block.

{
  "tool": "tool_name",
  "args": {
    "arg_name1": "value1",
    "arg_name2": "value2"
  }
}

Here are the available tools:
- `bash`: Executes a shell command.
  - `cmd` (str): The command to execute.
- `read_file`: Reads the content of a file.
  - `path` (str): The path to the file.
- `write_file`: Writes content to a file.
  - `path` (str): The path to the file.
  - `content` (str): The content to write.
- `list_dir`: Lists files in a directory.
  - `path` (str): The directory path.
  - `recursive` (bool): Whether to list recursively.
- `read_csv`: Reads data from a CSV file.
  - `path` (str): The path to the CSV file.
- `write_csv`: Writes data to a CSV file.
  - `path` (str): The path to the CSV file.
  - `data` (list): The data to write.
- `gmail_list`: Lists recent emails from a Gmail account.
  - `max_results` (int): The maximum number of emails to return.
- `gmail_send`: Sends an email.
  - `to` (str): The recipient's email address.
  - `subject` (str): The email subject.
  - `body` (str): The email body."""

MAX_HISTORY = 20

def setup_logger(level="INFO"):
    """Configure application logging with file output."""
    Path(PATHS['LOGS_DIR']).mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(PATHS['LOG_FILE'])
        ]
    )

    # Suppress noisy third-party library logs
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

class Config:
    """Manages application configuration including API keys, settings, and prompts."""

    def __init__(self):
        self.config_dir = Path(PATHS['CONFIG_DIR'])
        self.config_dir.mkdir(exist_ok=True)

        self._load_env()
        self._load_config()
        self._load_prompt()

    def _load_env(self):
        """Load environment variables from .env file or create default one."""
        env_file = Path(PATHS['ENV_FILE'])
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

        # Google API credentials paths (relative to config directory)
        creds_file = os.getenv("GOOGLE_CREDENTIALS", "credentials.json")
        token_file = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

        # Remove config/ prefix if present and resolve to config directory
        self.google_creds = self.config_dir / Path(creds_file).name
        self.google_token = self.config_dir / Path(token_file).name

    def _load_config(self):
        """Load application configuration from JSON file or create default."""
        config_file = Path(PATHS['CONFIG_FILE'])

        if config_file.exists():
            self.config = json.loads(config_file.read_text())
        else:
            self.config = DEFAULT_CONFIG
            self.save()

    def _load_prompt(self):
        """Load system prompt from file or create default."""
        prompt_file = Path(PATHS['PROMPT_FILE'])
        if not prompt_file.exists():
            prompt_file.write_text(DEFAULT_SYSTEM_PROMPT)
        self.system_prompt = prompt_file.read_text()

    def save(self):
        """Save current configuration to file."""
        Path(PATHS['CONFIG_FILE']).write_text(json.dumps(self.config, indent=2))

    @property
    def default_ai(self):
        return self.config["default_ai"]

    @property
    def telegram_enabled(self):
        return bool(self.telegram_token)

    def get_ai_config(self, provider):
        """Get configuration for specified AI provider."""
        cfg = self.config["ai"].get(provider, {}).copy()
        cfg["system_prompt"] = self.system_prompt
        return cfg

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Windows-specific UTF-8 encoding setup for proper Korean text display
if sys.platform == 'win32':
    import io
    os.environ['PYTHONIOENCODING'] = 'utf-8'  # Set UTF-8 encoding
    # Wrap stdout/stderr with UTF-8 codec for Unicode character support
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system('chcp 65001 > nul')  # Set console code page to UTF-8


class AIVA:
    """
    Main AIVA application class that coordinates all components.

    This class manages the lifecycle of the AI virtual assistant, including:
    - Configuration management
    - AI provider initialization
    - Interface management (console, Telegram)
    - Graceful shutdown handling
    """

    def __init__(self):
        """Initialize AIVA with logger setup and configuration loading."""
        setup_logger()
        self.config = Config()
        self.running = True

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.running = False

    async def _run_telegram_safely(self, router):
        """
        Safely start Telegram bot interface with error handling.

        Args:
            router: Router instance for handling messages
        """
        try:
            logger.info("Attempting to start Telegram bot...")
            telegram = TelegramBot(router, self.config)
            await telegram.run()
        except Exception as e:
            logger.warning(f"Failed to start Telegram bot: {e}. Continuing without Telegram interface.")

    async def run(self):
        """
        Main application runtime loop.

        Sets up signal handlers, initializes all components, and starts
        the available interfaces (console and optionally Telegram).
        """
        # Set up graceful shutdown signal handlers (SIGTERM not supported on Windows)
        signal.signal(signal.SIGINT, self.signal_handler)
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self.signal_handler)

        ai_manager = None

        try:
            # Initialize AI manager with configured providers
            ai_manager = AIManager(self.config)
            await ai_manager.initialize()

            # Create message router
            router = Router(ai_manager, self.config)

            # Start available interfaces
            tasks = []

            # Always start console interface
            console = Console(router)
            tasks.append(asyncio.create_task(console.run()))

            # Start Telegram interface if enabled
            if self.config.telegram_enabled:
                tasks.append(asyncio.create_task(self._run_telegram_safely(router)))

            # Run all interfaces concurrently
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            raise
        finally:
            # Cleanup resources
            if ai_manager:
                await ai_manager.cleanup()
            self.config.save()


if __name__ == "__main__":
    """Entry point when running as main module."""
    app = AIVA()
    asyncio.run(app.run())