import unittest
from unittest.mock import Mock, patch, mock_open  # Import mock_open here
from lib.telegram.runs_treads_handler import RunsTreadsHandler

class TestRunsTreadsHandler(unittest.TestCase):

    def setUp(self):
        # Mock dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_session = Mock()
        self.mock_conversation = Mock()

        # Setup for RunsTreadsHandler instance
        self.handler = RunsTreadsHandler(self.mock_openai_client, self.mock_update, self.mock_context, 'thread_id', 'assistant_id')

    @patch('lib.telegram.answer.Answer')
    @patch('lib.telegram.helpers.Helpers.cleanup_folder')
    @patch('builtins.open', new_callable=mock_open, create=True)
    @patch('random.randint', return_value=1)  # Mock random.randint
    def test_create_run(self, mock_randint, mock_file_open, mock_cleanup_folder, mock_answer):
        # Mock setup...
        mock_run_in_progress = Mock(status='in-progress', id='run_id')
        mock_run_completed = Mock(status='completed', id='run_id')
        self.mock_openai_client.beta.threads.runs.create.return_value = mock_run_in_progress
        self.mock_openai_client.beta.threads.runs.retrieve.side_effect = [mock_run_in_progress, mock_run_completed]
        # Ensure the response text length is within the short message threshold
        short_response_text = "Short response"
        mock_messages = Mock(data=[Mock(content=[Mock(text=Mock(value=short_response_text))])])
        self.mock_openai_client.beta.threads.messages.list.return_value = mock_messages

        self.handler.create_run()

        # Assertions...
        self.mock_openai_client.beta.threads.runs.create.assert_called_once()
        self.assertTrue(self.mock_openai_client.beta.threads.runs.retrieve.call_count > 0)
        self.mock_openai_client.beta.threads.messages.list.assert_called_once()
        mock_cleanup_folder.assert_called_once()
        mock_file_open.assert_called()  # Check if open was called during the test


    def test_create_thread(self):
        self.mock_conversation.id = 'conversation_id'
        mock_thread = Mock(id='new_thread_id')
        self.mock_openai_client.beta.threads.create.return_value = mock_thread

        self.handler.create_thread(self.mock_session, self.mock_conversation)

        # Assertions
        self.mock_session.query().filter_by().update.assert_called_once_with({"thread_id": "new_thread_id"})
        self.mock_session.commit.assert_called_once()

    def test_recreate_thread(self):
        self.mock_conversation.thread_id = 'existing_thread_id'

        self.handler.recreate_thread(self.mock_session, self.mock_conversation)

        # Assertions
        self.mock_openai_client.beta.threads.delete.assert_called_once_with('existing_thread_id')
        self.mock_session.query().filter_by().update.assert_called_once()
        self.mock_session.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
