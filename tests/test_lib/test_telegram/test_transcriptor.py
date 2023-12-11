import unittest
from unittest.mock import Mock, patch, mock_open
from lib.telegram.transcriptor import Transcriptor
from decimal import Decimal

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

        # Setup for Transcriptor instance
        self.transcriptor = Transcriptor(self.mock_openai_client, self.mock_update, self.mock_context, self.mock_conversation)


    @patch('lib.telegram.text_extractor.TextExtractor.extract_text')
    def test_transcript_document(self, mock_extract_text):
        file_path = "path/to/document"
        mock_extract_text.return_value = "Mocked extracted text"

        success = self.transcriptor.transcript_document(file_path)

        mock_extract_text.assert_called_once_with(file_path)
        self.assertTrue(success)
        self.mock_openai_client.beta.threads.messages.create.assert_called_once()


    def test_transcript_image(self):
        file = Mock(file_path="path/to/image")
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked Content"))]
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        self.transcriptor.transcript_image(file)

        self.mock_openai_client.chat.completions.create.assert_called_once()
        self.mock_bot.send_message.assert_called_once_with('chat_id', "Mocked Content")
        self.mock_openai_client.beta.threads.messages.create.assert_called_once()


    @patch('builtins.open', new_callable=mock_open)
    def test_transcript_voice(self, mock_file):
        file_path = "path/to/audio"
        self.mock_openai_client.audio.transcriptions.create.return_value = "Mocked Transcription"
        
        self.transcriptor.transcript_voice(file_path)

        mock_file.assert_called_once_with(file_path, "rb")
        self.mock_openai_client.audio.transcriptions.create.assert_called_once()
        self.mock_bot.send_message.assert_called_once_with('chat_id', "Mocked Transcription")
        self.mock_openai_client.beta.threads.messages.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
