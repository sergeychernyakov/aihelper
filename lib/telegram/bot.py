import logging
import time

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI()

logger = logging.getLogger(__name__)

# Pre-assign menu text
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

# Pre-assign button text
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

# Build keyboards
FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)
]])
SECOND_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
    [InlineKeyboardButton(TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
])


def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    # Print to console
    print(f'{update.message.from_user.first_name}({update.message.from_user.username}) wrote {update.message.text}')

    # This is equivalent to forwarding, without the sender's name
    # update.message.copy(update.message.chat_id)

    # messages = [
    #   {"role": "system", "content": "Ты полезный помощник"},
    #   {"role": "user", "content": update.message.text}
    # ]

    # response = openai.chat.completions.create(
    #   model = "gpt-3.5-turbo-16k-0613",
    #   messages = messages
    # )

    # print(f'AI responded {response.choices[0].message.content}')

    # context.bot.send_message(
    #     update.message.chat_id,
    #     response.choices[0].message.content
    # )


#####################  assistant_id: asst_rM8zJIWjSQMgE5JTCKbZY3cd, thread_id: thread_KrI5g5lwXwlr1Cepc1ihVYLh, run_id: run_MPJjQlTd9iroeF7ME4Gxao6n
    thread_id = 'thread_KrI5g5lwXwlr1Cepc1ihVYLh'
    run_id = 'run_MPJjQlTd9iroeF7ME4Gxao6n'
    assistant_id = 'asst_9ZDWRdmAfABY2iCYEf7Tf5Je' #'asst_rM8zJIWjSQMgE5JTCKbZY3cd'

    # assistant = openai.beta.assistants.create(
    #     name="Ruby Developer",
    #     instructions="You are a professional ruby developer with greate expirience. Write and run code to answer ruby questions.",
    #     tools=[{"type": "code_interpreter"}],
    #     model="gpt-4-1106-preview"
    # )

    # thread = openai.beta.threads.create()

    # message = openai.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="user",
    #     content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
    # )

    # run = openai.beta.threads.runs.create(
    #     thread_id=thread.id,
    #     assistant_id=assistant.id,
    #     instructions="Please address the user as Jane Doe. The user has a premium account."
    # )

    # run = openai.beta.threads.runs.retrieve(
    #     thread_id=thread.id,
    #     run_id=run.id
    # )

    # save assistant_id and thread_id to database
    # create new thread if there is no thread with user
    # assistant_id may be the same?

    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=update.message.text
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while run.status !="completed":
        time.sleep(3)
        run = openai.beta.threads.runs.retrieve(
          thread_id=thread_id,
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







def menu(update: Update, context: CallbackContext) -> None:
    """
    This handler sends a menu with the inline buttons we pre-assigned above
    """

    context.bot.send_message(
        update.message.from_user.id,
        FIRST_MENU,
        parse_mode=ParseMode.HTML,
        reply_markup=FIRST_MENU_MARKUP
    )


def button_tap(update: Update, context: CallbackContext) -> None:
    """
    This handler processes the inline buttons on the menu
    """

    data = update.callback_query.data
    text = ''
    markup = None

    if data == NEXT_BUTTON:
        text = SECOND_MENU
        markup = SECOND_MENU_MARKUP
    elif data == BACK_BUTTON:
        text = FIRST_MENU
        markup = FIRST_MENU_MARKUP

    # Close the query to end the client-side loading animation
    update.callback_query.answer()

    # Update message content with corresponding menu section
    update.callback_query.message.edit_text(
        text,
        ParseMode.HTML,
        reply_markup=markup
    )


def main() -> None:
    updater = Updater("TELEGRAM_TOKEN_REDACTED")

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("menu", menu))

    # Register handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
