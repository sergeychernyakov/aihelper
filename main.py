import time
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters
from openai import OpenAI
from dotenv import load_dotenv
import os
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from db.engine import SessionLocal
from db.models.conversation import Conversation
import random
import shutil
import logging
from lib.telegram.messages_handler import MessagesHandler
from lib.telegram.transcriptor import Transcriptor

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ASSISTANT_ID = os.getenv('URT_ASSISTANT_ID')  # Use the assistant id from the environment variable

openai = OpenAI()

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

# ######### Transcriptors for different types of messages #########
# def transcript_document(update, context, thread_id, assistant_id, file_path):
#     try:
#       caption = update.message.caption or "Что в этом файле? Если в файле есть текст, переведи его на украинский язык."

#       # Upload a file with an "assistants" purpose
#       file = openai.files.create(
#           file=open(file_path, "rb"),
#           purpose='assistants'
#       )

#       openai.beta.threads.messages.create(
#           thread_id=thread_id,
#           role="user",
#           content=caption,
#           file_ids=[file.id]
#       )

#       openai.beta.threads.messages.create(
#           thread_id=thread_id,
#           role="user",
#           content=caption
#       )

#       return True, 'File sent for transcription'
#     except Exception as e:
#         raise

# def transcript_image(update, context, thread_id, file):

#     caption = update.message.caption or "Что на этой картинке? Если на картинке есть текст - выведи его."

#     response = openai.chat.completions.create(
#         model="gpt-4-vision-preview",
#         messages=[
#             {
#               "role": "user",
#               "content": [
#                   { "type": "text", "text": caption },
#                   { "type": "image_url", "image_url": { "url": file.file_path, "detail": "low" } }
#               ],
#             }
#         ],
#         max_tokens=100
#     )

#     openai.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=caption
#     )

#     context.bot.send_message(
#         update.message.chat_id,
#         response.choices[0].message.content
#     )

#     openai.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content='Не говори о том, что ты не можешь увидеть картинку. Переведи текст на украинский язык: "' + response.choices[0].message.content + '"'
#     )

# def transcript_voice(update, context, thread_id, file_path):
#     audio_file= open(file_path, "rb")
#     transcription = openai.audio.transcriptions.create(
#       model="whisper-1",
#       file=audio_file,
#       response_format="text"
#     )

#     openai.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=transcription
#     )

#     context.bot.send_message(
#         update.message.chat_id,
#         transcription
#     )

#     openai.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content='Переведи текст на украинский язык: "' + transcription + '"'
#     )

######### Answers methods #########
def answer_with_text(context, message, chat_id):
    context.bot.send_message(chat_id, message)

def answer_with_voice(context, message, chat_id, thread_id):

    voice_answer_folder = Path(__file__).parent / 'tmp' / thread_id
    voice_answer_path = voice_answer_folder / "voice_answer.mp3"

    os.makedirs(voice_answer_folder, exist_ok=True)

    response = openai.audio.speech.create(
        model="tts-1", # tts-1-hd
        voice="nova",
        input=message
    )

    response.stream_to_file(voice_answer_path)

    voice_file = open(voice_answer_path, "rb")
    return context.bot.send_document(chat_id, voice_file)

######### Create conversation method #########
def create_conversation(session, update):
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

######### Work with OpenAI threads, runs #########
def create_run(thread_id, assistant_id, update, context):
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while run.status !="completed":
        time.sleep(2)
        run = openai.beta.threads.runs.retrieve(
          thread_id=thread_id,
          run_id=run.id
        )

    messages = openai.beta.threads.messages.list(
        thread_id=thread_id
    )

    response_text = messages.data[0].content[0].text.value
    print(f'AI responded: {response_text}')

    # Define a threshold for a short message, e.g., 100 characters
    short_message_threshold = 100

    # Randomly choose to respond with voice 1 out of 10 times
    if len(response_text) <= short_message_threshold and random.randint(1, 10) == 1:
        answer_with_voice(context, response_text, update.message.chat_id, thread_id)
    else:
        answer_with_text(context, response_text, update.message.chat_id)

    cleanup(thread_id, assistant_id)

def create_thread(session, conversation):
    thread = openai.beta.threads.create()
    session.query(Conversation).filter_by(id=conversation.id).update({"thread_id": thread.id})
    session.commit()

def recreate_thread(session, conversation):
    openai.beta.threads.delete(conversation.thread_id)
    create_thread(session, conversation)

######### Cleanup methods #########
def cleanup(thread_id, assistant_id):
    dir_path = f'tmp/{thread_id}'

    # Check if the directory exists
    if os.path.exists(dir_path):
        # Delete directory and all its contents
        shutil.rmtree(dir_path)
    else:
        print(f'The directory {dir_path} does not exist!')

######### Error handlers methods #########
def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger = logging.getLogger(__name__)
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    return False

######### Main message handler #########
def message_handler(update, context):
    successful_interaction = False

    with session_scope() as session:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) said: {update.message.text or "sent a photo, file or voice."}')

        try:
            # Check for existing conversation or create a new one
            conversation = session.query(Conversation).filter_by(
                user_id=update.message.from_user.id,
                assistant_id=ASSISTANT_ID
            ).first() or create_conversation(session, update)

            message_handler = MessagesHandler(openai, update, context, conversation.thread_id)
            transcriptor = Transcriptor(openai, update, context, conversation.thread_id, conversation.assistant_id)

            # Handle different types of messages
            if update.message.text:
                if message_handler.handle_text_message(update.message.text):
                    successful_interaction = True
            elif update.message.photo:
                success, message, file = message_handler.handle_photo_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    transcriptor.transcript_image(file)
                    successful_interaction = True
            elif update.message.voice:
                success, message, file =  message_handler.handle_voice_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    transcriptor.transcript_voice(file)
                    successful_interaction = True
            elif update.message.document:
                success, message, file =  message_handler.handle_document_message()
                if not success:
                    context.bot.send_message(update.message.chat_id, message)
                else:
                    transcriptor.transcript_document(file)
                    successful_interaction = True

            if successful_interaction:
                create_run(conversation.thread_id, conversation.assistant_id, update, context)
                # Update the conversation's timestamp after a successful interaction
                conversation.updated_at = datetime.utcnow()
                session.commit() # Make sure to commit only once after all updates

        except Exception as e:
            error_message = str(e)
            print(f"Error: {e}")
            if "Error code: 404" in error_message and "No thread found with id" in error_message:
                create_thread(session, conversation)
            elif "Failed to index file: Unsupported file" in error_message:
                recreate_thread(session, conversation)
            else:
                raise

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

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
