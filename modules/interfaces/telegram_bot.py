import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import TelegramError

from framework.constants import MSG

logger = logging.getLogger(__name__)


class TelegramBot:
    # Rate limiting configuration
    MAX_MESSAGE_LENGTH = 4096  # Telegram's message length limit
    TYPING_ACTION_INTERVAL = 5  # Send typing action every 5 seconds

    def __init__(self, router: Any, config: Any):
        """
        Initialize Telegram bot interface.

        Args:
            router: Message router for processing user inputs
            config: Application configuration with bot token
        """
        self.router = router
        self.config = config
        self.app: Optional[Application] = None
        self.running = True

        # User session tracking
        self.user_sessions: Dict[int, datetime] = {}

    async def run(self) -> None:
        """
        Start the Telegram bot and begin polling.

        Initializes the bot application, registers handlers,
        and starts polling for updates.
        """
        try:
            # Build application with configuration
            self.app = (
                Application.builder()
                .token(self.config.telegram_token)
                .build()
            )

            # Register command handlers
            self._register_handlers()

            # Set bot commands for UI
            await self._set_bot_commands()

            # Initialize and start bot
            await self.app.initialize()
            await self.app.start()

            logger.info("Telegram bot started successfully")

            # Start polling for updates
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Ignore old messages
            )

            # Keep bot running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            raise
        finally:
            # Cleanup on shutdown
            if self.app:
                try:
                    await self.app.updater.stop()
                    await self.app.stop()
                    await self.app.shutdown()
                except Exception as e:
                    logger.error(f"Error during Telegram bot cleanup: {e}")

    def _register_handlers(self) -> None:
        """Register message and command handlers."""
        if not self.app:
            return

        # Command handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("clear", self.cmd_clear))
        self.app.add_handler(CommandHandler("ai", self.cmd_ai))

        # Text message handler (including commands passed as text)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )

        # Handle edited messages
        self.app.add_handler(
            MessageHandler(
                filters.UpdateType.EDITED_MESSAGE & filters.TEXT,
                self.handle_edited_message
            )
        )

    async def _set_bot_commands(self) -> None:
        """Set bot commands for Telegram UI."""
        if not self.app or not self.app.bot:
            return

        commands = [
            BotCommand("start", "Start the bot and see welcome message"),
            BotCommand("help", "Show available commands"),
            BotCommand("clear", "Clear conversation history"),
            BotCommand("ai", "Switch AI provider or list available providers"),
        ]

        try:
            await self.app.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        except TelegramError as e:
            logger.warning(f"Failed to set bot commands: {e}")

    def _track_user_session(self, user_id: int) -> None:
        """
        Track user session for analytics.

        Args:
            user_id: Telegram user ID
        """
        self.user_sessions[user_id] = datetime.now()

        # Log new user
        if len(self.user_sessions) == 1:
            logger.info(f"First user connected: {user_id}")

    async def _send_typing_action(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Send typing indicator to show bot is processing.

        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
        except TelegramError as e:
            logger.warning(f"Failed to send typing action: {e}")

    async def _send_long_message(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            text: str
    ) -> None:
        """
        Send long message, splitting if necessary.

        Args:
            update: Telegram update object
            context: Bot context
            text: Message text to send
        """
        # Split message if too long
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            await update.message.reply_text(text)
            return

        # Split by paragraphs or sentences
        parts = []
        current_part = ""

        for paragraph in text.split('\n\n'):
            if len(current_part) + len(paragraph) + 2 > self.MAX_MESSAGE_LENGTH:
                if current_part:
                    parts.append(current_part.strip())
                current_part = paragraph
            else:
                if current_part:
                    current_part += "\n\n"
                current_part += paragraph

        if current_part:
            parts.append(current_part.strip())

        # Send parts
        for i, part in enumerate(parts):
            await update.message.reply_text(part)

            # Small delay between messages
            if i < len(parts) - 1:
                await asyncio.sleep(0.5)

    # Command handlers
    async def cmd_start(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /start command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user = update.effective_user
        welcome_message = (
            f"👋 Hello {user.first_name}!\n\n"
            f"I'm AIVA, your AI Virtual Assistant. "
            f"I can help you with various tasks, answer questions, "
            f"and even execute tools on your behalf.\n\n"
            f"Just send me a message to get started!\n\n"
            f"Type /help to see available commands."
        )

        await update.message.reply_text(welcome_message)
        self._track_user_session(user.id)
        logger.info(f"User {user.id} ({user.first_name}) started the bot")

    async def cmd_help(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /help command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        help_text = MSG.HELP
        await update.message.reply_text(help_text)

    async def cmd_clear(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /clear command to reset conversation history.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = str(update.effective_user.id)

        # Process clear command through router
        result = await self.router.process("/clear", user_id)

        if result['success']:
            response = result.get('response', MSG.CLEARED)
            await update.message.reply_text(f"✅ {response}")
        else:
            error = result.get('error', MSG.ERROR)
            await update.message.reply_text(f"❌ {error}")

    async def cmd_ai(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /ai command for provider management.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = str(update.effective_user.id)

        # Get command arguments
        args = context.args if context.args else []
        command = f"/ai {' '.join(args)}" if args else "/ai"

        # Process through router
        result = await self.router.process(command, user_id)

        if result['success']:
            response = result.get('response', '')
            if response:
                await update.message.reply_text(response)
        else:
            error = result.get('error', MSG.ERROR)
            await update.message.reply_text(f"❌ {error}")

    async def handle_message(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle regular text messages.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not update.message or not update.message.text:
            return

        user_id = str(update.effective_user.id)
        message_text = update.message.text

        # Track session
        self._track_user_session(update.effective_user.id)

        # Log message
        logger.info(f"Received message from user {user_id}: {message_text[:50]}...")

        try:
            # Send typing indicator
            await self._send_typing_action(update, context)

            # Create task for periodic typing updates
            typing_task = asyncio.create_task(
                self._send_typing_periodically(update, context)
            )

            try:
                # Process message through router
                result = await self.router.process(message_text, user_id)

                # Cancel typing indicator
                typing_task.cancel()

                # Send response
                if result['success']:
                    response = result.get('response', MSG.ERROR)
                    if response:
                        await self._send_long_message(update, context, response)
                else:
                    error = result.get('error', MSG.ERROR)
                    await update.message.reply_text(f"❌ {error}")

            finally:
                # Ensure typing task is cancelled
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass

        except TelegramError as e:
            logger.error(f"Telegram error handling message: {e}")
            try:
                await update.message.reply_text(
                    "❌ Sorry, I encountered an error sending the response. "
                    "Please try again."
                )
            except:
                pass  # Ignore errors when sending error message
        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "❌ An unexpected error occurred. Please try again later."
                )
            except:
                pass

    async def handle_edited_message(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle edited messages.

        Args:
            update: Telegram update object
            context: Bot context
        """
        await update.edited_message.reply_text(
            "ℹ️ I noticed you edited your message. "
            "Please send a new message with your updated request."
        )

    async def _send_typing_periodically(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Send typing indicator periodically during long operations.

        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            while True:
                await asyncio.sleep(self.TYPING_ACTION_INTERVAL)
                await self._send_typing_action(update, context)
        except asyncio.CancelledError:
            # Normal cancellation
            pass
        except Exception as e:
            logger.warning(f"Error in periodic typing indicator: {e}")