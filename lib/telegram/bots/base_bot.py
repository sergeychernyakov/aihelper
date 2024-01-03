import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, CallbackContext
from dotenv import load_dotenv
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.openai.runs_treads_handler import RunsTreadsHandler
from lib.openai.assistant import Assistant
from lib.telegram.payment import Payment
from lib.localization import _, change_language

class BaseBot:
    def __init__(self):
        load_dotenv()
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.assistant = Assistant()
        self.payment = Payment()
        self.openai = self.assistant.get_openai_client()
        self.ASSISTANT_ID = self.assistant.get_assistant_id()
        self.application = Application.builder().token(self.TELEGRAM_BOT_TOKEN).build()
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
            assistant_id=self.ASSISTANT_ID
        )

        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        print(f"New conversation created at: {conversation.updated_at}")
        return conversation

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

    def error_handler(self, update, context):
        logger = logging.getLogger(__name__)
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        return False

    async def message_handler(self, update, context):
        raise NotImplementedError("This method should be overridden in a subclass")

    async def ping(self, update: Update, context: CallbackContext) -> None:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent ping.')
        await context.bot.send_message(update.message.from_user.id, 'pong')

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
                    assistant_id=self.ASSISTANT_ID
                ).first()

                if conversation:
                    change_language(conversation.language_code)

                    await context.bot.send_message(chat_id, _('Goodbye! If you need assistance again, just send me a message.'))

                    runs_treads_handler = RunsTreadsHandler(self.openai, update, context, conversation, session, chat_id)
                    runs_treads_handler.recreate_thread(session, conversation)
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
                assistant_id=self.ASSISTANT_ID
            ).first()

            if conversation:
                change_language(conversation.language_code)

                balance_amount = conversation.balance
                await context.bot.send_message(chat_id, _("Your current balance is: ${0:.2f}").format(balance_amount))
            else:
                print(f'No active conversation found, chat_id: {chat_id}')

    async def start(self, update: Update, context: CallbackContext) -> None:
        raise NotImplementedError("This method should be overridden in a subclass")

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
