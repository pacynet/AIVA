"""Telegram bot interface for AIVA.

Provides a Telegram bot interface that allows users to interact with AIVA
through Telegram messages, handling both text messages and commands.
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from framework.constants import MSG

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot interface for AIVA.

    Handles Telegram bot initialization, message processing, and response delivery
    through the Telegram Bot API.
    """
    def __init__(self, router, config):
        """Initialize the Telegram bot.

        Args:
            router: Message router instance for processing user inputs
            config: Application configuration containing Telegram bot token
        """
        self.router = router
        self.config = config
        self.app = None

    async def run(self):
        """Start the Telegram bot and begin polling for messages.

        Initializes the bot application, sets up message handlers, and starts
        polling for updates from the Telegram API.
        """
        self.app = Application.builder().token(self.config.telegram_token).build()

        # Pass all text messages (including commands) to the message handler
        self.app.add_handler(MessageHandler(filters.TEXT, self.message))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        while True:
            await asyncio.sleep(1)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages from Telegram users.

        Args:
            update (Update): Telegram update object containing the message
            context (ContextTypes.DEFAULT_TYPE): Bot context object
        """
        user_id = str(update.effective_user.id)

        result = await self.router.process(update.message.text, user_id)

        if result['success']:
            await update.message.reply_text(result.get('response', ''))
        else:
            await update.message.reply_text(result.get('error', MSG.ERROR))