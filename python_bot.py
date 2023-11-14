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
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

openai = OpenAI()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ASSISTANT_ID = os.getenv('PYTHON_ASSISTANT_ID')


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


def create_new_conversation(session, update):

    thread = openai.beta.threads.create()

    new_conversation = Conversation(
        user_id=update.message.from_user.id, 
        language_code=update.message.from_user.language_code,
        username=update.message.from_user.username,
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    session.add(new_conversation)
    
    return new_conversation


def respond_to_user(conversation, update, context):

    message = openai.beta.threads.messages.create(
        thread_id=conversation.thread_id,
        role="user",
        content=update.message.text)

    run = openai.beta.threads.runs.create(
        thread_id=conversation.thread_id,
        assistant_id=conversation.assistant_id)

    while run.status !="completed":
        run = openai.beta.threads.runs.retrieve(
            thread_id=conversation.thread_id,
            run_id=run.id)

    messages = openai.beta.threads.messages.list(
        thread_id=conversation.thread_id)

    print(f'AI responded: {messages.data[0].content[0].text.value}')

    context.bot.send_message(
        update.message.chat_id,
        messages.data[0].content[0].text.value
    )

    conversation.updated_at=datetime.utcnow()


def text_handler(update, context):
    
    with session_scope() as session:

        conversation = session.query(Conversation).filter_by(
            user_id=update.message.from_user.id,
            assistant_id=ASSISTANT_ID).first() or create_new_conversation(session, update)

        if update.message.text:
            respond_to_user(conversation, update, context)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    updater.dispatcher.add_handler(MessageHandler(~Filters.command, text_handler))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
