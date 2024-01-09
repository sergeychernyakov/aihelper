from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.localization import _

class VoiceHandler(BaseHandler):

    MESSAGE_TYPE = 'voice'

    async def handle_message(self) -> bool:
        """Handle an incoming voice message.
        
        Extracts the voice from the update and processes it.
        Returns a tuple indicating success and a message.
        """
        voice = self.update.message.voice
        if not voice:
            return False, _("No voice message provided.")

        file_info = await self.context.bot.get_file(voice.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info):
            return False

        amount = self.tokenizer.tokens_to_money_from_voice(voice.duration)
        if not await self._check_sufficient_balance(amount):
            return False

        return await self.process_message(file_info.file_path, voice.duration)
