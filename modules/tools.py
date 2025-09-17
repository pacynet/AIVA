"""Tool management system for AIVA.

Provides a comprehensive set of tools for system operations, file management,
and Gmail integration. Tools can be executed by AI agents to perform various
tasks on behalf of users.
"""

import subprocess
import os
import csv
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow


class ToolManager:
    """Manager for tool execution and orchestration.

    Provides a unified interface for registering, validating, and executing
    various tools that AI agents can use to interact with the system.
    """
    def __init__(self, config):
        """Initialize the ToolManager with configuration.

        Args:
            config: Application configuration containing API keys and settings
        """
        self.config = config
        self.tools = {
            "bash": self.run_bash,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "read_csv": self.read_csv,
            "write_csv": self.write_csv,
            "list_dir": self.list_directory,
            "gmail_list": self.list_emails,
            "gmail_send": self.send_email,
        }

    def execute(self, tool_name: str, **kwargs):
        """Execute a named tool with provided arguments.

        Args:
            tool_name (str): Name of the tool to execute
            **kwargs: Keyword arguments specific to the tool

        Returns:
            Tool execution result (type varies by tool)

        Raises:
            Exception: If tool is not available or execution fails
        """
        if tool_name not in self.tools:
            raise Exception(f"Tool {tool_name} not available")
        return self.tools[tool_name](**kwargs)

    # Bash execution tools
    def run_bash(self, *, cmd: str) -> str:
        """Execute a bash command and return the output.

        Args:
            cmd (str): The bash command to execute

        Returns:
            str: Command output (stdout if successful, stderr if failed)
        """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()

    # File management tools
    def read_file(self, *, path: str) -> str:
        """Read the contents of a text file.

        Args:
            path (str): Path to the file to read

        Returns:
            str: File contents as a string
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, *, path: str, content: str) -> str:
        """Write content to a text file.

        Args:
            path (str): Path to the file to write
            content (str): Content to write to the file

        Returns:
            str: Success message with file path
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    def read_csv(self, *, path: str):
        """Read data from a CSV file.

        Args:
            path (str): Path to the CSV file to read

        Returns:
            list: List of rows, where each row is a list of values
        """
        with open(path, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            return [row for row in reader]

    def write_csv(self, *, path: str, data: list) -> str:
        """Write data to a CSV file.

        Args:
            path (str): Path to the CSV file to write
            data (list): List of rows to write, where each row is a list of values

        Returns:
            str: Success message with file path
        """
        with open(path, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)
        return f"Successfully wrote data to {path}"

    def list_directory(self, *, path: str, recursive=False):
        """List files in a directory.

        Args:
            path (str): Directory path to list
            recursive (bool): Whether to list files recursively in subdirectories

        Returns:
            list: List of file paths in the directory
        """
        files_list = []
        for root, dirs, files in os.walk(path):
            for f in files:
                files_list.append(os.path.join(root, f))
            if not recursive:
                break
        return files_list

    # Gmail integration tools
    def get_gmail_service(self):
        """Create Gmail service object and handle token refresh.

        Handles OAuth2 authentication, token refresh, and service initialization
        for Gmail API access.

        Returns:
            Gmail service object for API calls

        Raises:
            Exception: If credentials file not found or authentication fails
        """
        creds = None
        token_path = self.config.google_token
        creds_path = self.config.google_creds

        if not creds_path or not os.path.exists(creds_path):
            raise Exception(f"Google credentials file not found at: {creds_path}")

        # Load existing credentials from token file if available
        if token_path and os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(
                token_path, ["https://www.googleapis.com/auth/gmail.modify"])

        # Handle credential validation and refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # Refresh expired token
            else:
                # Create new credentials if no valid token exists
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, ["https://www.googleapis.com/auth/gmail.modify"])
                creds = flow.run_local_server(port=0)  # Start local auth server
            
            # Save credentials for future use
            if token_path:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

        service = build('gmail', 'v1', credentials=creds)
        return service

    def list_emails(self, *, max_results=5):
        """Retrieve and format recent email messages.

        Args:
            max_results (int): Maximum number of emails to retrieve (default: 5)

        Returns:
            str: Formatted string containing email details (sender, subject, snippet)
        """
        try:
            service = self.get_gmail_service()
            results = service.users().messages().list(userId='me', maxResults=max_results).execute()
            messages = results.get('messages', [])
            if not messages:
                return "No new messages."

            email_list_formatted = []
            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id']).execute()
                payload = m.get('payload', {})
                headers = payload.get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                snippet = m.get('snippet', 'No snippet available.')

                email_list_formatted.append(
                    f"From: {sender}\n"
                    f"Subject: {subject}\n"
                    f"Snippet: {snippet}"
                )
            
            return "\n---\n".join(email_list_formatted)
        except HttpError as error:
            return f"An error occurred: {error}"

    def create_message(self, *, to: str, subject: str, body: str):
        """Create a Gmail message object for sending.

        Args:
            to (str): Recipient email address
            subject (str): Email subject line
            body (str): Email body content

        Returns:
            dict: Gmail API message object with base64-encoded raw content
        """
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw}

    def send_email(self, *, to: str, subject: str, body: str):
        """Send an email via Gmail and return result message.

        Args:
            to (str): Recipient email address
            subject (str): Email subject line
            body (str): Email body content

        Returns:
            str: Success message with recipient and message ID, or error message
        """
        try:
            service = self.get_gmail_service()
            message = self.create_message(to=to, subject=subject, body=body)
            sent = service.users().messages().send(userId='me', body=message).execute()
            return f"Email sent successfully to {to}. Message ID: {sent['id']}"
        except HttpError as error:
            return f"An error occurred while sending email: {error}"