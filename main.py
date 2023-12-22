import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning from urllib3
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

import os
import logging
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler
from dotenv import load_dotenv
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from db.engine import SessionLocal
from db.models.conversation import Conversation
from lib.telegram.messages_handler import MessagesHandler
from lib.telegram.runs_treads_handler import RunsTreadsHandler
from lib.telegram.transcriptor import Transcriptor
from lib.telegram.helpers import Helpers
from lib.telegram.tokenizer import Tokenizer
from lib.telegram.assistant import Assistant
from lib.telegram.payment import Payment

load_dotenv()

# Initialize the Assistant
assistant = Assistant()

# Get OpenAI client and Assistant ID from the Assistant instance
openai = assistant.get_openai_client()

ASSISTANT_ID = assistant.get_assistant_id()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# private

######### Create conversation method #########
def _create_conversation(session, update):
    thread = openai.beta.threads.create()

    conversation = Conversation(
        user_id=update.message.from_user.id,
        language_code=update.message.from_user.language_code,
        username=update.message.from_user.username,
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Add the new conversation
    session.add(conversation)
    # Commit the session to save changes
    session.commit()
    # Refresh the conversation object to get the latest state from the database
    session.refresh(conversation)
    
    print(f"New conversation created at: {conversation.updated_at}")
    
    return conversation

######### Session #########
@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        print(f"An error occurred during session transaction: {e}")
        session.rollback()
    finally:
        session.close()

######### Error handlers methods #########
def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger = logging.getLogger(__name__)
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    return False

######### Main message handler ######### move to MessagesHandler
async def message_handler(update, context):
    successful_interaction = False

    with session_scope() as session:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) said: {update.message.text or "sent a photo, file, video or voice."}')

        try:
            # Check for existing conversation or create a new one
            conversation = session.query(Conversation).filter_by(
                user_id=update.message.from_user.id,
                assistant_id=ASSISTANT_ID
            ).first() or _create_conversation(session, update)
            
            print(f"Updated at: {conversation.updated_at}, Current time: {datetime.utcnow()}")

            runs_treads_handler = RunsTreadsHandler(openai, update, context, conversation, session, update.message.chat_id)
            if datetime.utcnow() - conversation.updated_at >= runs_treads_handler.thread_recreation_interval:
                # Recreate thread if interval has passed
                runs_treads_handler.recreate_thread(session, conversation)

            message_handler = MessagesHandler(openai, update, context, conversation)
            transcriptor = Transcriptor(openai, update, context, conversation)

            # Handle different types of messages
            if update.message.text:
                if message_handler.handle_text_message(update.message.text):
                    successful_interaction = True
            elif update.message.photo:
                success, message, file = await message_handler.handle_photo_message()
                if not success:
                    await context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction = await transcriptor.transcript_image(file)
            elif update.message.video:
                success, message, file = await message_handler.handle_video_message()
                if not success:
                    await context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction, message = await transcriptor.transcript_video(file)
                    if not successful_interaction:
                        await context.bot.send_message(update.message.chat_id, message)
            elif update.message.voice:
                success, message, file, amount = await message_handler.handle_voice_message()
                if not success:
                    await context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction, message = await transcriptor.transcript_voice(file, amount)
                    if not successful_interaction:
                        await context.bot.send_message(update.message.chat_id, message)
            elif update.message.document:
                transcriptor.assistant = assistant
                success, message, file = await message_handler.handle_document_message()
                if not success:
                    await context.bot.send_message(update.message.chat_id, message)
                else:
                    await transcriptor.transcript_document(file)
                    # no need to run thread - already answered to the chat.

            if successful_interaction:
                tokenizer = Tokenizer()
                messages = openai.beta.threads.messages.list(thread_id=conversation.thread_id, limit=100)
                amount = tokenizer.calculate_thread_total_amount(messages)

                # Check if the balance is sufficient
                if not tokenizer.has_sufficient_balance_for_amount(amount, conversation.balance):
                    print("Insufficient balance.")
                    await context.bot.send_message(update.message.chat_id, "Insufficient balance to process the message.")
                    return False

                # Update the balance
                print(f'---->>> Conversation balance decreased by: ${amount} for input text')
                conversation.balance -= amount

                await runs_treads_handler.create_run()
                # Update the conversation's timestamp after a successful interaction
                conversation.updated_at = datetime.utcnow()
                session.commit() # Make sure to commit only once after all updates

            Helpers.cleanup_folder(f'tmp/{conversation.thread_id}')

        except Exception as e:
            error_message = str(e)
            print(f"Error: {e}")
            if "Error code: 404" in error_message and "No thread found with id" in error_message:
                runs_treads_handler.create_thread(session, conversation)
            elif "Failed to index file: Unsupported file" in error_message:
                runs_treads_handler.recreate_thread(session, conversation)
            elif "Can't add messages to thread_" in error_message:
                thread_id, run_id = Helpers.get_thread_id_and_run_id_from_string(error_message)
                runs_treads_handler.cancel_run(thread_id, run_id)
            else:
                raise

async def ping(update: Update, context: CallbackContext) -> None:
    print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent ping.')
    await context.bot.send_message(update.message.from_user.id, 'pong')

