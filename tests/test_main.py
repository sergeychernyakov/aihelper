import unittest
from unittest.mock import Mock, patch
from main import message_handler, main, ping, TELEGRAM_BOT_TOKEN
from telegram import Update, User, Message
from db.models.conversation import Conversation
from datetime import datetime, timedelta
from decimal import Decimal

class TestMain(unittest.TestCase):

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

        # Mock Conversation object with a realistic updated_at and balance
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.updated_at = datetime.utcnow() - timedelta(hours=2)
        mock_conversation.balance = Decimal('5.0')  # Example balance
        mock_session.query().filter_by().first.return_value = mock_conversation

        # Set thread recreation interval
        mock_runs_treads_handler.return_value.thread_recreation_interval = timedelta(hours=1)

        # Mock the return value of openai.beta.threads.messages.list
        mock_openai_global.beta.threads.messages.list.return_value = [Mock(content=[Mock(type='text', text=Mock(value='Hello'))])]

        # Mock the tokenizer to return a Decimal amount
        with patch('main.Tokenizer.calculate_thread_total_amount', return_value=Decimal('1.0')):
            # Call the function
            message_handler(mock_update, mock_context)

        # Assertions for MessagesHandler
        mock_messages_handler.assert_called_once_with(
            mock_openai_global,
            mock_update,
            mock_context,
            mock_conversation
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

    @patch('main.CallbackContext')
    def test_ping(self, mock_context):
        # Mocking the Update and User objects
        mock_update = Mock()
        mock_user = Mock()
        mock_user.first_name = "TestFirstName"
        mock_user.username = "TestUsername"
        mock_user.id = 12345  # mock user ID
        mock_update.message = Mock(from_user=mock_user)

        # Call the ping function with the mock objects
        ping(mock_update, mock_context)

        # Assert that send_message is called with correct arguments
        mock_context.bot.send_message.assert_called_with(mock_user.id, 'pong')

if __name__ == '__main__':
    unittest.main()
