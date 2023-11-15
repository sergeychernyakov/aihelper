import time
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from openai import OpenAI
from dotenv import load_dotenv
import os
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from db.engine import SessionLocal
from db.models.conversation import Conversation

load_dotenv()

openai = OpenAI()

MAX_FILE_SIZE = 5.0 * 1024 * 1024  # 5 MB in bytes
ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_VOICE_EXTENSIONS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.oga'}
MAX_DIMENSION_SIZE = 2000  # Max pixels for the longest side
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ASSISTANT_ID = os.getenv('URT_ASSISTANT_ID')  # Use the assistant id from the environment variable

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

def handle_text_message(update, thread_id):
    try:
        # Logic to handle text messages and execute OpenAI API calls
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) wrote: "{update.message.text}"')
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=update.message.text
        )

        return True  # Return True on successful execution
    except Exception as e:
        print(f"Error: {e}")
        return False  # Return False on failure

def handle_photo_message(update, context):
    try:
        # take the photo near to 512x512px for vision low res mode
        photo = update.message.photo[-2]
        file = context.bot.get_file(photo.file_id)
        print(f"Function - Mock File ID: {id(file)}, Mock Photo ID: {id(photo)}")

        success, message = check_file_constraints(file, photo)
        if not success:
            return False, message, None

        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size} {photo.width}x{photo.height} "{update.message.caption}"')

        message = "Image processed successfully"
        return True, message, file
    except Exception as e:
        print(f"Error: {e}")
        return False, 'Some error occured while image processing', None # Return False on failure

def handle_voice_message(update, context, thread_id):
    try:
        # Logic to handle voice messages and execute OpenAI API calls
        voice = update.message.voice
        file = context.bot.get_file(voice.file_id)

        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent voice: "{file.file_path}" {file.file_size}')

        success, message = check_voice_constraints(file, voice)
        if not success:
            return False, message, None

        # Extract file extension
        _, file_extension = os.path.splitext(file.file_path)

        # Ensure the directory exists before trying to download
        download_dir_path = f'tmp/{thread_id}'
        os.makedirs(download_dir_path, exist_ok=True)

        # Download the file to the desired location with the extracted extension
        download_path = f'{download_dir_path}/voice{file_extension}'
        file.download(download_path)

        message = "Voice processed successfully"
        return True, message, download_path
    except Exception as e:
        print(f"Error: {e}")
        return False, 'Some error occured while voice processing', None # Return False on failure

def handle_document_message(update, context):
    if update.message.document:
        document = update.message.document
        file = context.bot.get_file(document.file_id)

        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size}')

        # Extract file extension
        _, file_extension = os.path.splitext(file.file_path)

        # Ensure the directory exists before trying to download
        download_dir_path = f'tmp/{conversation.thread_id}'
        os.makedirs(download_dir_path, exist_ok=True)

        # Download the file to the desired location with the extracted extension
        download_path = f'{download_dir_path}/photo{file_extension}'
        file.download(download_path)

def transcript_image(update, context, thread_id, file):

    caption = update.message.caption or "Что на этой картинке? Если на картинке есть текст - выведи его."

    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
              "role": "user",
              "content": [
                  { "type": "text", "text": caption },
                  { "type": "image_url", "image_url": { "url": file.file_path, "detail": "low" } }
              ],
            }
        ],
        max_tokens=100
    )

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=caption
    )

    context.bot.send_message(
        update.message.chat_id,
        response.choices[0].message.content
    )

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content='Переведи текст на украинский язык: "' + response.choices[0].message.content + '"'
    )

def transcript_voice(update, context, thread_id, file_path):
    audio_file= open(file_path, "rb")
    transcription = openai.audio.transcriptions.create(
      model="whisper-1",
      file=audio_file,
      response_format="text"
    )

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=transcription
    )

    context.bot.send_message(
        update.message.chat_id,
        transcription
    )

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content='Переведи текст на украинский язык: "' + transcription + '"'
    )

def check_file_constraints(file, photo):
    file_extension = os.path.splitext(file.file_path)[1]
    if file_extension.lower() not in ALLOWED_PHOTO_EXTENSIONS:
        return False, "Unsupported file type."
    if file.file_size >= MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        file_size_mb = file.file_size / (1024 * 1024)
        return False, f'The file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
    if photo.width > MAX_DIMENSION_SIZE or photo.height > MAX_DIMENSION_SIZE:
        return False, "Image dimensions are too large."
    return True, ""

def check_voice_constraints(file, voice):
    file_extension = os.path.splitext(file.file_path)[1]
    if file_extension.lower() not in ALLOWED_VOICE_EXTENSIONS:
        return False, "Unsupported file type."
    if file.file_size >= MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        file_size_mb = file.file_size / (1024 * 1024)
        return False, f'The file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
    return True, ""

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

    print(f'AI responded: {messages.data[0].content[0].text.value}')

    context.bot.send_message(
        update.message.chat_id,
        messages.data[0].content[0].text.value
    )


def message_handler(update, context):
    successful_interaction = False

    with session_scope() as session:
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) said: {update.message.text or "sent a photo, file or voice."}')

        print(update.message)

        # Check for existing conversation or create a new one
        conversation = session.query(Conversation).filter_by(
            user_id=update.message.from_user.id,
            assistant_id=ASSISTANT_ID
        ).first() or create_conversation(session, update)

        # Handle different types of messages
        if update.message.text:
            if handle_text_message(update, conversation.thread_id):
                successful_interaction = True
        elif update.message.photo:
            success, message, file = handle_photo_message(update, context)
            if not success:
                context.bot.send_message(update.message.chat_id, message)
            else:
                transcript_image(update, context, conversation.thread_id, file)
                successful_interaction = True
        elif update.message.voice:
            success, message, file = handle_voice_message(update, context, conversation.thread_id)
            if not success:
                context.bot.send_message(update.message.chat_id, message)
            else:
                transcript_voice(update, context, conversation.thread_id, file)
                successful_interaction = True

        if successful_interaction:
            create_run(conversation.thread_id, conversation.assistant_id, update, context)
            # Update the conversation's timestamp after a successful interaction
            conversation.updated_at = datetime.utcnow()
            session.commit() # Make sure to commit only once after all updates


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Echo any message that is not a command
    updater.dispatcher.add_handler(MessageHandler(~Filters.command, message_handler))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the bot receives a shutdown signal
    updater.idle()

if __name__ == '__main__':
    main()
