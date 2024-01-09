import os
import requests
from pathlib import Path
from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.localization import _

class VideoHandler(BaseHandler):
    MESSAGE_TYPE = 'video'

    def _calculate_total_amount(self, video) -> int:
        """Calculate the amount needed for processing the video."""
        amount = self.tokenizer.tokens_to_money_from_video(video.duration)
        if self.update.message.caption:
            amount += self.tokenizer.tokens_to_money_from_string(self.update.message.caption)
        return amount

    async def handle_message(self) -> bool:
        """Handle an incoming video message."""
        video = self.update.message.video
        if not video:
            return False, _("No video message provided.")

        file_info = await self.context.bot.get_file(video.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info):
            return False

        amount = self._calculate_total_amount(video)
        if not await self._check_sufficient_balance(amount):
            return False

        local_file_path = await self._download_file(file_info.file_path)
        if not local_file_path:
            return False, _("Failed to download the video.")

        return await self.process_message(local_file_path, video.duration)

    async def process_message(self, file_path: str, duration: int) -> bool:
        """Process the video message."""
        transcripted_text, total_tokens = await self.transcriptor.transcript_video(file_path, duration, self.update.message.caption)
        self._update_balance(total_tokens)
        self.__create_openai_thread_message(_('Translate: ') + transcripted_text)
        return True
