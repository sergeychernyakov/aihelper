import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
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
from datetime import datetime
import warnings
from urllib3.exceptions import InsecureRequestWarning

load_dotenv()

# Initialize the Assistant
assistant = Assistant()

# Get OpenAI client and Assistant ID from the Assistant instance
openai = assistant.get_openai_client()

ASSISTANT_ID = assistant.get_assistant_id()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Suppress only the single InsecureRequestWarning from urllib3
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

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

    # Add and commit the new conversation
    session.add(conversation)

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
def message_handler(update, context):
    successful_interaction = False

    with session_scope() as session:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) said: {update.message.text or "sent a photo, file, video or voice."}')

        

        try:
            # Check for existing conversation or create a new one
            conversation = session.query(Conversation).filter_by(
                user_id=update.message.from_user.id,
                assistant_id=ASSISTANT_ID
            ).first() or _create_conversation(session, update)

            print(f'!!!!!!! conversation.thread_id: {conversation.thread_id}')

            runs_treads_handler = RunsTreadsHandler(openai, update, context, conversation, session)
            if datetime.utcnow() - conversation.updated_at >= runs_treads_handler.thread_recreation_interval:
                # Recreate thread if interval has passed
                runs_treads_handler.recreate_thread(session, conversation)

            print(f'!!!!!!! conversation.thread_id: {conversation.thread_id}')

            message_handler = MessagesHandler(openai, update, context, conversation)
            transcriptor = Transcriptor(openai, update, context, conversation)

            # Handle different types of messages
            if update.message.text:
                if message_handler.handle_text_message(update.message.text):
                    successful_interaction = True
            elif update.message.photo:
                success, message, file = message_handler.handle_photo_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction = transcriptor.transcript_image(file)
            elif update.message.video:
                success, message, file = message_handler.handle_video_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction = transcriptor.transcript_video(file)
            elif update.message.voice:
                success, message, file, amount =  message_handler.handle_voice_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction = transcriptor.transcript_voice(file, amount)
            elif update.message.document:
                success, message, file = message_handler.handle_document_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    successful_interaction = transcriptor.transcript_document(file)

            if successful_interaction:
                tokenizer = Tokenizer()
                messages = openai.beta.threads.messages.list(thread_id=conversation.thread_id, limit=100)
                amount = tokenizer.calculate_thread_total_amount(messages)

                # Check if the balance is sufficient
                if not tokenizer.has_sufficient_balance_for_amount(amount, conversation.balance):
                    print("Insufficient balance.")
                    context.bot.send_message(update.message.chat_id, "Insufficient balance to process the message.")
                    return False

                # Update the balance
                print(f'---->>> Conversation balance decreased by: ${amount} for input text')
                conversation.balance -= amount

                runs_treads_handler.create_run()
                # Update the conversation's timestamp after a successful interaction
                conversation.updated_at = datetime.utcnow()
                session.commit() # Make sure to commit only once after all updates

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

def ping(update: Update, context: CallbackContext) -> None:
    print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent ping.')
    context.bot.send_message(update.message.from_user.id, 'pong')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('ping', ping))

    # Echo any message that is not a command
    updater.dispatcher.add_handler(MessageHandler(~Filters.command, message_handler))

    # Register the error handler
    updater.dispatcher.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the bot receives a shutdown signal
    updater.idle()

if __name__ == '__main__':
    main()
