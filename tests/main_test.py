import unittest
import main
from unittest import mock
from main import message_handler
from unittest.mock import Mock, patch, MagicMock, mock_open

def create_mock_update(text="Test message", user_id=12345, first_name="Test", username="testuser"):
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = text
    mock_update.message.from_user = Mock()
    mock_update.message.from_user.id = user_id
    mock_update.message.from_user.first_name = first_name
    mock_update.message.from_user.username = username

    return mock_update

def create_mock_update_with_caption(caption):
    mock_update = Mock()
    mock_update.message.caption = caption
    return mock_update

class TestTelegramBotFunctions(unittest.TestCase):

    @patch('main.RunsTreadsHandler.create_run')
    @patch('main.session_scope')
    def test_message_handler(self, mock_session_scope, mock_create_run):
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
        mock_create_run.assert_called_once()
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
