import unittest
from unittest.mock import Mock, patch
from lib.telegram.messages_handler import MessagesHandler

class TestMessagesHandler(unittest.TestCase):

    def setUp(self):
        # Mock dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_bot = Mock()
        self.mock_update.message = Mock()
        self.mock_context.bot = self.mock_bot

        # Mock conversation with thread_id attribute
        self.mock_conversation = Mock()
        self.mock_conversation.thread_id = 'thread_id'

        # Setup for MessagesHandler instance
        self.handler = MessagesHandler(self.mock_openai_client, self.mock_update, self.mock_context, self.mock_conversation)

    def test_handle_text_message(self):
        message = "Test message"
        self.handler.handle_text_message(message)

        self.mock_openai_client.beta.threads.messages.create.assert_called_once_with(
            thread_id='thread_id', role="user", content=message)

    @patch('lib.telegram.constraints_checker.ConstraintsChecker.check_photo_constraints')
    def test_handle_photo_message(self, mock_check_constraints):
        mock_check_constraints.return_value = (True, "Success")
        self.mock_update.message.photo = [Mock(), Mock(width=512, height=512, file_id='file_id')]
        self.mock_bot.get_file.return_value = Mock(file_path="path/to/photo", file_size=1024)

        success, message, file = self.handler.handle_photo_message()
        self.assertTrue(success)
        self.assertEqual(message, "Image processed successfully")
        mock_check_constraints.assert_called_once()

    @patch('os.makedirs')
    @patch('lib.telegram.constraints_checker.ConstraintsChecker.check_voice_constraints')
    def test_handle_voice_message(self, mock_check_constraints, mock_makedirs):
        mock_check_constraints.return_value = (True, "Success")
        self.mock_update.message.voice = Mock(file_id='voice_file_id')
        self.mock_bot.get_file.return_value = Mock(file_path="path/to/voice.mp3", file_size=2048)

        success, message, file_path = self.handler.handle_voice_message()
        self.assertTrue(success)
        self.assertEqual(message, "Voice processed successfully")
        mock_check_constraints.assert_called_once()
        mock_makedirs.assert_called_once()

    # Similar tests for handle_document_message

    # Additional test cases for error handling and constraint failure scenarios

if __name__ == '__main__':
    unittest.main()
