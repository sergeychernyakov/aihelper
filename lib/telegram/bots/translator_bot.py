import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lib.openai.tokenizer import Tokenizer
from lib.localization import _, change_language
from lib.telegram.bots.base_bot import BaseBot
from lib.telegram.payment import Payment
from lib.openai.assistant import Assistant

class TranslatorBot(BaseBot):
    """
    DietBot is a custom Telegram bot for handling various types of messages
    and translating or processing them using OpenAI's API.
    """
    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path='.env.translator', override=True)
        super().__init__()

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
