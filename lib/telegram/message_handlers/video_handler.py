from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.openai.tokenizer import Tokenizer
from decimal import Decimal

class VideoHandler(BaseHandler):
    MESSAGE_TYPE = 'video'

    def _calculate_total_amount(self, video) -> int:
        """
        Calculate the total cost required for processing the video based on its duration and caption.

        :param video: A video object from the Telegram update message.
        :return: The calculated amount as an integer.
        """
        amount = self.tokenizer.tokens_to_money_from_video(video.duration)
        if self.update.message.caption:
            amount += self.tokenizer.tokens_to_money_from_string(self.update.message.caption)
        return amount

    async def handle_message(self) -> bool:
        """
        Handle the processing of a video message received from a user.

        This method checks various constraints, downloads the video file, and processes it. 
        It returns a boolean indicating the success of the operation.

        :return: True if the video message is processed successfully, False otherwise.
        """
        video = self.update.message.video
        if not video:
            print(_("No video message provided."))
            return False

        file_info = await self.context.bot.get_file(video.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info):
            return False

        amount = self._calculate_total_amount(video)
        if not await self._check_sufficient_balance(amount):
            return False

        local_file_path = await self._download_file(file_info.file_path)
        if not local_file_path:
            print(_("Failed to download the video."))
            return False

        return await self.process_message(local_file_path, amount, self.update.message.caption)

    async def process_message(self, file_path, amount: Decimal = Tokenizer.MINIMUM_COST, caption: str = None) -> bool:
        """
        Process the message and update the conversation thread based on its type.

        :param args: Arguments needed for processing the message, e.g., file, caption, duration.
        :return: Boolean indicating if the message was processed successfully.
        """
        transcripted_text, total_tokens = await self.transcriptor.transcript_video(file_path, caption)

        # Update balance and create a thread message
        self._update_balance(total_tokens, amount)
        self._create_openai_thread_message(_('Translate: ') + transcripted_text)

        return True
