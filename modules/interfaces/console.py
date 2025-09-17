"""Console interface for AIVA.

Provides an interactive command-line interface for users to interact with
the AIVA assistant, including input handling, output formatting, and loading animations.
"""

import asyncio
from framework.constants import MSG
from modules.loader import Loader

class Console:
    """Interactive console interface for AIVA.

    Handles user input/output, manages the main interaction loop, and provides
    visual feedback through loading animations and formatted responses.
    """
    def __init__(self, router):
        """Initialize the console interface.

        Args:
            router: Message router instance for processing user inputs
        """
        self.router = router
        self.running = True
        self.loader = Loader()

    async def run(self):
        """Start the main console interaction loop.

        Displays the welcome banner and enters an interactive loop that:
        - Prompts for user input
        - Shows loading animation during processing
        - Displays formatted responses
        - Handles commands and exit conditions
        """
        print(MSG.BANNER)
        
        while self.running:
            loading_task = None
            try:
                # Get input
                print(MSG.PROMPT, end='')
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, "")

                if not user_input.strip():
                    continue

                # Start loader
                loading_task = asyncio.create_task(self.loader.start())

                # Process
                result = await self.router.process(user_input, "console")

                # Stop loader
                self.loader.stop()
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

                # Output
                if result['success']:
                    if result.get('action') == 'quit':
                        self.running = False
                        print(f"\n{MSG.EXIT}")
                    else:
                        response = result.get('response', '')
                        if response:
                            print(f"\n── AIVA ────────────\n{response}\n────────────────────")

            except KeyboardInterrupt:
                if loading_task:
                    self.loader.stop()
                    loading_task.cancel()
                self.running = False
                print(f"\n{MSG.EXIT}")
            except Exception as e:
                if loading_task:
                    self.loader.stop()
                    loading_task.cancel()
                pass
