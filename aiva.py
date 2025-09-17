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

# Import core modules
from modules.config import Config
from modules.ai import AIManager
from modules.router import Router
from modules.interfaces.console import Console
from modules.interfaces.telegram_bot import TelegramBot
from framework.logger import setup_logger

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Windows-specific UTF-8 encoding setup
if sys.platform == 'win32':
    import io
    # Set UTF-8 encoding environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Wrap stdout/stderr with UTF-8 codec to handle Korean and other Unicode characters
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # Set console code page to UTF-8
    os.system('chcp 65001 > nul')


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
        # Set up graceful shutdown signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
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