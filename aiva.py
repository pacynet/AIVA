"""
AIVA (AI Virtual Assistant) - Main Application Module
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from modules.ai import AIManager
from modules.router import Router
from modules.interfaces.console import Console
from framework.config import Config

logger = logging.getLogger(__name__)

class AIVA:
    """Main AIVA application controller."""

    def __init__(self):
        """Initialize AIVA."""
        # Config must be initialized first to get the log directory path
        self.config = Config()

        log_dir = self.config.log_dir
        log_file = log_dir / 'aiva.log'

        file_handler = RotatingFileHandler(
            log_file, maxBytes=1024 * 1024 * 5, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        root_logger.addHandler(file_handler)

        # Suppress noisy third-party library logs
        for logger_name in ['asyncio', 'httpx', 'aiohttp']:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        self.ai_manager: Optional[AIManager] = None

    async def run(self) -> None:
        """Main application runtime loop."""
        try:
            self.ai_manager = AIManager(self.config)
            await self.ai_manager.initialize()

            logger.info(f"Initialized AI providers: {self.ai_manager.list_providers()}")
            logger.info(f"Default provider: {self.ai_manager.current}")

            router = Router(self.ai_manager, self.config)
            console = Console(router)
            await console.run()

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Application interrupted.")
        except Exception as e:
            logger.critical(f"Fatal error: {e}", exc_info=True)
        finally:
            if self.ai_manager:
                await self.ai_manager.cleanup()
            logger.info("Shutdown complete.")


if __name__ == "__main__":
    app = AIVA()
    asyncio.run(app.run())