from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.openai.tokenizer import Tokenizer
from decimal import Decimal
from lib.localization import _

class VoiceHandler(BaseHandler):

    MESSAGE_TYPE = 'voice'

    async def handle_message(self) -> bool:
        """Handle an incoming voice message.

        Extracts the voice from the update and processes it.
        Returns True if successful, False otherwise.
        """
        voice = self.update.message.voice
        if not voice:
            print(_("No voice message provided."))
            return False

        file_info = await self.context.bot.get_file(voice.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info):
            return False

        amount = self.tokenizer.tokens_to_money_from_voice(voice.duration)
        if not await self._check_sufficient_balance(amount):
            return False

        local_file_path = await self._download_file(file_info.file_path)
        if not local_file_path:
            print(_("Failed to download the voice message."))
            return False

        return await self.process_message(local_file_path, amount)

    async def process_message(self, file_path, amount: Decimal = Tokenizer.MINIMUM_COST) -> bool:
        """
        Process the message and update the conversation thread based on its type.

        :param args: Arguments needed for processing the message, e.g., file, caption, duration.
        :return: Boolean indicating if the message was processed successfully.
        """
        transcripted_text = await self.transcriptor.transcript_voice(file_path)

        # Update balance and create a thread message
        self._update_balance(0, amount)
        self._create_openai_thread_message(transcripted_text)

        return True
