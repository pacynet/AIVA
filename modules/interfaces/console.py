import asyncio
import logging
import os
import random
import sys

logger = logging.getLogger(__name__)

class C:
    """ANSI terminal color codes and formatting."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    CL = '\033[2K\r'  # Clear line and return
    HC = '\033[?25l'  # Hide cursor
    SC = '\033[?25h'  # Show cursor

BANNER = f"""{C.GRAY}╔══════════════════════════════════════╗{C.RESET}
{C.GRAY}║{C.RESET}      {C.BOLD}█████╗ ██╗██╗   ██╗ █████╗{C.RESET}{C.GRAY}      ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██╔══██╗██║██║   ██║██╔══██╗{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}███████║██║██║   ██║███████║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██╔══██║██║╚██╗ ██╔╝██╔══██║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██║  ██║██║ ╚████╔╝ ██║  ██║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}                                      {C.GRAY}║{C.RESET}
{C.GRAY}║{C.RESET}    {C.BLUE}AI Virtual Assistant - v1.0.0{C.RESET}     {C.GRAY}║{C.RESET}
{C.GRAY}╚══════════════════════════════════════╝{C.RESET}
{C.GRAY}Type /help for commands{C.RESET}
"""

THINKING_MESSAGES = [
    "Computing the meaning of life...",
    "Consulting with the digital ghosts...",
    "Brewing some fresh ideas...",
    "Untangling the cosmic wires...",
    "Asking the silicon gods for advice...",
    "Reticulating splines...",
    "Mining for brilliant thoughts...",
    "Warming up the thinking caps...",
    "Generating witty remarks...",
    "Engaging quantum brain...",
]

class Console:
    """
    Interactive console interface for AIVA.
    """

    def __init__(self, router):
        """
        Initialize console with a message router.
        """
        self.router = router
        self.running = True
        self.dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    async def _thinking_animation(self, stop_event):
        """
        Displays a thinking animation until the stop_event is set.
        """
        message = random.choice(THINKING_MESSAGES)
        i = 0
        while not stop_event.is_set():
            print(f"{C.CL}{C.BLUE}{self.dots[i % len(self.dots)]}{C.RESET} {message}{C.HC}", end="", flush=True)
            await asyncio.sleep(0.1)
            i += 1
        print(f"{C.CL}{C.SC}", end="", flush=True)


    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)

    async def run(self) -> None:
        """
        Main loop for the console interface.
        """
        self.clear_screen()

        while self.running:
            # Inlined _get_user_input()
            loop = asyncio.get_running_loop()
            try:
                user_input = await loop.run_in_executor(None, lambda: input(">> "))
            except (KeyboardInterrupt, EOFError):
                self.running = False
                user_input = "/quit"

            if not user_input.strip():
                continue

            stop_event = asyncio.Event()
            thinking_task = asyncio.create_task(self._thinking_animation(stop_event))

            try:
                result = await self.router.process(user_input)

                if user_input.strip().lower() == '/clear':
                    self.clear_screen()
                    if result.get('response'):
                        print(f"{C.GREEN}✓{C.RESET} {result['response']}")
                    continue

                # Inlined _handle_response()
                if result.get('action') == 'quit':
                    self.running = False
                    print("\nGoodbye!")
                    continue

                if result.get('error'):
                    logger.error(f"Router error: {result['error']}")
                elif result.get('response'):
                    print(f"{C.CL}{C.BLUE}\n─ AIVA ─────────────────────────────────{C.RESET}")
                    print(f"{result['response']}")
                    print(f"{C.BLUE}────────────────────────────────────────\n{C.RESET}")

            except Exception as e:
                logger.critical(f"Unhandled error in console loop: {e}", exc_info=True)
                self.running = False
            finally:
                stop_event.set()
                await thinking_task


        logger.info("Console interface shutting down.")
