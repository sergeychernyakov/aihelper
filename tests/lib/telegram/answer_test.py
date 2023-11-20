import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
from lib.telegram.answer import Answer

class TestAnswer(unittest.TestCase):

    def setUp(self):
        # Mock the dependencies
        self.mock_openai_client = Mock()
        self.mock_context = Mock()
        self.mock_bot = Mock()
        self.mock_context.bot = self.mock_bot
        # Setup for Answer instance
        self.answer = Answer(self.mock_openai_client, self.mock_context, 'chat_id', 'thread_id')

    def test_answer_with_text(self):
        message = "Hello, world!"
        self.answer.answer_with_text(message)
        self.mock_bot.send_message.assert_called_once_with('chat_id', message)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_answer_with_voice(self, mock_makedirs, mock_file):
        message = "Hello, world!"
        # Simulate a response from openai_client
        self.mock_openai_client.audio.speech.create.return_value = Mock(stream_to_file=Mock())

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('lib.telegram.answer.__file__', new=temp_dir + '/answer.py'):
                result = self.answer.answer_with_voice(message)

        self.mock_openai_client.audio.speech.create.assert_called_once_with(model="tts-1", voice="nova", input=message)
        self.mock_bot.send_document.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()

if __name__ == '__main__':
    unittest.main()
