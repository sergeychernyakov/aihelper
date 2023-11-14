import time
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters
from openai import OpenAI
from dotenv import load_dotenv
import os
from contextlib import contextmanager
from db.engine import SessionLocal, engine
from db.models.conversation import Conversation
from db.base import Base

load_dotenv()

openai = OpenAI()

MAX_FILE_SIZE = 5.0 * 1024 * 1024  # 5 MB in bytes
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_DIMENSION_SIZE = 2000  # Max pixels for the longest side
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# ASSISTANT_ID = 'asst_9ZDWRdmAfABY2iCYEf7Tf5Je' # Ruby developer assistant gpt-4-1106-preview
# ASSISTANT_ID = 'asst_g9QxbJRApkJyERHaVHBxSiRo' # Python developer assistant gpt-4-1106-preview
# ASSISTANT_ID = 'asst_vI0acJWUvRz5VGugqsA8qkbO' # ukrainian-russian translator assistant gpt-4-1106-preview
ASSISTANT_ID = 'asst_X6NsU7jjgYRQzFx4cATu0znZ' # ukrainian-russian translator assistant gpt-3.5-turbo-1106


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def text_handler(update, context):
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """
    with session_scope() as session:

        # Print to console
        print(f'{update.message.from_user.first_name}({update.message.from_user.username}) wrote {update.message.text}')

        print(f'{update.message}')

        create_run = False

        conversation = session.query(Conversation).filter_by(user_id=update.message.from_user.id, assistant_id=ASSISTANT_ID).first()
        if conversation is None:

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

        if update.message.text is not None:
          print(f'{update.message.from_user.first_name}({update.message.from_user.username}) wrote: "{update.message.text}"')
          message = openai.beta.threads.messages.create(
              thread_id=conversation.thread_id,
              role="user",
              content=update.message.text
          )
          create_run = True

        elif update.message.photo is not None:
            # take the photo near to 512x512px for vision low res mode
            photo = update.message.photo[-2]
            file = context.bot.get_file(photo.file_id)

            print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size} {photo.width}x{photo.height} "{update.message.caption}"')

            # Extract file extension
            _, file_extension = os.path.splitext(file.file_path)

            caption = update.message.caption or "Что на этой картинке? Если на картинке есть текст - выведи его."

            # Check if the file extension is allowed
            if file_extension.lower() not in ALLOWED_EXTENSIONS:
                context.bot.send_message(
                    update.message.chat_id,
                    f'This type of file is not supported. We currently support PNG (.png), JPEG (.jpeg and .jpg), WEBP (.webp), and non-animated GIF (.gif)'
                )
                return
            elif file.file_size >= MAX_FILE_SIZE:
                # Convert the max file size from bytes to megabytes for the message
                max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
                file_size_mb = file.file_size / (1024 * 1024)

                # Send a message to the user with file sizes in megabytes
                context.bot.send_message(
                    update.message.chat_id,
                    f'The file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
                )
                return
            elif photo.width > MAX_DIMENSION_SIZE or photo.height > MAX_DIMENSION_SIZE: # Check the photo dimensions
                context.bot.send_message(
                    update.message.chat_id,
                    'The image is too large. Please upload an image with a maximum length or width of 2000 pixels.'
                )
                return
            else:
                print(f'image passed checks: "{file.file_path}" {file.file_size}')

                response = openai.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                          "role": "user",
                          "content": [
                              { "type": "text", "text": caption },
                              { "type": "image_url", "image_url": { "url": file.file_path } }
                          ],
                        }
                    ],
                    max_tokens=300
                )

                openai.beta.threads.messages.create(
                    thread_id=conversation.thread_id,
                    role="user",
                    content=caption
                )

                context.bot.send_message(
                    update.message.chat_id,
                    response.choices[0].message.content
                )

                openai.beta.threads.messages.create(
                    thread_id=conversation.thread_id,
                    role="user",
                    content=response.choices[0].message.content
                )

                create_run = True


        # if update.message.document is not None:
        #     document = update.message.document
        #     file = context.bot.get_file(document.file_id)

        #     print(f'{update.message.from_user.first_name}({update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size}')

        #     # Extract file extension
        #     _, file_extension = os.path.splitext(file.file_path)

        #     # Ensure the directory exists before trying to download
        #     download_dir_path = f'tmp/{conversation.thread_id}'
        #     os.makedirs(download_dir_path, exist_ok=True)

        #     # Download the file to the desired location with the extracted extension
        #     download_path = f'{download_dir_path}/photo{file_extension}'
        #     file.download(download_path)

        #     create_run = True

        if create_run:
          run = openai.beta.threads.runs.create(
              thread_id=conversation.thread_id,
              assistant_id=conversation.assistant_id
          )

          while run.status !="completed":
              run = openai.beta.threads.runs.retrieve(
                thread_id=conversation.thread_id,
                run_id=run.id
              )

          messages = openai.beta.threads.messages.list(
              thread_id=conversation.thread_id
          )

          print(f'AI responded: {messages.data[0].content[0].text.value}')

          context.bot.send_message(
              update.message.chat_id,
              messages.data[0].content[0].text.value
          )

          conversation.updated_at = datetime.utcnow()

        pass


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, text_handler))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
