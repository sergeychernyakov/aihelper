from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db.models.conversation import Conversation
from lib.telegram.messages_handler import MessagesHandler
from lib.openai.runs_treads_handler import RunsTreadsHandler
from lib.telegram.transcriptor import Transcriptor
from lib.telegram.helpers import Helpers
from lib.openai.tokenizer import Tokenizer
from lib.localization import _, change_language
from lib.telegram.bots.base_bot import BaseBot

class TranslatorBot(BaseBot):
    def __init__(self):
        super().__init__()
        # additional init

    async def message_handler(self, update, context):
        successful_interaction = False

        with self.session_scope() as session:
            print(f'{update.message.from_user.first_name}({update.message.from_user.username}) said: {update.message.text or "sent a photo, file, video or voice."}')
            try:
                conversation = session.query(Conversation).filter_by(
                    user_id=update.message.from_user.id,
                    assistant_id=self.ASSISTANT_ID
                ).first() or self._create_conversation(session, update)
                
                change_language(conversation.language_code)

                if conversation.balance <= 0:
                    print("Insufficient balance.")
                    await context.bot.send_message(update.message.chat_id, _("Insufficient balance to use the service."))
                    await self.payment.send_invoice(update, context, False)
                    return False

                runs_treads_handler = RunsTreadsHandler(self.openai, update, context, conversation, session, update.message.chat_id)
                if datetime.utcnow() - conversation.updated_at >= runs_treads_handler.thread_recreation_interval:
                    runs_treads_handler.recreate_thread(session, conversation)

                message_handler = MessagesHandler(self.openai, update, context, conversation)
                transcriptor = Transcriptor(self.openai, update, context, conversation)

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
                    transcriptor.assistant = self.assistant
                    success, message, file = await message_handler.handle_document_message()
                    if not success:
                        await context.bot.send_message(update.message.chat_id, message)
                    else:
                        await transcriptor.transcript_document(file)

                if successful_interaction:
                    tokenizer = Tokenizer()
                    messages = self.openai.beta.threads.messages.list(thread_id=conversation.thread_id, limit=100)
                    amount = tokenizer.calculate_thread_total_amount(messages)

                    if not tokenizer.has_sufficient_balance_for_amount(amount, conversation.balance):
                        print("Insufficient balance.")
                        await context.bot.send_message(update.message.chat_id, _("Insufficient balance to process the message."))
                        await self.payment.send_invoice(update, context, False)
                        return False

                    print(f'---->>> Conversation balance decreased by: ${amount} for input text')
                    conversation.balance -= amount

                    await runs_treads_handler.create_run()
                    conversation.updated_at = datetime.utcnow()
                    session.commit()

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

    async def start(self, update: Update, context: CallbackContext) -> None:    
        with self.session_scope() as session:
            user_id = update.message.from_user.id
            conversation = session.query(Conversation).filter_by(
                user_id=user_id,
                assistant_id=self.ASSISTANT_ID
            ).first()

            if not conversation:
                conversation = self._create_conversation(session, update)
                print(f"New conversation created with ID: {conversation.id}")

            if conversation:
                change_language(conversation.language_code)

            current_balance = conversation.balance

        start_balance = Tokenizer.START_BALANCE
        initial_welcome_message = _(
            "Welcome to the Russian-Ukrainian AI Translator! "
            "My name is Nova and I can assist you with various tasks. Here's what you can do:\n\n"
            "Speak with me like with friend :)\n"
            "Translate various texts from/to Russian/Ukrainian\n"
            "Translate voice messages\n"
            "Translate audio/video files\n"
            "Translate text, pdf and other documents\n"
            "Generate images\n"
            "I speak your language\n\n"
        )
        initial_welcome_message += _(
            "Balance:\n"
            "Your start balance is ${0:.2f} - we'll ask to refill the balance when you'll use it in full.\n"
            "Your current balance is ${1:.2f}.\n\n"
        ).format(start_balance, current_balance)
        initial_welcome_message += _(
            "Contacts:\n"
            "- For advertising inquiries, contact @AIBotsAdv\n"
            "- For investment-related questions, contact @AIBotsInvest\n"
            "- For development of intelligent bots, write to @AIBotsTech\n"
            "- Support: @AIBotsTech\n\n"
            "Available Actions:\n"
        )

        # Buttons and the remaining part of the welcome message
        keyboard = [
            [
                InlineKeyboardButton(_("Check Balance"), callback_data='balance'),
                InlineKeyboardButton(_("Top Up Balance"), callback_data='invoice'),
                InlineKeyboardButton(_("Finish Session"), callback_data='finish')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the initial part of the welcome message
        await context.bot.send_message(update.message.chat_id, initial_welcome_message, reply_markup=reply_markup)

        remaining_welcome_message = _(
            "/balance - Check your current balance\n"
            "/invoice - Top up your balance\n"
            "/start - Show welcome message again\n"
            "/finish - Finish your current session\n\n"
            "Enjoy your experience with our service!\n"
            "Check our video tutorial."
        )

        # Send the remaining part of the welcome message with buttons
        await context.bot.send_message(update.message.chat_id, remaining_welcome_message)
        await context.bot.send_message(update.message.chat_id, 'https://youtu.be/_L1mFH_V-0o')
