import time

from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from openai import OpenAI
from dotenv import load_dotenv
from db.engine import SessionLocal, engine
from db.models.conversation import Conversation
from db.base import Base

load_dotenv()

# Ensure all tables are created
Base.metadata.create_all(bind=engine)

session = SessionLocal()

openai = OpenAI()

ASSISTANT_ID = 'asst_9ZDWRdmAfABY2iCYEf7Tf5Je'

def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    # Print to console
    print(f'{update.message.from_user.first_name}({update.message.from_user.username}) wrote {update.message.text}')

    conversation = session.query(Conversation).filter_by(user_id=update.message.from_user.id, assistant_id=ASSISTANT_ID).first()
    if conversation is None:
        print("No conversation found for the given user_id and assistant_id.")
        thread = openai.beta.threads.create()

        conversation = Conversation(user_id=update.message.from_user.id, language_code=update.message.from_user.language_code, username=update.message.from_user.username, thread_id=thread.id, assistant_id=ASSISTANT_ID)

        # Add and commit the new conversation
        session.add(conversation)
        session.commit()
    else:
        print("Conversation found:", conversation)

    # Close the session
    session.close()

    message = openai.beta.threads.messages.create(
        thread_id=conversation.thread_id,
        role="user",
        content=update.message.text
    )

    run = openai.beta.threads.runs.create(
        thread_id=conversation.thread_id,
        assistant_id=conversation.assistant_id
    )

    while run.status !="completed":
        time.sleep(3)
        run = openai.beta.threads.runs.retrieve(
          thread_id=conversation.thread_id,
          run_id=run.id
        )

    messages = openai.beta.threads.messages.list(
        thread_id=thread_id
    )

    print(f'AI responded {messages.data[0].content[0].text.value}')

    context.bot.send_message(
        update.message.chat_id,
        messages.data[0].content[0].text.value
    )


def main() -> None:
    updater = Updater("TELEGRAM_TOKEN_REDACTED")

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
