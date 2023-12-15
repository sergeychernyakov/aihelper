import unittest
from unittest.mock import Mock, patch, mock_open
from lib.telegram.transcriptor import Transcriptor
from decimal import Decimal
from lib.telegram.answer import Answer

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

    @patch('lib.telegram.text_extractor.TextExtractor.extract_text')
    @patch('lib.telegram.transcriptor.Answer.__init__')
    def test_transcript_document(self, mock_answer_init, mock_extract_text):
        mock_answer_init.return_value = None  # Mock the __init__ method of Answer to do nothing
        file_path = "path/to/document"
        mock_extract_text.return_value = "Mocked extracted text"
        mock_answer_instance = Mock(spec=Answer)  # Create a mock Answer instance

        # Replace the instance method with the mock
        self.transcriptor.answer = mock_answer_instance

        # Mock __create_non_thread_message to return a valid response
        self.transcriptor._Transcriptor__create_non_thread_message = Mock(return_value=("Translated text", 100))

        success = self.transcriptor.transcript_document(file_path)

        mock_extract_text.assert_called_once_with(file_path)
        self.assertTrue(success)
        self.mock_context.bot.send_message.assert_called()
        mock_answer_instance.answer_with_document.assert_called()

    def test_transcript_image(self):
        file = Mock(file_path="path/to/image")
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked Content"))]
        mock_response.usage = Mock(total_tokens=123)  # Set a specific integer for total_tokens

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
