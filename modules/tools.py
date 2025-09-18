import subprocess
import csv
import logging
from pathlib import Path
from typing import List, Any

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Custom exception for tool execution failures."""
    pass


class ToolManager:
    """
    Tool execution manager.
    """
    BASH_TIMEOUT = 30  # Maximum execution time for bash commands

    def __init__(self, config: Any):
        """
        Initialize ToolManager.
        """
        self.config = config
        self.tools = {
            "bash": self.run_bash,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "read_csv": self.read_csv,
            "write_csv": self.write_csv,
            "list_dir": self.list_directory,
        }

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a named tool.
        """
        if tool_name not in self.tools:
            raise ToolExecutionError(f"Tool '{tool_name}' is not available")

        try:
            logger.info(f"Executing tool '{tool_name}'")
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}")
            raise ToolExecutionError(f"Tool execution failed: {e}") from e

    def run_bash(self, *, cmd: str) -> str:
        """
        Execute a bash command.
        """
        if not cmd.strip():
            raise ValueError("Empty command")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.BASH_TIMEOUT,
                encoding='utf-8',
                errors='replace'
            )
            output = result.stdout.strip() or result.stderr.strip()
            logger.info(f"Bash command executed: {cmd[:50]}... (exit code: {result.returncode})")
            return output or f"Command executed with exit code {result.returncode}"
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {self.BASH_TIMEOUT}s: {cmd}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise ToolExecutionError(f"Command execution failed: {e}")

    def read_file(self, *, path: str) -> str:
        """
        Read text file.
        """
        file_path = Path(path).resolve()
        if not file_path.exists():
            raise ToolExecutionError(f"File not found: {path}")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            raise ToolExecutionError(f"Failed to read file: {e}")

    def write_file(self, *, path: str, content: str) -> str:
        """
        Write content to file.
        """
        file_path = Path(path).resolve()
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            content_size = len(content.encode('utf-8'))
            logger.info(f"Wrote {content_size} bytes to {path}")
            return f"Successfully wrote {content_size} bytes to {path}"
        except Exception as e:
            raise ToolExecutionError(f"Failed to write file: {e}")

    def read_csv(self, *, path: str) -> List[List[str]]:
        """
        Read CSV file data.
        """
        file_path = Path(path).resolve()
        if not file_path.exists():
            raise ToolExecutionError(f"CSV file not found: {path}")
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
            logger.info(f"Read {len(data)} rows from CSV: {path}")
            return data
        except Exception as e:
            raise ToolExecutionError(f"Failed to read CSV: {e}")

    def write_csv(self, *, path: str, data: List[List[Any]]) -> str:
        """
        Write data to CSV file.
        """
        file_path = Path(path).resolve()
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            logger.info(f"Wrote {len(data)} rows to CSV: {path}")
            return f"Successfully wrote {len(data)} rows to {path}"
        except Exception as e:
            raise ToolExecutionError(f"Failed to write CSV: {e}")

    def list_directory(self, *, path: str, recursive: bool = False) -> List[str]:
        """
        List files in directory.
        """
        dir_path = Path(path).resolve()
        if not dir_path.is_dir():
            raise ToolExecutionError(f"Not a directory: {path}")
        try:
            files_list = []
            if recursive:
                for file_path in dir_path.rglob('*'):
                    files_list.append(str(file_path))
            else:
                for file_path in dir_path.iterdir():
                    files_list.append(str(file_path))
            logger.info(f"Listed {len(files_list)} files in {path}")
            return files_list
        except Exception as e:
            raise ToolExecutionError(f"Failed to list directory: {e}")
