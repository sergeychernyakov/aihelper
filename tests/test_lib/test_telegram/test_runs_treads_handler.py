import unittest
import io
import json
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

    def test_cancel_run_with_valid_ids(self):
        # Test cancel_run with valid thread_id and run_id
        self.handler.cancel_run('valid_thread_id', 'valid_run_id')
        # Verify if the openai client's cancel method was called correctly
        self.mock_openai_client.beta.threads.runs.cancel.assert_called_once_with(
            thread_id='valid_thread_id',
            run_id='valid_run_id'
        )

    def test_cancel_run_with_invalid_ids(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.handler.cancel_run(None, None)
            self.assertIn("Cannot cancel run: Missing thread_id or run_id.", fake_output.getvalue())

    def test_cancel_run_exception_handling(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.mock_openai_client.beta.threads.runs.cancel.side_effect = Exception("Test Exception")
            self.handler.cancel_run('valid_thread_id', 'valid_run_id')
            self.assertIn("Error occurred while cancelling the run: Test Exception", fake_output.getvalue())


    @patch('lib.telegram.runs_treads_handler.Image')
    def test_submit_tool_outputs_with_generateImage(self, mock_image_class):
        mock_image_instance = mock_image_class.return_value
        mock_image_instance.generate.return_value = ('image_url', 'revised_prompt')

        # Mocking a run object with tool calls
        mock_tool_call = Mock(
            id='tool_call_id',
            type='function',
            function=Mock(
                name='generateImage',
                arguments=json.dumps({'description': 'test description'})
            )
        )
        mock_tool_call.function.name = 'generateImage'
        mock_run = Mock(
            id='run_id',
            required_action=Mock(
                submit_tool_outputs=Mock(
                    tool_calls=[mock_tool_call]
                )
            )
        )

        # Executing the method
        self.handler.submit_tool_outputs(mock_run)

        # Assertions
        mock_image_instance.generate.assert_called_once_with('test description')
        self.mock_openai_client.beta.threads.runs.submit_tool_outputs.assert_called_once_with(
            thread_id='thread_id',
            run_id='run_id',
            tool_outputs=[{
                "tool_call_id": 'tool_call_id',
                "output": 'image_url - эта картинка уже отправлена пользователю в чат в телеграме. Отвечать на сообщение не нужно.'
            }]
        )


if __name__ == '__main__':
    unittest.main()
