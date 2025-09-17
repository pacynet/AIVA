"""Message routing and processing module for AIVA.

This module handles incoming user messages, processes commands, manages conversation
history, and coordinates with AI providers and tools to generate responses.
"""

import logging
import json
from framework.constants import MSG
from modules.tools import ToolManager

logger = logging.getLogger(__name__)

class Router:
    """Central message router for processing user inputs and generating responses.

    The Router class handles message routing, command processing, conversation history
    management, and coordination between AI providers and tool execution.
    """
    def __init__(self, ai_manager, config):
        """Initialize the Router with AI manager and configuration.

        Args:
            ai_manager: AI provider manager instance
            config: Application configuration object
        """
        self.ai = ai_manager
        self.config = config
        self.history = {}
        self.tools = ToolManager(config)
        self.commands = {
            'quit': self._cmd_quit,
            'clear': self._cmd_clear,
            'ai': self._cmd_ai,
            'help': self._cmd_help,
        }

    def _is_json(self, text):
        """Check if text appears to be JSON format.

        Args:
            text (str): Text to check

        Returns:
            bool: True if text looks like JSON (starts with '{' and ends with '}')
        """
        text = text.strip()
        return text.startswith('{') and text.endswith('}')

    async def _handle_tool_call(self, response_text: str, text: str, uid: str) -> dict:
        """Execute a tool call from AI response and get final AI response.

        Args:
            response_text (str): JSON-formatted tool call from AI
            text (str): Original user message
            uid (str): User identifier

        Returns:
            dict: Result containing success status and final AI response
        """
        try:
            tool_json = json.loads(response_text)
            tool_name = tool_json.get("tool")
            tool_args = tool_json.get("args", {})

            if not tool_name:
                return {'success': False, 'error': "Invalid tool format: 'tool' key missing."}

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            result = self.tools.execute(tool_name, **tool_args)

            # Format tool result for AI
            if isinstance(result, list):
                tool_result = '\n'.join(map(str, result))
            elif isinstance(result, dict):
                tool_result = json.dumps(result, indent=2, ensure_ascii=False)
            else:
                tool_result = str(result)

            # Add messages to history and get final AI response
            self.history[uid].append({'role': 'user', 'content': text})
            self.history[uid].append({'role': 'assistant', 'content': response_text})
            self.history[uid].append({'role': 'user', 'content': f"Tool result: {tool_result}"})

            # Get AI's interpretation/summary of the tool result
            final_response = await self.ai.generate(
                f"The tool '{tool_name}' returned: {tool_result}. Please provide a helpful summary or response to the user.",
                history=self.history[uid]
            )

            self.history[uid].append({'role': 'assistant', 'content': final_response})

            return {'success': True, 'response': final_response}

        except json.JSONDecodeError:
            return {'success': False, 'error': "Invalid JSON format in tool call."}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {'success': False, 'error': f"Error executing tool {tool_name}: {e}"}

    async def process(self, text: str, uid: str = "console") -> dict:
        """Process incoming text and return response"""
        text = text.strip()
        if not text:
            return {'success': False, 'error': MSG.EMPTY_MSG}

        # Handle commands
        if text.startswith('/'):
            return await self._handle_command(text[1:], uid)

        # Generate AI response
        try:
            if uid not in self.history:
                self.history[uid] = []

            response = await self.ai.generate(text, history=self.history[uid])

            # Check for tool call and handle it
            if self._is_json(response):
                return await self._handle_tool_call(response, text, uid)

            self.history[uid].append({'role': 'user', 'content': text})
            self.history[uid].append({'role': 'assistant', 'content': response})

            # Keep history limited to prevent context overflow
            max_history = 20  # Moved from constants
            if len(self.history[uid]) > max_history:
                self.history[uid] = self.history[uid][-max_history:]

            return {'success': True, 'response': response}

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {'success': False, 'error': MSG.GEN_FAILED}

    async def _handle_command(self, cmd_text: str, uid: str) -> dict:
        """Process user commands starting with '/'.

        Args:
            cmd_text (str): Command text without the leading '/'
            uid (str): User identifier

        Returns:
            dict: Command execution result
        """
        parts = cmd_text.split()
        if not parts:
            return {'success': False, 'error': MSG.INVALID_CMD}

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in self.commands:
            return await self.commands[cmd](args, uid)
        return {'success': False, 'error': MSG.INVALID_CMD}

    # Command implementations
    async def _cmd_quit(self, args, uid):
        """Handle quit command.

        Args:
            args (list): Command arguments (unused)
            uid (str): User identifier (unused)

        Returns:
            dict: Success result with quit action
        """
        return {'success': True, 'action': 'quit'}

    async def _cmd_clear(self, args, uid):
        """Handle clear command to reset conversation history.

        Args:
            args (list): Command arguments (unused)
            uid (str): User identifier

        Returns:
            dict: Success result with clear confirmation
        """
        if uid in self.history:
            self.history[uid] = []
        return {'success': True, 'response': MSG.CLEARED}

    async def _cmd_ai(self, args, uid):
        """Handle AI provider switching command.

        Args:
            args (list): Command arguments, first arg is provider name
            uid (str): User identifier (unused)

        Returns:
            dict: Result of provider switch or list of available providers
        """
        if not args:
            providers = self.ai.list_providers()
            return {'success': True, 'response': MSG.AI_LIST.format(self.ai.current, ', '.join(providers))}

        if self.ai.switch_provider(args[0]):
            return {'success': True, 'response': MSG.AI_SWITCHED.format(args[0])}
        return {'success': False, 'error': MSG.AI_NOT_FOUND}

    async def _cmd_help(self, args, uid):
        """Handle help command to show available commands.

        Args:
            args (list): Command arguments (unused)
            uid (str): User identifier (unused)

        Returns:
            dict: Success result with help text
        """
        return {'success': True, 'response': MSG.HELP}
