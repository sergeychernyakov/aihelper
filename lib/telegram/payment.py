import os
from dotenv import load_dotenv
from telegram import LabeledPrice, Update
from telegram.ext import CallbackContext

# Load environment variables
load_dotenv()

class Payment:
    """
    Handles payment processing through Telegram using Stripe.

    This class provides methods to send invoices, handle pre-checkout, and confirm successful payments
    in a Telegram bot context. It uses Stripe for payment processing and requires a valid Stripe API token.
    The class methods are designed to be integrated with the python-telegram-bot framework.

    Attributes:
    STRIPE_API_TOKEN (str): Class-level attribute that stores the Stripe API token.
    PAYLOAD (str): Constant payload string used to validate payment callbacks.

    Methods:
    send_invoice: Sends an invoice to a user in a chat.
    precheckout_callback: Handles the pre-checkout query, ensuring the payload is correct.
    successful_payment_callback: Confirms and responds to a successful payment.

    Note:
    Ensure that the STRIPE_API_TOKEN environment variable is set correctly for payment processing.
    This class assumes that the python-telegram-bot framework is used for the bot implementation.
    """

    # Class-level constant for Stripe API token
    STRIPE_API_TOKEN = os.getenv('STRIPE_API_TOKEN')
    # Constant payload used for validating payment callbacks
    PAYLOAD = "Custom-Payload"

    @staticmethod
    async def send_invoice(update: Update, context: CallbackContext) -> None:
        """
        Sends an invoice to a user for payment.

        Parameters:
        update (Update): The update instance containing message details.
        context (CallbackContext): Context object passed by the Telegram bot framework.

        This method constructs an invoice with a predefined title, description, and price,
        then sends it to the user using the bot's context.
        """
        chat_id = update.message.chat_id
        title = "Payment Example"
        description = "Payment Example using python-telegram-bot"
        currency = "USD"
        price = 1  # price in dollars
        prices = [LabeledPrice("Test", price * 100)]

        await context.bot.send_invoice(
            chat_id, title, description, Payment.PAYLOAD, Payment.STRIPE_API_TOKEN, currency, prices
        )

    @staticmethod
    async def precheckout_callback(update: Update, context: CallbackContext) -> None:
        """
        Handles the pre-checkout process of a payment.

        Parameters:
        update (Update): The update instance containing pre-checkout query details.
        context (CallbackContext): Context object passed by the Telegram bot framework.

        This method validates the pre-checkout query to ensure it matches the expected payload.
        If the validation fails, it responds with an error message.
        """
        query = update.pre_checkout_query
        if query.invoice_payload != Payment.PAYLOAD:
            await query.answer(ok=False, error_message="Something went wrong...")
        else:
            await query.answer(ok=True)

    @staticmethod
    async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
        """
        Confirms the successful completion of a payment.

        Parameters:
        update (Update): The update instance containing successful payment details.
        context (CallbackContext): Context object passed by the Telegram bot framework.

        This method is triggered after a successful payment, and it can be used to
        acknowledge the payment and perform any post-payment processing.
        """
        await update.message.reply_text("Thank you for your payment!")
