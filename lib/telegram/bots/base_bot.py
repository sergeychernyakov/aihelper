import glob
import importlib
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List

from sqlalchemy.exc import SQLAlchemyError
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (Application, CallbackContext, CallbackQueryHandler,
                          CommandHandler, filters, MessageHandler,
                          PreCheckoutQueryHandler)

from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.constraints_checker import ConstraintsChecker
from lib.localization import _, change_language
from lib.openai.assistant import Assistant
from lib.openai.thread_run_manager import ThreadRunManager
from lib.openai.tokenizer import Tokenizer
from lib.telegram.helpers import Helpers
from lib.telegram.payment import Payment

class BaseBot:
    """
    Base class for custom Telegram bots.

    This class sets up the bot with basic command handlers and
    manages conversation states, payments, and message processing.
    """

    TELEGRAM_BOT_TOKEN = None

    def __init__(self) -> None:
        """
        Initializes the bot and sets up command handlers.
        """
        self.assistant = Assistant()
        self.payment = Payment()
        self.tokenizer = Tokenizer()
        self.openai = self.assistant.get_openai_client()
        self.application = Application.builder().token(self.TELEGRAM_BOT_TOKEN).build()
        self.conversation = None
        self.update = None
        self.context = None
        self.thread_run_manager = None
        self._setup_handlers()

    # Private Utility Methods

    def _setup_handlers(self) -> None:
        """
        Sets up the command and message handlers for the bot.
        """
        # Command handlers
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('ping', self.ping))
        self.application.add_handler(CommandHandler('balance', self.balance))
        self.application.add_handler(CommandHandler('finish', self.finish))
        self.application.add_handler(CommandHandler('invoice', self.send_invoice))

        # Callback query handler for inline keyboard buttons
        self.application.add_handler(CallbackQueryHandler(self.button))

        # Payment handlers
        self.application.add_handler(PreCheckoutQueryHandler(self.payment.precheckout_callback))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.payment.successful_payment_callback))

        # General message handler
        self.application.add_handler(MessageHandler(~filters.COMMAND, self.message_handler))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    def _create_conversation(self, session: SessionLocal, update: Update) -> Conversation:
        """
        Creates a new conversation record in the database.

        :param session: The database session for transaction management.
        :param update: The Telegram update object containing the user's message.
        :return: The newly created Conversation object.
        """
        # Create a new thread in OpenAI
        thread = self.openai.beta.threads.create()

        # Create a new Conversation object with user and thread details
        conversation = Conversation(
            user_id=update.message.from_user.id,
            language_code=update.message.from_user.language_code,
            username=update.message.from_user.username,
            thread_id=thread.id,
            assistant_id=Assistant.ASSISTANT_ID
        )

        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        print(f"New conversation created at: {conversation.updated_at}")
        return conversation

    def _get_or_create_conversation(self, session: SessionLocal) -> Conversation:
        """
        Retrieves an existing conversation from the database or creates a new one.

        This method checks if there's an existing conversation for the current user and the assistant.
        If found, it returns this conversation; otherwise, it creates a new conversation.

        :param session: The database session used to query or create the conversation.
        :return: A Conversation object representing the current conversation.
        """
        # Attempt to find an existing conversation for the current user and assistant
        return (session.query(Conversation).filter_by(
                    user_id=self.update.message.from_user.id,
                    assistant_id=Assistant.ASSISTANT_ID).first() or 
                self._create_conversation(session, self.update))

    @contextmanager
    def session_scope(self) -> Generator[SessionLocal, None, None]:
        """
        Provides a transactional scope around a series of operations.
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            print(f"An error occurred during session transaction: {e}")
            session.rollback()
        finally:
            session.close()

    # Command Handlers

    async def start(self, update: Update, context: CallbackContext) -> None:
        """
        Responds to the /start command. Initializes conversation.

        :param update: Telegram update object.
        :param context: Telegram context object.
        """
        raise NotImplementedError("This method should be overridden in a subclass")

    async def ping(self, update: Update, context: CallbackContext) -> None:
        """
        Responds to the /ping command.

        :param update: Telegram update object.
        :param context: Telegram context object.
        """
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent ping.')
        await context.bot.send_message(update.message.from_user.id, 'pong')

    async def balance(self, update: Update, context: CallbackContext, from_button: bool = False) -> None:
        """
        Responds to the /balance command. Displays user's current balance.

        :param update: Telegram update object.
        :param context: Telegram context object.
        :param from_button: Boolean indicating if triggered by a button.
        """
        if from_button:
            chat_id = update.callback_query.message.chat_id
            user_id = update.callback_query.from_user.id
        else:
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id

        with self.session_scope() as session:
            conversation = session.query(Conversation).filter_by(
                user_id=user_id,
                assistant_id=Assistant.ASSISTANT_ID
            ).first()

            if conversation:
                change_language(conversation.language_code)

                balance_amount = conversation.balance
                await context.bot.send_message(chat_id, _("Your current balance is: ${0:.2f}").format(balance_amount))
            else:
                print(f'No active conversation found, chat_id: {chat_id}')

    async def finish(self, update: Update, context: CallbackContext, from_button: bool = False) -> None:
        """
        Ends the current conversation session.

        :param update: Telegram update object.
        :param context: Telegram context object.
        :param from_button: Boolean indicating if triggered by a button.
        """
        if from_button:
            chat_id = update.callback_query.message.chat_id
            user_id = update.callback_query.from_user.id
        else:
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id

        with self.session_scope() as session:
            try:
                conversation = session.query(Conversation).filter_by(
                    user_id=user_id,
                    assistant_id=Assistant.ASSISTANT_ID
                ).first()

                if conversation:
                    change_language(conversation.language_code)

                    await context.bot.send_message(chat_id, _('Goodbye! If you need assistance again, just send me a message.'))

                    thread_run_manager = ThreadRunManager(self.openai, update, context, conversation, session, chat_id)
                    thread_run_manager.recreate_thread(session, conversation)
                else:
                    print(f'No active conversation found, chat_id: {chat_id}')

            except SQLAlchemyError as e:
                print(f"An error occurred: {e}")
                await context.bot.send_message(chat_id, _('An error occurred while processing your request.'))

    async def send_invoice(self, update: Update, context: CallbackContext) -> None:
        """
        Sends an invoice to the user for balance top-up.

        :param update: Telegram update object.
        :param context: Telegram context object.
        """
        await self.payment.send_invoice(update, context, from_button=False)

    # Callback and Message Handlers

    async def button(self, update: Update, context: CallbackContext) -> None:
        """
        Handles button presses from inline keyboards.

        :param update: Telegram update object.
        :param context: Telegram context object.
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == 'balance':
            await self.balance(update, context, from_button=True)
        elif callback_data == 'invoice':
            await self.payment.send_invoice(update, context, from_button=True)
        elif callback_data == 'finish':
            await self.finish(update, context, from_button=True)

    async def message_handler(self, update: Update, context: CallbackContext) -> None:
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
            if successful_interaction and not update.message.document:
                await self.thread_run_manager.manage_run()

            await self.update_balance_and_cleanup(session)

    # Interaction Handling Methods

    # async def handle_interaction(self, session: SessionLocal) -> bool:
    #     """
    #     Handles user interaction with the bot.

    #     :param session: Database session for transactions.
    #     """
    #     try:
    #         self.conversation = self._get_or_create_conversation(session)
    #         change_language(self.conversation.language_code)

    #         if self.is_balance_insufficient():
    #             await self.prompt_for_payment()
    #             return False

    #         return await self.process_message(session)
    #     except BadRequest as e:
    #         await self.handle_bad_request(e)
    #     except Exception as e:
    #         await self.handle_general_exception(session, e)

    async def handle_interaction(self, session: SessionLocal) -> bool:
        """
        Handles user interaction with the bot.

        :param session: Database session for transactions.
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self.conversation = self._get_or_create_conversation(session)
                change_language(self.conversation.language_code)

                if self.is_balance_insufficient():
                    await self.prompt_for_payment()
                    return False

                return await self.process_message(session)

            except BadRequest as e:
                await self.handle_bad_request(e)
                return False  # Do not retry for BadRequest exceptions

            except Exception as e:
                try:
                    await self.handle_general_exception(session, e)
                except Exception:
                    return False  # Do not retry if the exception is re-raised
                # If handle_general_exception doesn't raise an exception, continue for a retry
                print(f"Retrying interaction after handling exception. Attempt {attempt + 1} of {max_retries}")

        return False  # Return False if all retries failed

    async def process_message(self, session: SessionLocal) -> bool:
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

    async def handle_message_type(self, message_type: str) -> bool:
        """
        Handles a specific message type by dynamically importing the corresponding handler.
        """
        module_name = f"lib.telegram.message_handlers.{message_type}_handler"
        class_name = f"{message_type.capitalize()}Handler"

        # Check if the module and class exist
        if self.module_and_class_exist(module_name, class_name):
            module = importlib.import_module(module_name)
            handler_class = getattr(module, class_name)
            handler = handler_class(self.openai, self.update, self.context, self.conversation)

            # Differentiate between text and other message types
            if message_type == 'text':
                # For text messages, pass the text content to handle_message
                return handler.handle_message(self.update.message.text)
            elif hasattr(handler, 'handle_message'):
                # For other message types, call handle_message without arguments
                return await handler.handle_message()
            else:
                print(f"No handle_message method found for {message_type} handler.")
                return False
        else:
            print(f"Handler for {message_type} not found.")
            return False

    def module_and_class_exist(self, module_name: str, class_name: str) -> bool:
        """
        Checks if a module and class exist in the project.
        """
        try:
            module = importlib.import_module(module_name)
            return hasattr(module, class_name)
        except ModuleNotFoundError:
            return False

    # Utility Methods

    def get_message_handler_types(self) -> List[str]:
        """
        Dynamically lists all message handler types based on the files in the handlers directory.

        :return: List of message handler types like 'text', 'photo', etc.
        """
        # Get the directory of the current file (base_bot.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Adjust the path to point to the correct message_handlers directory
        handlers_dir = os.path.join(current_dir, '..', 'message_handlers')

        # Glob for .py files in the message handlers directory
        handler_files = glob.glob(os.path.join(handlers_dir, '*.py'))

        # Extract the handler types from the file names
        return [os.path.basename(f)[:-11] for f in handler_files if not f.endswith(('__init__.py', 'base_handler.py'))]

    def log_user_interaction(self) -> None:
        """
        Logs the user's interaction with the bot.

        This method logs the details of the message received from the user, 
        including the user's name, username, and the content of their message.
        """
        user_message = self.update.message.text or "sent a photo, file, video or voice."
        print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) said: {user_message}')

    def is_balance_insufficient(self) -> bool:
        """
        Checks if the user's balance is insufficient for further interactions.

        :return: True if balance is insufficient, False otherwise.
        """
        if self.conversation.balance <= 0:
            print("Insufficient balance.")
            return True
        return False

    async def prompt_for_payment(self) -> None:
        """
        Sends a message to the user prompting for payment due to insufficient balance.

        This method is called when the user's balance is not enough to continue
        using the bot's services.
        """
        await self.context.bot.send_message(self.update.message.chat_id, _("Insufficient balance to use the service."))
        await self.payment.send_invoice(self.update, self.context, False)

    # Exception Handling Methods

    async def handle_bad_request(self, exception: BadRequest) -> None:
        """
        Handles BadRequest exceptions from the Telegram API.

        :param exception: The BadRequest exception.
        """
        error_message = str(exception)
        if "File is too big" in error_message:
            file_size_limit = ConstraintsChecker.MAX_FILE_SIZE
            file_type_message = _("file")

            if self.update.message.video:
                file_size_limit = ConstraintsChecker.MAX_VIDEO_FILE_SIZE
                file_type_message = _("video file")
            
            file_size_limit_mb = file_size_limit / (1024 * 1024)  # Convert bytes to MB
            await self.context.bot.send_message(self.update.message.chat_id, _("The {file_type} you are trying to send is too large. The maximum allowed size is {size_limit:.2f} MB.").format(file_type=file_type_message, size_limit=file_size_limit_mb))
        else:
            print(f"Unhandled BadRequest: {error_message}")
            raise

    async def handle_general_exception(self, session: SessionLocal, exception: Exception) -> None:
        """
        Handles general exceptions that occur during interaction.

        :param session: Database session for managing transactions.
        :param exception: The exception that occurred.
        """
        error_message = str(exception)
        print(f"Error: {exception}")
        
        self.thread_run_manager = ThreadRunManager(self.openai, self.update, self.context, self.conversation, session, self.update.message.chat_id)

        if "Error code: 404" in error_message and "No thread found with id" in error_message:
            self.thread_run_manager.create_thread(session, self.conversation)
        elif "Failed to index file: Unsupported file" in error_message:
            self.thread_run_manager.recreate_thread(session, self.conversation)
        elif "Can't add messages to thread_" in error_message:
            thread_id, run_id = Helpers.get_thread_id_and_run_id_from_string(error_message)
            self.thread_run_manager.cancel_run(thread_id, run_id)
        else:
            raise exception

    def error_handler(self, update: Update, context: CallbackContext) -> None:
        """
        Handles any uncaught errors during update processing.

        :param update: Telegram update object.
        :param context: Telegram context object with error details.
        """
        logger = logging.getLogger(__name__)
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        return False

    # Post-Interaction Methods

    async def update_balance_and_cleanup(self, session: SessionLocal) -> None:
        """
        Updates the user's balance and cleans up any temporary files.

        :param session: Database session for transactions.
        """
        if self.conversation:
            messages = self.openai.beta.threads.messages.list(thread_id=self.conversation.thread_id, limit=100)
            amount = self.tokenizer.calculate_thread_total_amount(messages)

            print(f'---->>> Conversation balance decreased by: ${amount} for input text')
            self.conversation.balance -= amount
            self.conversation.updated_at = datetime.utcnow()
            session.commit()
            Helpers.cleanup_folder(f'tmp/{self.conversation.thread_id}')

    # Run Method

    def run(self) -> None:
        """
        Starts the bot and begins polling for updates.
        """
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
