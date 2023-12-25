import os
import unittest
from unittest.mock import Mock, AsyncMock, patch
from lib.telegram.messages_handler import MessagesHandler
from decimal import Decimal
from pathlib import Path
import asyncio

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

        # Use AsyncMock for the asynchronous get_file method
        self.mock_bot.get_file = AsyncMock(return_value=Mock(file_path="path/to/photo", file_size=1024))

        loop = asyncio.get_event_loop()
        success, message, file = loop.run_until_complete(self.handler.handle_photo_message())
        self.assertTrue(success)
        self.assertEqual(message, "Image processed successfully")
        mock_check_constraints.assert_called_once()

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('requests.get')
    @patch('os.makedirs')
    @patch('lib.telegram.constraints_checker.ConstraintsChecker.check_voice_constraints')
    def test_handle_voice_message(self, mock_check_constraints, mock_makedirs, mock_requests_get, mock_open):

        mock_check_constraints.return_value = (True, "Success")
        voice_duration = 10
        self.mock_update.message.voice = Mock(file_id='voice_file_id', duration=voice_duration)

        # Mock get_file to return a valid URL for file_path
        mock_file_path = "https://example.com/path/to/voice.mp3"
        self.mock_bot.get_file = AsyncMock(return_value=Mock(file_path=mock_file_path, file_size=2048))

        # Mock the requests.get call to return a successful response
        mock_requests_get.return_value = Mock(status_code=200, content=b'fake voice content')

        # Use the mock_open to mock file writing
        mock_open.return_value = unittest.mock.mock_open().return_value

        loop = asyncio.get_event_loop()
        success, message, file_path, _ = loop.run_until_complete(self.handler.handle_voice_message())

        # Assertions
        self.assertTrue(success)
        self.assertEqual(message, "Voice processed successfully")
        mock_check_constraints.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_requests_get.assert_called_once_with(mock_file_path)
        # Correct the path to match the actual path used in handle_voice_message
        # Make sure the project_root calculation is correct
        project_root = Path(__file__).parent.parent.parent.parent

        # Construct the path as it is done in your method
        expected_file_path = project_root / 'tmp' / self.mock_conversation.thread_id / 'voice.mp3'

        # Assert that mock_open was called with the expected path
        mock_open.assert_called_once_with(str(expected_file_path), 'wb')

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('requests.get')
    @patch('os.makedirs')
    @patch('lib.telegram.constraints_checker.ConstraintsChecker.check_document_constraints')
    def test_handle_document_message(self, mock_check_constraints, mock_makedirs, mock_requests_get, mock_open):
        mock_check_constraints.return_value = (True, "Success")
        document_extension = ".pdf"
        self.mock_update.message.document = Mock(file_id='document_file_id')
        self.mock_bot.get_file = AsyncMock(return_value=Mock(file_path=f"https://example.com/path/to/document{document_extension}", file_size=3072))

        # Mock the requests.get call
        mock_requests_get.return_value = Mock(status_code=200, content=b'fake document content')

        # Mock the open function
        mock_open.return_value = unittest.mock.mock_open().return_value

        loop = asyncio.get_event_loop()
        success, message, file_path = loop.run_until_complete(self.handler.handle_document_message())

        # Assertions
        self.assertTrue(success)
        self.assertEqual(message, "Document processed successfully")
        mock_check_constraints.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_requests_get.assert_called_once_with(f"https://example.com/path/to/document{document_extension}")
        self.mock_bot.get_file.assert_called_once_with('document_file_id')

        # Construct the expected file path
        project_root = Path(__file__).parent.parent.parent.parent
        expected_file_path = project_root / 'tmp' / self.mock_conversation.thread_id / f'document{document_extension}'

        # Assert that mock_open was called with the expected path
        mock_open.assert_called_once_with(str(expected_file_path), 'wb')

if __name__ == '__main__':
    unittest.main()
