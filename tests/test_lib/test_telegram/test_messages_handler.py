import os
import unittest
from unittest.mock import Mock, patch
from lib.telegram.messages_handler import MessagesHandler
from decimal import Decimal
from pathlib import Path

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
        self.mock_conversation.balance = Decimal('10.0')  # Assign a Decimal value to balance

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
        voice_duration = 10  # Set a specific duration in seconds
        self.mock_update.message.voice = Mock(file_id='voice_file_id', duration=voice_duration)
        self.mock_bot.get_file.return_value = Mock(file_path="path/to/voice.mp3", file_size=2048)

        success, message, file_path, _ = self.handler.handle_voice_message()
        self.assertTrue(success)
        self.assertEqual(message, "Voice processed successfully")
        mock_check_constraints.assert_called_once()
        mock_makedirs.assert_called_once()

    @patch('os.makedirs')
    @patch('lib.telegram.constraints_checker.ConstraintsChecker.check_document_constraints')
    def test_handle_document_message(self, mock_check_constraints, mock_makedirs):
        # Set up mock return values and conditions
        mock_check_constraints.return_value = (True, "Success")
        document_extension = ".pdf"
        self.mock_update.message.document = Mock(file_id='document_file_id')
        self.mock_bot.get_file.return_value = Mock(file_path=f"path/to/document{document_extension}", file_size=3072)

        # Call the method under test
        success, message, file_path = self.handler.handle_document_message()

        # Assertions
        self.assertTrue(success)
        self.assertEqual(message, "Document processed successfully")
        mock_check_constraints.assert_called_once()
        mock_makedirs.assert_called_once()

        # Verify that get_file was called with the correct file_id
        self.mock_bot.get_file.assert_called_once_with('document_file_id')

        # Constructing the expected download path using a relative path
        document_extension = ".pdf"  # Assuming document extension is known
        relative_path = os.path.join('tmp', self.mock_conversation.thread_id, f'document{document_extension}')
        expected_download_path = Path(relative_path).resolve()

        self.assertEqual(file_path, expected_download_path)


if __name__ == '__main__':
    unittest.main()
