import io
import json
import shutil
import os
import unittest
import asyncio
from unittest.mock import Mock, patch, mock_open, AsyncMock, ANY
from lib.openai.thread_run_manager import ThreadRunManager
from decimal import Decimal

class TestThreadRunManager(unittest.TestCase):

    def setUp(self):
        # Mock dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_session = Mock()

        # Mock conversation object with required attributes
        self.mock_conversation = Mock()
        self.mock_conversation.thread_id = 'thread_id'
        self.mock_conversation.assistant_id = 'assistant_id'
        self.mock_conversation.balance = Decimal('10.0')  # Assign a Decimal value to balance
        self.mock_context.bot.send_photo = AsyncMock() 

        # Add a mock chat_id
        self.mock_chat_id = 12345  # or any valid chat ID

        # Update the ThreadRunManager instantiation
        self.handler = ThreadRunManager(
            self.mock_openai_client, 
            self.mock_update, 
            self.mock_context, 
            self.mock_conversation, 
            self.mock_session,
            self.mock_chat_id
        )

    def test_manage_run(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_manage_run())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.openai.thread_run_manager.ThreadRunManager.create_run')
    @patch('lib.openai.thread_run_manager.ThreadRunManager.process_run')
    async def async_test_manage_run(self, mock_process_run, mock_create_run):
        # Set return values for the mocks
        mock_create_run.return_value = 'run_id'
        mock_process_run.return_value = asyncio.Future()
        mock_process_run.return_value.set_result(None)  # Simulate a completed async call

        # Call the method under test
        await self.handler.manage_run()

        # Assertions
        mock_create_run.assert_called_once()
        mock_process_run.assert_called_once_with('run_id')

    def test_process_run(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_process_run())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.openai.thread_run_manager.ThreadRunManager.wait_for_run_completion')
    @patch('lib.openai.thread_run_manager.ThreadRunManager.handle_run_response')
    async def async_test_process_run(self, mock_handle_run_response, mock_wait_for_run_completion):
        # Mock the run object
        mock_run = Mock()

        # Set the return value of wait_for_run_completion to mock_run directly
        mock_wait_for_run_completion.return_value = mock_run

        # Invoke the method under test
        await self.handler.process_run('run_id')

        # Assertions
        mock_wait_for_run_completion.assert_called_once_with('run_id', ANY)
        mock_handle_run_response.assert_called_once_with(mock_run)

    def test_create_run(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_create_run())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.telegram.answer.Answer')
    @patch('lib.telegram.helpers.Helpers.cleanup_folder')
    @patch('builtins.open', new_callable=mock_open, create=True)
    @patch('random.randint', return_value=1)
    async def async_test_create_run(self, mock_randint, mock_file_open, mock_cleanup_folder, mock_answer):
        # Mock setup for runs.create
        mock_run = Mock(status='in-progress', id='run_id')
        self.mock_openai_client.beta.threads.runs.create.return_value = mock_run

        # Execute the method under test
        run_id = await self.handler.create_run()

        # Assertions
        self.mock_openai_client.beta.threads.runs.create.assert_called_once_with(thread_id=self.mock_conversation.thread_id, assistant_id=self.mock_conversation.assistant_id)
        self.assertEqual(run_id, 'run_id')

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

    def test_cancel_run_exception_handling(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.mock_openai_client.beta.threads.runs.cancel.side_effect = Exception("Test Exception")
            self.handler.cancel_run('valid_thread_id', 'valid_run_id')
            self.assertIn("Error occurred while cancelling the run: Test Exception", fake_output.getvalue())

    def test_cancel_run_with_none_or_invalid_ids(self):
        # This method is now an async method
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.handler.cancel_run(None, None)
            self.assertIn("Failed to cancel run with invalid IDs.", fake_output.getvalue())

    def test_submit_tool_outputs(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_submit_tool_outputs())

        # Close the loop at the end of the test
        loop.close()
    
    @patch('lib.openai.thread_run_manager.ThreadRunManager._handle_tool_call')
    async def async_test_submit_tool_outputs(self, mock_handle_tool_call):
        mock_handle_tool_call.return_value = {'tool_call_id': 'tool_call_id', 'output': 'test_output'}

        # Create a mock run object with necessary attributes
        mock_run = Mock()
        mock_run.required_action.submit_tool_outputs.tool_calls = [Mock(id='tool_call_id')]

        # Call the method under test
        await self.handler.submit_tool_outputs(mock_run)

        # Assertions
        mock_handle_tool_call.assert_awaited()
        self.mock_openai_client.beta.threads.runs.submit_tool_outputs.assert_called_once_with(
            thread_id='thread_id',
            run_id=mock_run.id,
            tool_outputs=[{'tool_call_id': 'tool_call_id', 'output': 'test_output'}]
        )

    def tearDown(self):
        temp_dir_path = './tmp/thread_id'  # Ensure this is the correct path
        if os.path.exists(temp_dir_path):
            try:
                shutil.rmtree(temp_dir_path)
            except Exception as e:
                print(f"Error deleting temporary directory {temp_dir_path}: {e}")

if __name__ == '__main__':
    unittest.main()
