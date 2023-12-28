import os
from dotenv import load_dotenv
from telegram import LabeledPrice, Update
from telegram.ext import CallbackContext
from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.telegram.assistant import Assistant
from decimal import Decimal
from lib.localization import _

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
    
    assistant = Assistant()
    ASSISTANT_ID = assistant.get_assistant_id()

    @staticmethod
    async def send_invoice(update: Update, context: CallbackContext, from_button: False) -> None:
        """
        Sends an invoice to a user for payment.

        Parameters:
        update (Update): The update instance containing message details.
        context (CallbackContext): Context object passed by the Telegram bot framework.
        from_button (Bool): Indicates if this function is called from a button press.

        This method constructs an invoice with a predefined title, description, and price,
        then sends it to the user using the bot's context.
        """
            # Determine the chat_id and user_id based on how the function was called
        if from_button:
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.message.chat_id

        title = _("Пополнение баланса")
        description = _("Пополнение баланса переводчика.")
        currency = "USD"
        prices = [LabeledPrice(_("Пополненить баланс"), 1*100)]

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
            await query.answer(ok=False, error_message=_("Something went wrong..."))
        else:
            await query.answer(ok=True)

    @staticmethod
    async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
        """
        Confirms the successful completion of a payment and updates the user's conversation balance.

        Parameters:
        update (Update): The update instance containing successful payment details.
        context (CallbackContext): Context object passed by the Telegram bot framework.
        """
        # Extract payment amount from the successful payment update
        payment_amount = Decimal(update.message.successful_payment.total_amount) / 100  # Assuming amount is in cents

        # Create a new database session
        session = SessionLocal()
        try:
            user_id = update.message.from_user.id
            # Query for the conversation
            conversation = session.query(Conversation).filter_by(
                user_id=update.message.from_user.id,
                assistant_id=Payment.ASSISTANT_ID
            ).first()

            if conversation:
                # Update the conversation balance
                conversation.balance += payment_amount
                session.commit()  # Commit the transaction
                await update.message.reply_text(_("Thank you for your payment! Your balance has been updated by ${0:.2f}.").format(payment_amount))
            else:
                # Handle case where conversation does not exist
                await update.message.reply_text(_("Error: No active conversation found for payment update."))

        except Exception as e:
            # Handle any exceptions that occur during the database operation
            session.rollback()  # Rollback the transaction in case of error
            raise e
        finally:
            session.close()  # Ensure the session is closed
