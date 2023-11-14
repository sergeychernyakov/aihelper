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

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# ASSISTANT_ID = 'asst_9ZDWRdmAfABY2iCYEf7Tf5Je' # Ruby developer assistant
ASSISTANT_ID = 'asst_g9QxbJRApkJyERHaVHBxSiRo' # Python developer assistant

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

        conversation = session.query(Conversation).filter_by(user_id=update.message.from_user.id, assistant_id=ASSISTANT_ID).first()
        if conversation is None:

            thread = openai.beta.threads.create()

            conversation = Conversation(user_id=update.message.from_user.id, language_code=update.message.from_user.language_code, username=update.message.from_user.username, thread_id=thread.id, assistant_id=ASSISTANT_ID)

            # Add and commit the new conversation
            session.add(conversation)

        # if update.message.text is not None:
        #   message = openai.beta.threads.messages.create(
        #       thread_id=conversation.thread_id,
        #       role="user",
        #       content=update.message.text
        #   )

        if update.message.photo is not None:
          print(update.message.photo[-1])
          file = context.bot.get_file(update.message.photo[-1].file_id)
          print("file_id: " + str(update.message.photo[-1].file_id))
          print(file)
          file.download('tmp/photo.jpg')

        if update.message.document is not None:
          print(update.message.document)
          file = context.bot.get_file(update.message.document.file_id)
          print("file_id: " + str(update.message.document.file_id))
          file.download('tmp/' + update.message.document.file_name)

        # run = openai.beta.threads.runs.create(
        #     thread_id=conversation.thread_id,
        #     assistant_id=conversation.assistant_id
        # )

        # while run.status !="completed":
        #     run = openai.beta.threads.runs.retrieve(
        #       thread_id=conversation.thread_id,
        #       run_id=run.id
        #     )

        # messages = openai.beta.threads.messages.list(
        #     thread_id=conversation.thread_id
        # )

        # print(f'AI responded: {messages.data[0].content[0].text.value}')

        # context.bot.send_message(
        #     update.message.chat_id,
        #     messages.data[0].content[0].text.value
        # )

        # conversation.updated_at = datetime.utcnow()

        # pass


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
