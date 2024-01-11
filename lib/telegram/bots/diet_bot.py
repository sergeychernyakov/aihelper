import os
import importlib
import glob
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lib.openai.thread_run_manager import ThreadRunManager
from lib.openai.tokenizer import Tokenizer
from lib.localization import _, change_language
from lib.telegram.bots.new_base_bot import NewBaseBot
from lib.telegram.payment import Payment
from lib.openai.assistant import Assistant

class DietBot(NewBaseBot):
    """
    DietBot is a custom Telegram bot for handling various types of messages
    and translating or processing them using OpenAI's API.
    """

    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path='.env.diet', override=True)
        # Initialize the bot with the token from the environment variable
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

        Assistant.ASSISTANT_ID = os.getenv('ASSISTANT_ID')

        Payment.YOOKASSA_API_TOKEN = os.getenv('YOOKASSA_API_TOKEN')
        Payment.STRIPE_API_TOKEN = os.getenv('STRIPE_API_TOKEN')

        super().__init__()

    async def message_handler(self, update, context):
        """
        Primary message handler for the bot. It processes incoming messages
        and manages the conversation flow.

        :param update: Telegram update object containing message and chat details.
        :param context: Telegram context object for managing bot state and data.
        """
        self.update = update
        self.context = context
        with self.session_scope() as session:
            self.log_user_interaction()
            successful_interaction = await self.handle_interaction(session)

            # Check if the message is not a document before managing the run
            # no need to create run for documents
            if successful_interaction and not update.message.document:
                await self.thread_run_manager.manage_run()

            await self.update_balance_and_cleanup(session)

    async def process_message(self, session):
        """
        Processes the received message based on its type (text, photo, video, etc.)

        :param session: Database session for handling transactions.
        """
        self.thread_run_manager = ThreadRunManager(self.openai, self.update, self.context, self.conversation, session, self.update.message.chat_id)
        if datetime.utcnow() - self.conversation.updated_at >= self.thread_run_manager.thread_recreation_interval:
            self.thread_run_manager.recreate_thread(session, self.conversation)

        for message_type in self.get_message_handler_types():
            if getattr(self.update.message, message_type):
                success = await self.handle_message_type(message_type)
                if not success:
                    await self.context.bot.send_message(self.update.message.chat_id, _(f'Failed to process the {message_type}.'))
                    return False
                return True
        return False

    def get_message_handler_types(self):
        """
        Dynamically lists all message handler types based on the files in the handlers directory.

        :return: List of message handler types like 'text', 'photo', etc.
        """
        handler_files = glob.glob('lib/telegram/message_handlers/*.py')
        return [os.path.basename(f)[:-11] for f in handler_files if not f.endswith(('__init__.py', 'base_handler.py'))]

    async def handle_message_type(self, message_type):
        """
        Handles a specific message type by dynamically importing and initializing the corresponding handler.

        :param message_type: Type of the message (e.g., 'text', 'photo').
        :return: Boolean indicating the success of the message processing.
        """
        module_name = f"lib.telegram.message_handlers.{message_type}_handler"
        class_name = f"{message_type.capitalize()}Handler"

        module = importlib.import_module(module_name)
        handler_class = getattr(module, class_name)

        handler = handler_class(self.openai, self.update, self.context, self.conversation)

        # Use a ternary conditional expression to decide which method to call
        return handler.handle_message(self.update.message.text) if message_type == 'text' else await handler.handle_message()

    async def start(self, update: Update, context: CallbackContext) -> None:
        """
        Start command handler. Initializes the conversation and sends the welcome message.

        :param update: Telegram update object.
        :param context: Telegram context object.
        """
        self.update = update
        self.context = context
        with self.session_scope() as session:
            self.conversation = self._get_or_create_conversation(session)
            change_language(self.conversation.language_code)

            current_balance = self.conversation.balance
            start_balance = Tokenizer.START_BALANCE

            initial_welcome_message = _(
                "Welcome to the Russian-Ukrainian AI Translator! "
                "My name is Nova and I can assist you with various tasks. Here's what you can do:\n\n"
                "Speak with me like with a friend :)\n"
                "Translate various texts from/to Russian/Ukrainian\n"
                "Translate voice messages\n"
                "Translate audio/video files\n"
                "Translate text, pdf, and other documents\n"
                "Generate images\n"
                "I speak your language\n\n"
                "Balance:\n"
                "Your start balance is ${0:.2f} - we'll ask to refill the balance when you'll use it in full.\n"
                "Your current balance is ${1:.2f}.\n\n"
                "Contacts:\n"
                "- For advertising inquiries, contact @AIBotsAdv\n"
                "- For investment-related questions, contact @AIBotsInvest\n"
                "- For development of intelligent bots, write to @AIBotsTech\n"
                "- Support: @AIBotsTech\n\n"
                "Available Actions:\n"
            ).format(start_balance, current_balance)

            # Buttons and the remaining part of the welcome message
            keyboard = [
                [
                    InlineKeyboardButton(_("Check Balance"), callback_data='balance'),
                    InlineKeyboardButton(_("Top Up Balance"), callback_data='invoice'),
                    InlineKeyboardButton(_("Finish Session"), callback_data='finish')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send the initial part of the welcome message
            await context.bot.send_message(update.message.chat_id, initial_welcome_message, reply_markup=reply_markup)

            remaining_welcome_message = _(
                "/balance - Check your current balance\n"
                "/invoice - Top up your balance\n"
                "/start - Show welcome message again\n"
                "/finish - Finish your current session\n\n"
                "Enjoy your experience with our service!\n"
                "Check our video tutorial."
            )

            # Send the remaining part of the welcome message with buttons
            await context.bot.send_message(update.message.chat_id, remaining_welcome_message)
            await context.bot.send_message(update.message.chat_id, 'https://youtu.be/_L1mFH_V-0o')
