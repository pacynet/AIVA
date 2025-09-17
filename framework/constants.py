"""Application constants and configuration values for AIVA.

Defines terminal colors, user interface messages, file paths, configuration defaults,
and environment variable keys used throughout the AIVA application.
"""

import os
import sys

class Color:
    """ANSI terminal color codes and formatting.

    Provides color constants for terminal output formatting, including
    color codes, cursor control, and platform-specific initialization.
    """
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
        """Initialize color support for the current platform.

        Enables color support on Windows by calling 'color' command.
        No action needed on Unix-like systems.
        """
        if sys.platform == 'win32':
            os.system('color')
            pass

class MSG:
    """User interface messages and text constants.

    Contains all text messages, prompts, error messages, help text,
    and other user-facing strings used throughout the application.
    """
    # Banner
    BANNER = f"""{Color.GRAY}╔══════════════════════════════════════╗{Color.RESET}
{Color.GRAY}║{Color.RESET}      {Color.BOLD}█████╗ ██╗██╗   ██╗ █████╗{Color.RESET}{Color.GRAY}      ║{Color.RESET}
{Color.GRAY}║{Color.RESET}     {Color.BOLD}██╔══██╗██║██║   ██║██╔══██╗{Color.RESET}{Color.GRAY}     ║{Color.RESET}
{Color.GRAY}║{Color.RESET}     {Color.BOLD}███████║██║██║   ██║███████║{Color.RESET}{Color.GRAY}     ║{Color.RESET}
{Color.GRAY}║{Color.RESET}     {Color.BOLD}██╔══██║██║╚██╗ ██╔╝██╔══██║{Color.RESET}{Color.GRAY}     ║{Color.RESET}
{Color.GRAY}║{Color.RESET}     {Color.BOLD}██║  ██║██║ ╚████╔╝ ██║  ██║{Color.RESET}{Color.GRAY}     ║{Color.RESET}
{Color.GRAY}║{Color.RESET}     {Color.BOLD}╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝{Color.RESET}{Color.GRAY}     ║{Color.RESET}
{Color.GRAY}║{Color.RESET}                                      {Color.GRAY}║{Color.RESET}
{Color.GRAY}║{Color.RESET}    {Color.YELLOW}AI Virtual Assistant - v1.0.0{Color.RESET}     {Color.GRAY}║{Color.RESET}
{Color.GRAY}╚══════════════════════════════════════╝{Color.RESET}
{Color.GRAY}Type /help for commands{Color.RESET} """

    # System messages
    INIT = "Initializing AIVA..."
    LOADING = "Loading components..."
    READY = "✓ AIVA ready!"
    EXIT = "Goodbye!"
    SHUTDOWN = "Shutting down..."
    CLEANUP = "Cleaning up..."
    CLEANUP_DONE = "Cleanup completed"

    # Interface messages
    PROMPT = "\n>> "

    # Command responses
    CLEARED = "History cleared"
    AI_SWITCHED = "Switched to {}"
    AI_CURRENT = "Current: {}\nAvailable: {}"
    AI_LIST = "Current: {}\nAvailable: {}"
    TOOLS_LIST = "Available tools:\n{}"
    SAVED = "Saved to {}"
    LOADED = "Loaded {} messages"
    NO_FILES = "No files found"
    FILES_HEADER = "Files:"
    FILE_ITEM = "• {} ({} bytes)"

    # Status messages
    STATUS_HEADER = "Status:"
    STATUS = "AI Provider: {}\nHistory: {} messages\nTools: {}"
    STATUS_AI = "• AI Provider: {}"
    STATUS_HISTORY = "• History: {} messages"
    STATUS_NLU = "• NLU: {}"
    STATUS_FILES = "• File Manager: {}"
    ENABLED = "Enabled"
    DISABLED = "Disabled"

    # Help text
    HELP = """  /clear - Clear conversation
  /quit - Exit application
  /help - Show this help
  /ai <provider> - Switch AI provider
  /tools - List available tools
  /tool <name> - Show tool schema"""

    # Errors
    ERROR = "Error"
    EMPTY_MSG = "Empty message"
    INVALID_CMD = "Unknown command"
    NO_PROVIDER = "No AI providers available"
    PROVIDER_NOT_AVAIL = "Provider not available"
    AI_NOT_FOUND = "AI provider not found"
    TOOL_NOT_FOUND = "Tool not found"
    NO_TOOLS = "No tools available"
    FILE_NOT_FOUND = "File not found"
    INVALID_FILE = "Invalid file"
    NO_FILENAME = "Provide filename"
    NO_FILE_MGR = "File manager not available"
    NO_PERMISSION = "Access denied"
    CONN_ERROR = "Connection error"
    GEN_FAILED = "Generation failed"
    GREETING_EN = "Hello! How can I help?"

    # Provider messages
    OPENAI_NO_KEY = "OpenAI API key not configured"
    GEMINI_NO_KEY = "Gemini API key not configured"
    OLLAMA_NOT_AVAIL = "Ollama not available at {}"
    PROVIDER_INIT_FAIL = "Failed to initialize {}"

    # Loader messages
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

    # Installation prompts
    INSTALL_OLLAMA = "Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh"
    PULL_MODEL = "Pulling model {}..."

