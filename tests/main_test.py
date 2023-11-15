import unittest
import main
from unittest import mock
from main import check_file_constraints, handle_text_message, create_conversation, handle_photo_message, transcript_image, create_run, text_handler
from unittest.mock import Mock, patch, MagicMock

def create_mock_file_and_photo(file_extension=".jpg", file_size=1024, width=1000, height=1000):
    mock_file = Mock()
    mock_file.file_path = f"test{file_extension}"
    mock_file.file_size = file_size

    mock_photo = Mock()
    mock_photo.width = width
    mock_photo.height = height

    return mock_file, mock_photo

def create_mock_update(text="Test message", user_id=12345, first_name="Test", username="testuser"):
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = text
    mock_update.message.from_user = Mock()
    mock_update.message.from_user.id = user_id
    mock_update.message.from_user.first_name = first_name
    mock_update.message.from_user.username = username

    return mock_update

class TestTelegramBotFunctions(unittest.TestCase):

    def test_check_file_constraints(self):
        # Assuming you have a way to create a mock 'file' and 'photo' object
        mock_file, mock_photo = create_mock_file_and_photo()  # You need to define this helper function

        # Test for a valid file
        success, message = check_file_constraints(mock_file, mock_photo)
        self.assertTrue(success)
        self.assertEqual(message, "")

        # Test for an invalid file type
        mock_file_invalid, _ = create_mock_file_and_photo(file_extension=".txt")
        success, message = check_file_constraints(mock_file_invalid, mock_photo)
        self.assertFalse(success)
        self.assertEqual(message, "Unsupported file type.")

    @mock.patch('main.openai')
    def test_handle_text_message(self, mock_openai):
        mock_update = create_mock_update()
        mock_thread_id = "12345"
        result = handle_text_message(mock_update, mock_thread_id)

        # Assert if OpenAI API was called correctly
        mock_openai.beta.threads.messages.create.assert_called_with(
            thread_id=mock_thread_id,
            role="user",
            content=mock_update.message.text
        )

        # Assert if the function executed successfully
        self.assertTrue(result)

    @mock.patch('main.check_file_constraints')
    def test_handle_photo_message(self, mock_check_file_constraints):
        # Mock the check_file_constraints function to return True
        mock_check_file_constraints.return_value = (True, "")

        # Create mock update and context
        mock_update = create_mock_update()
        mock_context = Mock()
        mock_file = Mock(file_path="path/to/photo.jpg", file_size=1024)
        mock_context.bot.get_file.return_value = mock_file

        # Add a placeholder mock photo object and then the actual mock_photo
        placeholder_mock_photo = Mock()
        mock_photo = Mock()
        mock_photo.file_id = "photo_file_id"
        mock_photo.width = 512
        mock_photo.height = 512
        another_placeholder_mock_photo = Mock()  # This will be the last item in the list
        mock_update.message.photo = [mock_photo, another_placeholder_mock_photo]  # mock_photo is now second-to-last

        # Call the function
        success, message, file = handle_photo_message(mock_update, mock_context)

        # Assert if the function succeeded
        self.assertTrue(success)
        self.assertEqual(message, "Image processed successfully")
        self.assertIsNotNone(file)

        # Mock and assert check_file_constraints call
        mock_check_file_constraints.assert_called_once_with(mock_file, mock_photo)

    @mock.patch('main.SessionLocal')
    def test_create_conversation(self, mock_session):
        # Create a mock update
        mock_update = create_mock_update()  # You need to define this helper function

        # Call the function
        conversation = create_conversation(mock_session, mock_update)

        # Assert if conversation has correct attributes
        self.assertEqual(conversation.user_id, mock_update.message.from_user.id)
        self.assertEqual(conversation.language_code, mock_update.message.from_user.language_code)
        # ... other assertions ...

    @mock.patch('main.openai.chat.completions.create')
    @mock.patch('main.openai.beta.threads.messages.create')
    def test_transcript_image(self, mock_threads_messages_create, mock_chat_completions_create):
        # Create mocks for update and context
        mock_update = create_mock_update()
        mock_context = Mock()
        mock_file = Mock(file_path="path/to/photo.jpg")
        mock_thread_id = "12345"

        # Set return values for OpenAI API calls
        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock(message=Mock(content="Transcription result"))]
        mock_chat_completions_create.return_value = mock_chat_response

        # Call the transcript_image function
        transcript_image(mock_update, mock_context, mock_thread_id, mock_file)

        # Assert if OpenAI API was called correctly for chat completions
        mock_chat_completions_create.assert_called_with(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": mock_update.message.caption or "Default caption"},
                        {"type": "image_url", "image_url": {"url": mock_file.file_path, "detail": "low"}}
                    ],
                }
            ],
            max_tokens=100
        )

        # Assert if OpenAI API was called correctly for thread messages
        # This depends on how you expect the function to interact with the OpenAI API
        # ...

        # Assert if the bot sent a message with the expected content
        mock_context.bot.send_message.assert_called_with(
            mock_update.message.chat_id,
            "Transcription result"
        )

    @patch('main.openai.beta.threads.runs.create')
    @patch('main.openai.beta.threads.runs.retrieve')
    @patch('main.openai.beta.threads.messages.list')
    def test_create_run(self, mock_threads_messages_list, mock_threads_runs_retrieve, mock_threads_runs_create):
        # Create mocks for update, context, and the run object
        mock_update = create_mock_update()
        mock_context = Mock()
        mock_thread_id = "12345"
        mock_assistant_id = "assistant_id"
        
        # Mock the run object and its properties
        mock_run = Mock()
        mock_run.status = "completed"
        mock_threads_runs_create.return_value = mock_run

        # Mock the response for runs.retrieve
        mock_threads_runs_retrieve.return_value = mock_run

        # Mock the response for threads.messages.list
        mock_message_response = Mock()
        mock_message_response.data = [Mock(content=[Mock(text=Mock(value="AI response"))])]
        mock_threads_messages_list.return_value = mock_message_response

        # Call the create_run function
        create_run(mock_thread_id, mock_assistant_id, mock_update, mock_context)

        # Assert if openai.beta.threads.runs.create was called correctly
        mock_threads_runs_create.assert_called_with(thread_id=mock_thread_id, assistant_id=mock_assistant_id)

        # Assert if openai.beta.threads.runs.retrieve was called correctly
        # This depends on your implementation details and how often you expect the function to poll the run status
        # ...

        # Assert if openai.beta.threads.messages.list was called correctly
        mock_threads_messages_list.assert_called_with(thread_id=mock_thread_id)

        # Assert if the bot sent a message with the expected content
        mock_context.bot.send_message.assert_called_with(
            mock_update.message.chat_id,
            "AI response"
        )

    @patch('main.create_run')
    @patch('main.transcript_image')
    @patch('main.handle_photo_message')
    @patch('main.handle_text_message')
    @patch('main.create_conversation')
    @patch('main.session_scope')
    def test_text_handler(self, mock_session_scope, mock_create_conversation, 
                          mock_handle_text_message, mock_handle_photo_message, 
                          mock_transcript_image, mock_create_run):
        # Mock setup
        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_update = create_mock_update()
        mock_context = Mock()
        mock_conversation = Mock()
        mock_conversation.thread_id = 'some_thread_id'
        mock_create_conversation.return_value = mock_conversation

        # Ensure conversation is retrieved
        mock_session.query().filter_by().first.return_value = mock_conversation

        mock_handle_text_message.return_value = True
        text_handler(mock_update, mock_context)

        # Assert the create_run call
        mock_create_run.assert_called_once_with('some_thread_id', mock_conversation.assistant_id, mock_update, mock_context)

    @patch('main.Updater')
    @patch('main.MessageHandler')
    @patch('main.Filters')
    def test_main(self, mock_Filters, mock_MessageHandler, mock_Updater):
        # Mock the bot and dispatcher
        mock_bot = Mock()
        mock_dispatcher = Mock()
        mock_Updater.return_value = Mock(bot=mock_bot, dispatcher=mock_dispatcher, start_polling=Mock(), idle=Mock())

        # Run the main method
        main.main()

        # Assert Updater is called with the correct token
        mock_Updater.assert_called_with(main.TELEGRAM_BOT_TOKEN, use_context=True)

        # Assert that a MessageHandler is created
        mock_MessageHandler.assert_called()

        # Assert the handler is added to the dispatcher
        mock_dispatcher.add_handler.assert_called()

        # Assert that start_polling and idle methods are called
        mock_Updater.return_value.start_polling.assert_called_once()
        mock_Updater.return_value.idle.assert_called_once() 

if __name__ == '__main__':
    unittest.main()
