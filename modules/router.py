"""
Message routing and processing module for AIVA.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum

from framework.constants import MSG
from modules.tools import ToolManager, ToolExecutionError

logger = logging.getLogger(__name__)


class ResponseAction(str, Enum):
    """Response actions."""
    QUIT = "quit"
    CLEAR = "clear"


class ProcessResult(TypedDict, total=False):
    """Type for process method results."""
    success: bool
    response: Optional[str]
    error: Optional[str]
    action: Optional[ResponseAction]


class Router:
    """Central message router."""
    MAX_HISTORY = 20

    def __init__(self, ai_manager: Any, config: Any):
        self.ai = ai_manager
        self.config = config
        self.history: Dict[str, List[Dict]] = {}
        self.tools = ToolManager(config)
        self.commands = {
            'quit': self.cmd_quit,
            'clear': self.cmd_clear,
            'ai': self.cmd_ai,
            'help': self.cmd_help,
        }

    def _manage_history(self, uid: str):
        """Trim history to MAX_HISTORY."""
        if len(self.history.get(uid, [])) > self.MAX_HISTORY:
            self.history[uid] = self.history[uid][-self.MAX_HISTORY:]

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract JSON tool call from mixed text response."""
        # Find all potential JSON objects in the text
        brace_count = 0
        start_pos = -1

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_pos = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    # Found a complete JSON object
                    potential_json = text[start_pos:i+1]
                    try:
                        tool_call = json.loads(potential_json)
                        if isinstance(tool_call, dict) and "tool" in tool_call:
                            return tool_call
                    except json.JSONDecodeError:
                        pass
                    start_pos = -1

        return None

    async def process(self, text: str, uid: str = "console") -> ProcessResult:
        """Process incoming text and return a response."""
        text = text.strip()
        if not text:
            return {'success': False, 'error': MSG.EMPTY_MSG}

        if text.startswith('/'):
            return await self.handle_command(text[1:], uid)

        if uid not in self.history:
            self.history[uid] = []

        try:
            response = await self.ai.generate(text, history=self.history[uid])

            # Check for tool calls - either pure JSON or mixed in text
            tool_call = None
            if response.strip().startswith('{') and response.strip().endswith('}'):
                # Try pure JSON first
                try:
                    tool_call = json.loads(response)
                except json.JSONDecodeError:
                    pass

            # If not pure JSON, look for JSON within text
            if not tool_call:
                tool_call = self._extract_json_from_text(response)

            # Execute tool if found
            if tool_call and isinstance(tool_call, dict) and "tool" in tool_call:
                try:
                    tool_name = tool_call.get("tool")
                    tool_args = tool_call.get("args", {})

                    if not tool_name:
                        return {'success': False, 'error': "Invalid tool format: 'tool' is required"}

                    logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
                    result = self.tools.execute(tool_name, **tool_args)

                    tool_result_str = json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)

                    # Extract text part without the JSON
                    text_response = response
                    if not (response.strip().startswith('{') and response.strip().endswith('}')):
                        # Remove JSON part from mixed response
                        json_str = json.dumps(tool_call)
                        text_response = response.replace(json_str, '').strip()

                    self.history[uid].extend([
                        {'role': 'user', 'content': text},
                        {'role': 'assistant', 'content': response},
                        {'role': 'user', 'content': f"Tool '{tool_name}' result: {tool_result_str}"}
                    ])

                    # Combine text response with tool result
                    if text_response:
                        final_response = f"{text_response}\n\nTool result: {tool_result_str}"
                    else:
                        final_response = await self.ai.generate(
                            f"The tool '{tool_name}' returned: {tool_result_str}\nProvide a helpful summary.",
                            history=self.history[uid]
                        )

                    self.history[uid].append({'role': 'assistant', 'content': final_response})
                    self._manage_history(uid)
                    return {'success': True, 'response': final_response}

                except ToolExecutionError as e:
                    return {'success': False, 'error': str(e)}
                except Exception as e:
                    logger.error(f"Error handling tool call: {e}")
                    return {'success': False, 'error': f"Error processing tool call: {e}"}

            # No tool call found, return normal response
            self.history[uid].extend([
                {'role': 'user', 'content': text},
                {'role': 'assistant', 'content': response}
            ])
            self._manage_history(uid)
            return {'success': True, 'response': response}
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return {'success': False, 'error': MSG.GEN_FAILED}

    async def handle_command(self, cmd_text: str, uid: str) -> ProcessResult:
        """Process user commands."""
        parts = cmd_text.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ''
        args = parts[1].split() if len(parts) > 1 else []

        handler = self.commands.get(cmd)
        if handler:
            try:
                return await handler(args, uid)
            except Exception as e:
                logger.error(f"Command '{cmd}' failed: {e}")
                return {'success': False, 'error': f"Command failed: {e}"}
        return {'success': False, 'error': MSG.INVALID_CMD}

    @staticmethod
    async def cmd_quit(self, args: List[str], uid: str) -> ProcessResult:
        """Handle /quit command."""
        return {'success': True, 'action': ResponseAction.QUIT}

    async def cmd_clear(self, args: List[str], uid: str) -> ProcessResult:
        """Handle /clear command."""
        if uid in self.history:
            self.history[uid] = []
            logger.info(f"Cleared history for user {uid}")
        return {'success': True, 'response': MSG.CLEARED}

    async def cmd_ai(self, args: List[str], uid: str) -> ProcessResult:
        """Handle /AI command for switching providers."""
        if not args:
            providers = self.ai.list_providers()
            current = self.ai.current
            provider_list = ', '.join(f"[{p}]" if p == current else p for p in providers)
            return {'success': True, 'response': MSG.AI_LIST.format(current, provider_list)}

        provider_name = args[0].lower()
        if self.ai.switch_provider(provider_name):
            return {'success': True, 'response': MSG.AI_SWITCHED.format(provider_name)}
        else:
            available = ', '.join(self.ai.list_providers())
            return {'success': False, 'error': f"{MSG.AI_NOT_FOUND}. Available: {available}"}

    @staticmethod
    async def cmd_help(self, args: List[str], uid: str) -> ProcessResult:
        """Handle /help command."""
        return {'success': True, 'response': MSG.HELP}