class PATHS:
    """File and directory path constants.

    Defines standard paths for configuration files, logs, workspace
    directories, and other file system locations used by AIVA.
    """
    CONFIG_DIR = "./config"
    WORKSPACE = "./workspace"
    LOGS_DIR = "./logs"
    ENV_FILE = "./config/.env"
    CONFIG_FILE = "./config/settings.json"
    PROMPT_FILE = "./config/system_prompt.txt"
    LOG_FILE = "./logs/aiva.log"

    # Workspace subdirs
    DOCUMENTS = "documents"
    TEMP = "temp"
    ARCHIVES = "archives"

class CONFIG:
    """Default configuration values and settings.

    Contains default values for AI providers, model settings, timeouts,
    file size limits, and other configuration parameters.
    """
    DEFAULT_SYSTEM_PROMPT = """You are AIVA, a helpful AI assistant.
You can use tools to perform actions. When you need to use a tool, respond with a JSON object in the following format. Do not add any other text outside the JSON block.

{
  "tool": "tool_name",
  "args": {
    "arg_name1": "value1",
    "arg_name2": "value2"
  }
}

Here are the available tools:
- `bash`: Executes a shell command.
  - `cmd` (str): The command to execute.
- `read_file`: Reads the content of a file.
  - `path` (str): The path to the file.
- `write_file`: Writes content to a file.
  - `path` (str): The path to the file.
  - `content` (str): The content to write.
- `list_dir`: Lists files in a directory.
  - `path` (str): The directory path.
  - `recursive` (bool): Whether to list recursively.
- `read_csv`: Reads data from a CSV file.
  - `path` (str): The path to the CSV file.
- `write_csv`: Writes data to a CSV file.
  - `path` (str): The path to the CSV file.
  - `data` (list): The data to write.
- `gmail_list`: Lists recent emails from a Gmail account.
  - `max_results` (int): The maximum number of emails to return.
- `gmail_send`: Sends an email.
  - `to` (str): The recipient's email address.
  - `subject` (str): The email subject.
  - `body` (str): The email body."""

    DEFAULT_CONFIG = {
        "default_ai": "ollama",
        "ai": {
            "openai": {"model": "gpt-4o-mini", "temperature": 0.7},
            "gemini": {"model": "gemini-2.5-pro", "temperature": 0.7},
            "ollama": {"model": "llama3.2", "temperature": 0.7}
        }
    }
    DEFAULT_TEMP = 0.7
    DEFAULT_TOKENS = 2000
    MAX_FILE_SIZE_MB = 10
    MAX_HISTORY = 20
    NLU_THRESHOLD = 0.7
    OLLAMA_HOST = "http://localhost:11434"

    # Timeouts
    TIMEOUT_SHORT = 3
    TIMEOUT_MEDIUM = 60
    TIMEOUT_LONG = 300

    # Extensions
    ALLOWED_EXT = [".txt", ".md", ".json", ".py", ".js", ".html", ".css"]

class ENV:
    """Environment variable key constants.

    Defines the names of environment variables used for API keys,
    service endpoints, and other configuration values.
    """
    OPENAI = "OPENAI_API_KEY"
    GEMINI = "GEMINI_API_KEY"
    TELEGRAM = "TELEGRAM_BOT_TOKEN"
    OLLAMA = "OLLAMA_HOST"
