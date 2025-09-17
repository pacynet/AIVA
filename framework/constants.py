"""Shared constants for AIVA.

Common messages used across multiple modules.
"""

class MSG:
    """Common messages used across modules."""
    # Common error messages used across modules
    ERROR = "Error"
    EMPTY_MSG = "Empty message"
    INVALID_CMD = "Unknown command"
    AI_NOT_FOUND = "AI provider not found"
    GEN_FAILED = "Generation failed"

    # Command responses used in router
    CLEARED = "History cleared"
    AI_SWITCHED = "Switched to {}"
    AI_LIST = "Current: {}\nAvailable: {}"

    # Help text
    HELP = """  /clear - Clear conversation
  /quit - Exit application
  /help - Show this help
  /ai <provider> - Switch AI provider"""