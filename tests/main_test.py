import unittest
import main
from unittest import mock
from main import check_file_constraints, check_voice_constraints, create_conversation, transcript_image, transcript_voice
from main import message_handler, handle_text_message, handle_photo_message, create_run
from unittest.mock import Mock, patch, MagicMock, mock_open

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

def create_mock_voice(file_extension=".mp3", file_size=1024):
    mock_voice = Mock()
    mock_voice.file_path = f"test{file_extension}"
    mock_voice.file_size = file_size

    return mock_voice

def create_mock_update_with_caption(caption):
    mock_update = Mock()
    mock_update.message.caption = caption
    return mock_update

class TestTelegramBotFunctions(unittest.TestCase):

    @mock.patch('main.openai')
    def test_handle_text_message(self, mock_openai):
        # Create a mock update with a string text message
        mock_update = create_mock_update(text="Test message")
        mock_thread_id = "12345"
        result = handle_text_message(mock_update.message.text, mock_thread_id)

        # Assert if OpenAI API was called correctly
        mock_openai.beta.threads.messages.create.assert_called_with(
            thread_id=mock_thread_id,
            role="user",
            content="Test message"  # Ensuring this is a string as expected
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

    @patch('main.openai.chat.completions.create')
    @patch('main.openai.beta.threads.messages.create')
    def test_transcript_image(self, mock_threads_messages_create, mock_chat_completions_create):
        mock_update = create_mock_update_with_caption("Test caption")
        mock_context = Mock()
        mock_file = Mock(file_path="path/to/valid_photo.jpg")
        mock_thread_id = "12345"

        # Mocking the OpenAI API response
        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock(message=Mock(content="Transcription result"))]
        mock_chat_completions_create.return_value = mock_chat_response

        # Call the function
        transcript_image(mock_update, mock_context, mock_thread_id, mock_file)

        # Updated Assertions
        expected_messages = [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'Test caption'},
                    {'type': 'image_url', 'image_url': {'url': 'path/to/valid_photo.jpg', 'detail': 'low'}}
                ]
            }
        ]
        mock_chat_completions_create.assert_called_with(
            model='gpt-4-vision-preview',
            messages=expected_messages,
            max_tokens=100
        )

        mock_threads_messages_create.assert_called_with(
            thread_id=mock_thread_id, 
            role='user', 
            content='Переведи текст на украинский язык: "Transcription result"'
        )


        actual_call = mock_chat_completions_create.call_args[1]
        self.assertEqual(actual_call['messages'][0]['content'][1]['image_url']['url'], 'path/to/valid_photo.jpg')

        self.assertEqual(actual_call['messages'][0]['content'][0]['text'], 'Test caption')

        mock_context.bot.send_message.assert_called_with(
            mock_update.message.chat_id,
            "Transcription result"
        )

    @patch('main.openai.audio.transcriptions.create')
    @patch('main.openai.beta.threads.messages.create')
    @patch('builtins.open', new_callable=mock_open, read_data="data")
    def test_transcript_voice(self, mock_file_open, mock_threads_messages_create, mock_transcriptions_create):
        # Create mocks for update, context, and the file path
        mock_update = Mock()
        mock_context = Mock()
        mock_thread_id = "12345"
        file_path = "path/to/voice.mp3"

        # Set a mock response for the OpenAI transcription
        mock_transcription_response = "Transcribed text"
        mock_transcriptions_create.return_value = mock_transcription_response

        # Call the transcript_voice function
        transcript_voice(mock_update, mock_context, mock_thread_id, file_path)

        # Assert if the file was opened correctly
        mock_file_open.assert_called_with(file_path, "rb")

        # Assert if OpenAI transcription was called correctly
        mock_transcriptions_create.assert_called_with(
            model="whisper-1",
            file=mock.ANY,
            response_format="text"
        )

        # Assert if the thread message creation was correctly mocked
        mock_threads_messages_create.assert_called()

        # Assert if the bot sends a message with the transcription
        mock_context.bot.send_message.assert_called_with(
            mock_update.message.chat_id,
            mock_transcription_response
        )

    @patch('main.random.randint')
    @patch('main.answer_with_voice')
    @patch('main.answer_with_text')
    @patch('main.openai.beta.threads.messages.list')
    @patch('main.openai.beta.threads.runs.create')
    def test_create_run(self, mock_runs_create, mock_message_list, mock_answer_with_text, mock_answer_with_voice, mock_randint):
        # Mock setup for openai.beta.threads.runs.create
        mock_runs_create.return_value = MagicMock(status="completed")

        # Correctly mock the structure of the messages list response
        mock_message_list.return_value = MagicMock()
        mock_message_list.return_value.data = [MagicMock(content=[MagicMock(text=MagicMock(value="Short response"))])]

        # Setup for the test (mock_update and mock_context)
        mock_thread_id = "12345"
        mock_assistant_id = "assistant_id"
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test for text response
        mock_randint.return_value = 2  # Ensure it picks text response
        main.create_run(mock_thread_id, mock_assistant_id, mock_update, mock_context)

        mock_answer_with_text.assert_called_once_with(mock_context, "Short response", mock_update.message.chat_id)
        mock_answer_with_voice.assert_not_called()

        # Reset mocks for voice response test
        mock_answer_with_text.reset_mock()
        mock_answer_with_voice.reset_mock()

        # Test for voice response
        mock_randint.return_value = 1  # Force it to pick voice response
        main.create_run(mock_thread_id, mock_assistant_id, mock_update, mock_context)

        mock_answer_with_voice.assert_called_once_with(mock_context, "Short response", mock_update.message.chat_id, mock_thread_id)
        mock_answer_with_text.assert_not_called()

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
        message_handler(mock_update, mock_context)

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
