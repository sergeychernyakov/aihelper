from lib.telegram.message_handlers.base_handler import BaseHandler
from lib.localization import _
from lib.telegram.new_transcriptor import NewTranscriptor
from lib.text_extractor import TextExtractor

class DocumentHandler(BaseHandler):
    MESSAGE_TYPE = 'document'

    async def _translate_text(self, text: str, caption: str) -> str:
        # Split the extracted text into smaller pieces and translate each piece
        translated_text = ""
        total_tokens = 0
        num_pieces = (len(text) + NewTranscriptor.MAX_MESSAGE_LENGTH - 1) // NewTranscriptor.MAX_MESSAGE_LENGTH
        for i in range(num_pieces):
            start_index = i * NewTranscriptor.MAX_MESSAGE_LENGTH
            end_index = start_index + NewTranscriptor.MAX_MESSAGE_LENGTH
            text_piece = text[start_index:end_index]
            translated_text, total_tokens = self._create_openai_non_thread_message(f'{caption}: {text_piece}')
            translated_text += translated_text + "\n\n"
            total_tokens += total_tokens

        return translated_text, total_tokens

    async def handle_message(self) -> bool:
        """Handle an incoming document message."""
        document = self.update.message.document
        if not document:
            return False, _("No document provided.")

        file_info = await self.context.bot.get_file(document.file_id)
        self._log_user_interaction(file_info)

        if not await self._check_constraints(file_info):
            return False

        caption = self.update.message.caption or _("Translate this document:")

        return await self.process_message(file_info.file_path, caption)

    async def process_message(self, file_path: str, caption: str) -> bool:
        """Process the document message."""
        local_file_path = await self._download_file(file_path)
        if not local_file_path:
            return False, _("Failed to download the document.")
        extracted_text = TextExtractor.extract_text(str(local_file_path)) 
        caption_amount = self.tokenizer.tokens_to_money_from_string(caption)
        amount = caption_amount + self.tokenizer.tokens_to_money_from_string(extracted_text)
        if not await self._check_sufficient_balance(amount):
            return False

        translated_text, total_tokens = await self._translate_text(extracted_text, caption)
        # Truncate the text for Telegram message and send a notification about the full text
        truncated_text = (translated_text[:200] + _("... (truncated)\n\n")) if len(translated_text) > 200 else translated_text

        await self._send_chat_message(truncated_text + _("Full translated text has been sent as a document."))
        await self.answer.answer_with_document(translated_text)
        self._update_balance(total_tokens, caption_amount)
        return True
