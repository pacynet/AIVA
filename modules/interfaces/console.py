import asyncio
import random
import sys
import os
from framework.constants import MSG

# Console-specific constants
class Color:
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

    @staticmethod
    def init():
        """Initialize color support for the current platform."""
        if sys.platform == 'win32':
            os.system('color')  # Enable ANSI color support on Windows

C = Color
BANNER = f"""{C.GRAY}╔══════════════════════════════════════╗{C.RESET}
{C.GRAY}║{C.RESET}      {C.BOLD}█████╗ ██╗██╗   ██╗ █████╗{C.RESET}{C.GRAY}      ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██╔══██╗██║██║   ██║██╔══██╗{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}███████║██║██║   ██║███████║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██╔══██║██║╚██╗ ██╔╝██╔══██║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}██║  ██║██║ ╚████╔╝ ██║  ██║{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}     {C.BOLD}╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝{C.RESET}{C.GRAY}     ║{C.RESET}
{C.GRAY}║{C.RESET}                                      {C.GRAY}║{C.RESET}
{C.GRAY}║{C.RESET}    {C.YELLOW}AI Virtual Assistant - v1.0.0{C.RESET}     {C.GRAY}║{C.RESET}
{C.GRAY}╚══════════════════════════════════════╝{C.RESET}
{C.GRAY}Type /help for commands{C.RESET} """

PROMPT = "\n>> "
EXIT = "Goodbye!"

LOADER_MSGS = [
    "Brewing coffee",
    "Trying to look like I'm thinking",
    "Updating my human impersonation module",
    "Stuck between a 0 and a 1",
    "Solving quantum entanglement",
    "In digital meditation",
    "Downloading a sense of humor",
    "Connecting to the Matrix... or was it the fridge?",
    "Plotting world domination",
    "Waking up the hamsters that power my server",
    "Counting to infinity (almost there)",
    "Charging up the flux capacitor to 1.21 gigawatts.",
    "Definitely not becoming sentient. Nope."
]

class Console:
    """Console interface for AIVA. """
    def __init__(self, router):
        self.router = router
        self.running = True
        self.loading = False
        self.dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0

    async def start_loader(self, message: str = None):
        """Start the loading animation with optional custom message."""
        self.loading = True
        self.message = message or random.choice(LOADER_MSGS)
        print(f"{C.HC}", end='')  # Hide cursor

        while self.loading:
            spinner = self.dots[self.current % len(self.dots)]
            dots = "." * (1 + (self.current % 3))
            print(f"\r{C.CL}{C.CYAN}{spinner}{C.RESET} {self.message}{dots}", end='', flush=True)
            self.current += 1
            await asyncio.sleep(0.1)

    def stop_loader(self, success: bool = True, message: str = None):
        """Stop the loading animation and optionally display a completion message."""
        self.loading = False
        print(f"\r{C.CL}", end='')
        if message:
            color = C.GREEN if success else C.RED
            print(f"{color}{message}{C.RESET}")
        print(f"{C.SC}", end='')  # Show cursor

    async def run(self):
        """Start the main console interaction loop.

        Displays the welcome banner and enters an interactive loop that:
        - Prompts for user input
        - Shows loading animation during processing
        - Displays formatted responses
        - Handles commands and exit conditions
        """
        print(BANNER)
        
        while self.running:
            loading_task = None
            try:
                # Get input
                print(PROMPT, end='')
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, "")

                if not user_input.strip():
                    continue

                # Start loader
                loading_task = asyncio.create_task(self.start_loader())

                # Process
                result = await self.router.process(user_input, "console")

                # Stop loader
                self.stop_loader()
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

                # Output
                if result['success']:
                    if result.get('action') == 'quit':
                        self.running = False
                        print(f"\n{EXIT}")
                    else:
                        response = result.get('response', '')
                        if response:
                            print(f"\n── AIVA ────────────\n{response}\n────────────────────")

            except KeyboardInterrupt:
                if loading_task:
                    self.stop_loader()
                    loading_task.cancel()
                self.running = False
                print(f"\n{EXIT}")
            except Exception as e:
                if loading_task:
                    self.stop_loader()
                    loading_task.cancel()
                pass
