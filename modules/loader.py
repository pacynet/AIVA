"""Loading animation module for AIVA.

Provides animated loading indicators with customizable messages and spinner animations
to enhance user experience during processing operations.
"""

import asyncio
import random
from framework.constants import Color as C, MSG

class Loader:
    """Animated loading indicator with spinner and customizable messages.

    Provides a non-blocking loading animation that displays a rotating spinner
    and cycling messages to indicate processing activity.
    """

    def __init__(self):
        """Initialize the loader with default spinner characters and state."""
        self.loading = False
        self.dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0

    async def start(self, message: str = None):
        """Start the loading animation with optional custom message.

        Args:
            message (str, optional): Custom loading message. If None, a random
                                   message from MSG.LOADER_MSGS is used.
        """
        self.loading = True
        self.message = message or random.choice(MSG.LOADER_MSGS)

        print(f"{C.HC}", end='')  # Hide cursor

        while self.loading:
            spinner = self.dots[self.current % len(self.dots)]
            dots = "." * (1 + (self.current % 3))

            print(f"\r{C.CL}{C.CYAN}{spinner}{C.RESET} {self.message}{dots}", end='', flush=True)

            self.current += 1
            await asyncio.sleep(0.1)

    def stop(self, success: bool = True, message: str = None):
        """Stop the loading animation and optionally display a completion message.

        Args:
            success (bool): Whether the operation was successful (affects message color)
            message (str, optional): Completion message to display. If None, no message shown.
        """
        self.loading = False
        print(f"\r{C.CL}", end='')

        if message:
            color = C.GREEN if success else C.RED
            print(f"{color}{message}{C.RESET}")

        print(f"{C.SC}", end='')  # Show cursor
