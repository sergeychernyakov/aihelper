import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, CallbackContext
from telegram.error import BadRequest
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.openai.thread_run_manager import ThreadRunManager
from lib.openai.assistant import Assistant
from lib.telegram.payment import Payment
from lib.telegram.helpers import Helpers
from lib.openai.tokenizer import Tokenizer
from lib.constraints_checker import ConstraintsChecker
from datetime import datetime
from lib.localization import _, change_language

class NewBaseBot:
    def __init__(self):
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

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('ping', self.ping))
        self.application.add_handler(CommandHandler('balance', self.balance))
        self.application.add_handler(CommandHandler('finish', self.finish))
        self.application.add_handler(CallbackQueryHandler(self.button))
        self.application.add_handler(CommandHandler('invoice', self.send_invoice))
        self.application.add_handler(PreCheckoutQueryHandler(self.payment.precheckout_callback))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.payment.successful_payment_callback))
        self.application.add_handler(MessageHandler(~filters.COMMAND, self.message_handler))
        self.application.add_error_handler(self.error_handler)

    def _create_conversation(self, session, update):
        thread = self.openai.beta.threads.create()

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

    def _get_or_create_conversation(self, session):
        return (session.query(Conversation).filter_by(
                    user_id=self.update.message.from_user.id,
                    assistant_id=Assistant.ASSISTANT_ID).first() or 
                self._create_conversation(session, self.update))

    def log_user_interaction(self):
        user_message = self.update.message.text or "sent a photo, file, video or voice."
        print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) said: {user_message}')

    @contextmanager
    def session_scope(self):
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            print(f"An error occurred during session transaction: {e}")
            session.rollback()
        finally:
            session.close()

    def is_balance_insufficient(self):
        if self.conversation.balance <= 0:
            print("Insufficient balance.")
            return True
        return False

    async def prompt_for_payment(self):
        await self.context.bot.send_message(self.update.message.chat_id, _("Insufficient balance to use the service."))
        await self.payment.send_invoice(self.update, self.context, False)

    async def message_handler(self, update, context):
        raise NotImplementedError("This method should be overridden in a subclass")

    async def handle_interaction(self, session):
        try:
            self.conversation = self._get_or_create_conversation(session)
            change_language(self.conversation.language_code)

            if self.is_balance_insufficient():
                await self.prompt_for_payment()
                return False

            return await self.process_message(session)
        except BadRequest as e:
            await self.handle_bad_request(e)
        except Exception as e:
            await self.handle_general_exception(session, e)

    async def handle_bad_request(self, exception):
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

    async def handle_general_exception(self, session, exception):
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

    async def update_balance_and_cleanup(self, session):
        if self.conversation:
            messages = self.openai.beta.threads.messages.list(thread_id=self.conversation.thread_id, limit=100)
            amount = self.tokenizer.calculate_thread_total_amount(messages)

            print(f'---->>> Conversation balance decreased by: ${amount} for input text')
            self.conversation.balance -= amount
            self.conversation.updated_at = datetime.utcnow()
            session.commit()
            Helpers.cleanup_folder(f'tmp/{self.conversation.thread_id}')

    def error_handler(self, update, context):
        logger = logging.getLogger(__name__)
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        return False

    async def ping(self, update: Update, context: CallbackContext) -> None:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent ping.')
        await context.bot.send_message(update.message.from_user.id, 'pong')

    async def start(self, update: Update, context: CallbackContext) -> None:
        raise NotImplementedError("This method should be overridden in a subclass")

    async def finish(self, update: Update, context: CallbackContext, from_button=False) -> None:
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

    async def balance(self, update: Update, context: CallbackContext, from_button=False) -> None:
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

            print(conversation.username)
            print(f'conversation amount: {conversation.balance} user_id: {user_id}')

            if conversation:
                change_language(conversation.language_code)

                balance_amount = conversation.balance
                await context.bot.send_message(chat_id, _("Your current balance is: ${0:.2f}").format(balance_amount))
            else:
                print(f'No active conversation found, chat_id: {chat_id}')

    async def button(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == 'balance':
            await self.balance(update, context, from_button=True)
        elif callback_data == 'invoice':
            await self.payment.send_invoice(update, context, from_button=True)
        elif callback_data == 'finish':
            await self.finish(update, context, from_button=True)

    async def send_invoice(self, update: Update, context: CallbackContext):
        await self.payment.send_invoice(update, context, from_button=False)

    def run(self):
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
