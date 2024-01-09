import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lib.openai.thread_run_manager import ThreadRunManager
from lib.openai.tokenizer import Tokenizer
from lib.localization import _, change_language
from lib.telegram.bots.new_base_bot import NewBaseBot
from lib.telegram.message_handlers.text_handler import TextHandler
from lib.telegram.message_handlers.photo_handler import PhotoHandler
from lib.telegram.message_handlers.voice_handler import VoiceHandler
from lib.telegram.message_handlers.video_handler import VideoHandler
from lib.telegram.message_handlers.document_handler import DocumentHandler

class DietBot(NewBaseBot):
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv('DIET_BOT_TOKEN')
        super().__init__()

    async def message_handler(self, update, context):
        self.update = update
        self.context = context
        with self.session_scope() as session:
            self.log_user_interaction()
            successful_interaction = await self.handle_interaction(session)
            if successful_interaction:
                await self.thread_run_manager.manage_run()
                await self.update_balance_and_cleanup(session)

    # refactor this method
    async def process_message(self, session):
        self.thread_run_manager = ThreadRunManager(self.openai, self.update, self.context, self.conversation, session, self.update.message.chat_id)
        if datetime.utcnow() - self.conversation.updated_at >= self.thread_run_manager.thread_recreation_interval:
            self.thread_run_manager.recreate_thread(session, self.conversation)

        if self.update.message.text:
            text_handler = TextHandler(self.openai, self.update, self.context, self.conversation)
            if text_handler.handle_message(self.update.message.text):
                return True

        elif self.update.message.photo:
            photo_handler = PhotoHandler(self.openai, self.update, self.context, self.conversation)
            success, message = await photo_handler.handle_message()
            if not success:
                await self.context.bot.send_message(self.update.message.chat_id, message)
                return False
            return True

        elif self.update.message.video:
            video_handler = VideoHandler(self.openai, self.update, self.context, self.conversation)
            success, message = await video_handler.handle_message()
            if not success:
                await self.context.bot.send_message(self.update.message.chat_id, message)
                return False
            return True

        elif self.update.message.voice:
            voice_handler = VoiceHandler(self.openai, self.update, self.context, self.conversation)
            success, message = await voice_handler.handle_message()
            if not success:
                await self.context.bot.send_message(self.update.message.chat_id, message)
                return False
            return True

        elif self.update.message.document:
            document_handler = DocumentHandler(self.openai, self.update, self.context, self.conversation)
            success, message = await document_handler.handle_message()
            if not success:
                await self.context.bot.send_message(self.update.message.chat_id, message)
                return False
            return True

        return False

    async def start(self, update: Update, context: CallbackContext) -> None:
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
