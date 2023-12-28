import unittest
from unittest.mock import Mock, AsyncMock, patch, mock_open
from lib.telegram.transcriptor import Transcriptor
from decimal import Decimal
from lib.telegram.answer import Answer
from asyncio import run

class TestTranscriptor(unittest.TestCase):

    def setUp(self):
        # Mock dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_bot = Mock()
        self.mock_update.message = Mock(caption=None, chat_id='chat_id')
        self.mock_context.bot = self.mock_bot

        # Mock conversation object with required attributes
        self.mock_conversation = Mock()
        self.mock_conversation.thread_id = 'thread_id'
        self.mock_conversation.assistant_id = 'assistant_id'
        self.mock_conversation.balance = Decimal('5.0')  # Example balance

        # Mock assistant with a prompt method
        self.mock_assistant = Mock()
        self.mock_assistant.prompt.return_value = "Mocked assistant prompt"

        # Setup for Transcriptor instance
        self.transcriptor = Transcriptor(self.mock_openai_client, self.mock_update, self.mock_context, self.mock_conversation)
        self.transcriptor.assistant = self.mock_assistant  # Use the mocked assistant
        self.transcriptor.context.bot.send_message = AsyncMock()

    @patch('lib.text_extractor.TextExtractor.extract_text')
    @patch('lib.telegram.transcriptor.Answer.__init__', return_value=None)
    def test_transcript_document(self, mock_answer_init, mock_extract_text):
        mock_extract_text.return_value = "Mocked extracted text"
        self.transcriptor.answer = Mock(spec=Answer)
        self.transcriptor.answer.answer_with_document = AsyncMock()
        self.transcriptor.tokenizer.tokens_to_money_from_string = Mock(return_value=0)
        self.transcriptor.tokenizer.has_sufficient_balance_for_amount = Mock(return_value=True)

        # Mock async methods
        self.transcriptor._Transcriptor__send_message = AsyncMock()
        self.transcriptor._Transcriptor__create_non_thread_message = Mock(return_value=("Translated text", 100))

        # Corrected: Expecting a single boolean return value
        success = run(self.transcriptor.transcript_document("path/to/document"))

        mock_extract_text.assert_called_once()
        self.transcriptor.tokenizer.tokens_to_money_from_string.assert_called()
        self.transcriptor.tokenizer.has_sufficient_balance_for_amount.assert_called()
        self.transcriptor._Transcriptor__create_non_thread_message.assert_called()
        self.transcriptor.answer.answer_with_document.assert_awaited()
        self.assertTrue(success)  # Asserting the boolean return value

    def test_transcript_image(self):
        file = Mock(file_path="path/to/image")
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked Content"))]
        mock_response.usage = Mock(total_tokens=123)
        self.mock_openai_client.chat.completions.create.return_value = mock_response

        # Set the mock_bot.send_message to be an AsyncMock
        self.mock_bot.send_message = AsyncMock()

        run(self.transcriptor.transcript_image(file))

        self.mock_openai_client.chat.completions.create.assert_called_once()
        self.mock_openai_client.beta.threads.messages.create.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    def test_transcript_voice(self, mock_file):
        mock_transcription = Mock(return_value="Mocked Transcription")
        self.mock_openai_client.audio.transcriptions.create = mock_transcription

        # No changes for async methods if they are correctly defined as async in your actual class
        self.transcriptor._Transcriptor__create_thread_message = Mock()

        # Run the async method
        run(self.transcriptor.transcript_voice("path/to/audio"))

        # Assertions
        mock_file.assert_called_once_with("path/to/audio", "rb")
        mock_transcription.assert_called_once()  # Change here

        self.transcriptor._Transcriptor__create_thread_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
