"""Logging configuration and setup for AIVA.

Provides centralized logging configuration with file output and customizable
log levels. Manages log directory creation and suppresses noisy third-party library logs.
"""

import logging
from pathlib import Path
from framework.constants import PATHS

def setup_logger(level="INFO"):
    """Configure application logging with file output.

    Sets up logging configuration with specified level, creates log directory
    if needed, and configures file handler for persistent logging.

    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                    Defaults to "INFO"
    """
    Path(PATHS.LOGS_DIR).mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(PATHS.LOG_FILE)
        ]
    )

    # Suppress noisy libraries
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    # logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)