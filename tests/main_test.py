import unittest
from unittest.mock import Mock, patch
from main import message_handler, main, TELEGRAM_BOT_TOKEN, ASSISTANT_ID
from telegram import Update, User, Message
from db.models.conversation import Conversation

class TestTelegramBot(unittest.TestCase):

    @patch('main.openai', new_callable=Mock)
    @patch('main.MessagesHandler')
    @patch('main.Transcriptor')
    @patch('main.RunsTreadsHandler')
    @patch('main.session_scope')
    def test_message_handler_text(self, mock_session_scope, mock_runs_treads_handler, 
                                mock_transcriptor, mock_messages_handler, mock_openai_global):

        # Mock dependencies
        mock_update = Mock(spec=Update)
        mock_context = Mock()
        mock_session = Mock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_user = User(123, 'TestUser', False)
        mock_message = Message(1, mock_user, None, Mock())
        mock_message.text = 'Hello'
        mock_update.message = mock_message

        # Call the function
        message_handler(mock_update, mock_context)

        # Assertions for MessagesHandler
        mock_messages_handler.assert_called_once_with(
            mock_openai_global,
            mock_update, 
            mock_context, 
            mock_session.query().filter_by().first().thread_id
        )

        # Assert the correct database query
        mock_session.query.assert_called()
        self.assertGreaterEqual(mock_session.query().filter_by().first.call_count, 1)

    @patch('main.Updater')
    @patch('main.MessageHandler')
    @patch('main.Filters')
    def test_main(self, mock_Filters, mock_MessageHandler, mock_Updater):
        # Mock the bot and dispatcher
        mock_bot = Mock()
        mock_dispatcher = Mock()
        mock_Updater.return_value = Mock(bot=mock_bot, dispatcher=mock_dispatcher, start_polling=Mock(), idle=Mock())

        # Run the main method
        main()

        # Assert Updater is called with the correct token
        mock_Updater.assert_called_with(TELEGRAM_BOT_TOKEN, use_context=True)

        # Assert that a MessageHandler is created
        mock_MessageHandler.assert_called()

        # Assert the handler is added to the dispatcher
        mock_dispatcher.add_handler.assert_called()

        # Assert that start_polling and idle methods are called
        mock_Updater.return_value.start_polling.assert_called_once()
        mock_Updater.return_value.idle.assert_called_once() 

if __name__ == '__main__':
    unittest.main()