async def finish(update: Update, context: CallbackContext, from_button=False) -> None:
    """
    Handle the /finish command or button press. Sends a goodbye message to the user and recreates the conversation thread.

    :param update: The Telegram update object.
    :param context: The context object provided by the Telegram bot framework.
    :param from_button: Indicates if this function is called from a button press.
    """
    if from_button:
        chat_id = update.callback_query.message.chat_id
        user_id = update.callback_query.from_user.id
    else:
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

    with session_scope() as session:
        try:
            conversation = session.query(Conversation).filter_by(
                user_id=user_id,
                assistant_id=ASSISTANT_ID
            ).first()

            if conversation:
                await context.bot.send_message(chat_id, 'Goodbye! If you need assistance again, just send me a message.')

                # Create the RunsTreadsHandler using the correct chat_id
                runs_treads_handler = RunsTreadsHandler(openai, update, context, conversation, session, chat_id)

                runs_treads_handler.recreate_thread(session, conversation)
            else:
                await context.bot.send_message(chat_id, 'No active conversation found.')

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            await context.bot.send_message(chat_id, 'An error occurred while processing your request.')

async def balance(update: Update, context: CallbackContext, from_button=False) -> None:
    """
    Respond to the /balance command or button press by sending the current balance of the user's conversation.

    :param update: The Telegram update object.
    :param context: The context object provided by the Telegram bot framework.
    :param from_button: Indicates if this function is called from a button press.
    """
    # Determine the chat_id and user_id based on how the function was called
    if from_button:
        chat_id = update.callback_query.message.chat_id
        user_id = update.callback_query.from_user.id
    else:
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

    with session_scope() as session:
        # Retrieve the conversation for the user
        conversation = session.query(Conversation).filter_by(
            user_id=user_id,
            assistant_id=ASSISTANT_ID
        ).first()

        # Existing logic to send balance information
        if conversation:
            balance_amount = conversation.balance
            await context.bot.send_message(chat_id, f'Your current balance is: ${balance_amount:.2f}')
        else:
            await context.bot.send_message(chat_id, 'No active conversation found.')

async def start(update: Update, context: CallbackContext) -> None:    
    with session_scope() as session:
        # Check for an existing conversation or create a new one
        user_id = update.message.from_user.id
        conversation = session.query(Conversation).filter_by(
            user_id=user_id,
            assistant_id=ASSISTANT_ID
        ).first()

    if not conversation:
        conversation = _create_conversation(session, update)
        print(f"New conversation created with ID: {conversation.id}")

    # Initial part of the welcome message
    start_balance = Tokenizer.START_BALANCE
    initial_welcome_message = (
        "Welcome to the Russian-Ukrainian Translating AI Bot!"
        "My name is Nova and I can assist you with various tasks. Here's what you can do:\n\n"
        "Speak with me like with friend :)\n"
        "Translate various texts from/to Russian/Ukrainian\n"
        "Translate voice messages\n"
        "Translate audio/video files\n"
        "Translate text, pdf and other documents\n"
        "Generate images\n"
        "We speak your language\n\n"
        f"Balance:\n"
        f"Your start balance is ${start_balance:.2f} - we'll ask to refill the balance when you'll use it in full.\n\n"
        "Contacts:\n"
        "- For advertising inquiries, contact @AIBotsAdv\n"
        "- For investment-related questions, contact @AIBotsInvest\n"
        "- For development of intelligent bots, write to @AIBotsTech\n"
        "- Support: @AIBotsTech\n"
        "- Try our other bots: @phpgpt, @rubygpt, @pythongpt\n\n"
        "Available Actions:\n"
    )

    # Buttons and the remaining part of the welcome message
    keyboard = [
        [InlineKeyboardButton("Check Balance", callback_data='balance'), InlineKeyboardButton("Finish Session", callback_data='finish')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the initial part of the welcome message
    await context.bot.send_message(update.message.chat_id, initial_welcome_message, reply_markup=reply_markup)

    remaining_welcome_message = (
        "/balance - Check your current balance\n"
        "/start - Show welcome message again\n"
        "/finish - Finish your current session\n\n"
        "Enjoy your experience with our AI Helper Bot!\n"
        "Check our video tutorial."
    )

    # Send the remaining part of the welcome message with buttons
    await context.bot.send_message(update.message.chat_id, remaining_welcome_message)

    # Send a welcome video
    video_path = 'welcome_video.mov'
    with open(video_path, 'rb') as video:
        await context.bot.send_video(update.message.chat_id, video)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == 'balance':
        await balance(update, context, from_button=True)
    elif callback_data == 'finish':
        await finish(update, context, from_button=True)

def main() -> None:
    payment = Payment()

    # Create an instance of the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ping', ping))
    application.add_handler(CommandHandler('balance', balance))
    application.add_handler(CommandHandler('finish', finish))
    application.add_handler(CallbackQueryHandler(button))

    # Payments handling
    payment = Payment()
    application.add_handler(CommandHandler('invoice', payment.send_invoice))
    application.add_handler(PreCheckoutQueryHandler(payment.precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment.successful_payment_callback))

    # General message handling
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))

    # Error handling
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
