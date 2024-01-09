from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.localization import _

class PhotoHandler(BaseHandler):

    MESSAGE_TYPE = 'photo'

    def _calculate_total_amount(self, caption: str) -> int:
        """Calculate the total amount needed for processing the photo and its caption."""
        amount = self.tokenizer.tokens_to_money_from_image()
        if caption:
            amount += self.tokenizer.tokens_to_money_from_string(caption)
        return amount

    async def handle_message(self) -> bool:
        """Handle an incoming photo message."""
        photo = self.update.message.photo[-2] if self.update.message.photo else None
        if not photo:
            return False, _("No image provided.")

        file_info = await self.context.bot.get_file(photo.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info, photo):
            return False

        caption = self.update.message.caption or _("What's in this image? If there's text, extract it and translate.")
        amount = self._calculate_total_amount(caption)

        if not await self._check_sufficient_balance(amount):
            return False

        return await self.process_message(file_info.file_path, caption)
