import os
from dotenv import load_dotenv
from telegram import LabeledPrice, Update
from telegram.ext import CallbackContext
from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.telegram.assistant import Assistant
from decimal import Decimal
from lib.localization import _, change_language
from lib.currency_converter import CurrencyConverter

# Load environment variables
load_dotenv()

class Payment:
    """
    Handles payment processing through Telegram using YOOKASSA.

    Attributes:
    YOOKASSA_API_TOKEN (str): Class-level attribute that stores the Stripe API token.
    PAYLOAD (str): Constant payload string used to validate payment callbacks.

    Methods:
    send_invoice: Sends an invoice to a user in a chat.
    precheckout_callback: Handles the pre-checkout query, ensuring the payload is correct.
    successful_payment_callback: Confirms and responds to a successful payment.

    Note:
    Ensure that the YOOKASSA_API_TOKEN environment variable is set correctly for payment processing.
    This class assumes that the python-telegram-bot framework is used for the bot implementation.
    """

    YOOKASSA_API_TOKEN = os.getenv('YOOKASSA_API_TOKEN')
    PAYLOAD = "Custom-Payload"
    
    assistant = Assistant()
    ASSISTANT_ID = assistant.get_assistant_id()

    @staticmethod
    async def send_invoice(update: Update, context: CallbackContext, from_button: False) -> None:
        if from_button:
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.message.chat_id

        title = _("Top Up Balance")
        description = _("Top Up the Balance of the Translator.")
        currency = "RUB"
        prices = [LabeledPrice(_("Top Up the Balance"), 100*100)]

        await context.bot.send_invoice(
            chat_id, title, description, Payment.PAYLOAD, Payment.YOOKASSA_API_TOKEN, currency, prices
        )

    @staticmethod
    async def precheckout_callback(update: Update, context: CallbackContext) -> None:
        query = update.pre_checkout_query
        if query.invoice_payload != Payment.PAYLOAD:
            await query.answer(ok=False, error_message=_("Something went wrong..."))
        else:
            await query.answer(ok=True)

    @staticmethod
    async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
        currency = update.message.successful_payment.currency
        payment_amount = Decimal(update.message.successful_payment.total_amount) / 100
        
        print()

        session = SessionLocal()
        try:
            conversation = session.query(Conversation).filter_by(
                user_id=update.message.from_user.id,
                assistant_id=Payment.ASSISTANT_ID
            ).first()

            if conversation:
                change_language(conversation.language_code)

                conversion_rate = CurrencyConverter.get_conversion_rate(currency, 'USD')
                conversation.balance += payment_amount * conversion_rate
                session.commit()
                await update.message.reply_text(_("Thank you for your payment! Your balance has been updated by {0:.2f} {1}.").format(payment_amount, currency))
                await update.message.reply_text(_("Your current balance is: ${0:.2f}").format(conversation.balance))
            else:
                await update.message.reply_text(_("Error: No active conversation found for payment update."))

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
