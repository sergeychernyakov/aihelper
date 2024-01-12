import unittest
from unittest.mock import Mock, AsyncMock, patch
from lib.telegram.bots.base_bot import BaseBot
from telegram import Update, User, CallbackQuery
from telegram.ext import CallbackContext
from db.models.conversation import Conversation
from lib.openai.assistant import Assistant
from sqlalchemy.exc import SQLAlchemyError
import asyncio

class TestBaseBot(unittest.TestCase):

    def setUp(self):
        patcher = patch('os.getenv', side_effect=lambda x: {'TELEGRAM_BOT_TOKEN': 'mock_telegram_bot_token', 
                                                            'STRIPE_API_TOKEN': 'mock_stripe_token',
                                                            'ASSISTANT_ID': 'mock_assistant_id'}.get(x, 'mock_value'))
        self.mock_getenv = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('telegram.ext.Application.builder')
        self.mock_builder = patcher.start()
        self.mock_application = self.mock_builder.return_value
        self.mock_application.token.return_value = self.mock_application
        self.mock_application.build.return_value = Mock()
        self.addCleanup(patcher.stop)

        self.bot = BaseBot()

    @patch('lib.telegram.bots.base_bot.Assistant')
    @patch('lib.telegram.bots.base_bot.Payment')
    @patch('lib.telegram.bots.base_bot.Application')
    def test_init(self, mock_Application, mock_payment, mock_assistant):
        # Mock the Application builder
        mock_builder = Mock()
        mock_Application.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = Mock()

        # Initialize BaseBot
        base_bot = BaseBot()

        # Assert that the environment variable is fetched
        self.mock_getenv.assert_any_call('TELEGRAM_BOT_TOKEN')
        self.mock_getenv.assert_any_call('STRIPE_API_TOKEN')
        self.mock_getenv.assert_any_call('ASSISTANT_ID')

        # Assert that the Assistant and Payment objects are initialized
        mock_assistant.assert_called_once()
        mock_payment.assert_called_once()

        # Assert that the bot token, openai client, and assistant ID are set correctly
        self.assertEqual(base_bot.TELEGRAM_BOT_TOKEN, 'mock_telegram_bot_token')
        self.assertIsNotNone(base_bot.openai)  # Assuming get_openai_client() returns a client object
        self.assertIsNotNone(base_bot.assistant)  # Assuming Assistant() returns an assistant object

        # Assert that the Application builder is set up correctly
        mock_Application.builder.assert_called_once()
        mock_builder.token.assert_called_once_with('mock_telegram_bot_token')
        mock_builder.build.assert_called_once()

        # Assert handlers are added, but don't check for specific handlers
        self.assertTrue(mock_builder.build.return_value.add_handler.called)

    @patch('lib.telegram.bots.base_bot.Application')
    def test_setup_handlers(self, mock_Application):
        # Mock the Application builder and its methods
        mock_builder = Mock()
        mock_Application.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = Mock()

        # Initialize BaseBot
        base_bot = BaseBot()

        # Assert the builder pattern is used correctly
        mock_Application.builder.assert_called_once()
        mock_builder.token.assert_called_once_with(base_bot.TELEGRAM_BOT_TOKEN)
        mock_builder.build.assert_called_once()

    @patch('lib.telegram.bots.base_bot.SessionLocal')
    @patch('lib.telegram.bots.base_bot.Assistant')
    def test_create_conversation(self, mock_assistant, mock_session_local):
        # Mocking the openai client and the database session
        mock_openai_client = Mock()
        mock_thread = Mock(id='mock_thread_id')
        mock_openai_client.beta.threads.create.return_value = mock_thread
        mock_assistant.return_value.get_openai_client.return_value = mock_openai_client

        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Setting up the Update and User mock objects
        mock_user = Mock(spec=User)
        mock_user.id = 123
        mock_user.language_code = 'en'
        mock_user.username = 'TestUser'
        mock_user.is_bot = False

        mock_update = Mock(spec=Update)
        mock_update.message = Mock()
        mock_update.message.from_user = mock_user

        # Initializing BaseBot and calling _create_conversation
        base_bot = BaseBot()
        conversation = base_bot._create_conversation(mock_session, mock_update)

        # Assertions
        mock_openai_client.beta.threads.create.assert_called_once()
        self.assertIsInstance(conversation, Conversation)
        self.assertEqual(conversation.user_id, 123)
        self.assertEqual(conversation.language_code, 'en')
        self.assertEqual(conversation.username, 'TestUser')
        self.assertEqual(conversation.thread_id, 'mock_thread_id')
        self.assertEqual(conversation.assistant_id, Assistant.ASSISTANT_ID)

        # Verify the conversation is added to the session
        mock_session.add.assert_called_once_with(conversation)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(conversation)

    @patch('lib.telegram.bots.base_bot.SessionLocal')
    def test_session_scope(self, mock_session_local):
        # Create a mock session object
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Initialize BaseBot
        base_bot = BaseBot()

        # Use the session_scope in a with block
        with base_bot.session_scope() as session:
            self.assertEqual(session, mock_session)

        # Check if commit was called
        mock_session.commit.assert_called_once()

        # Check if the session was closed
        mock_session.close.assert_called_once()

    @patch('lib.telegram.bots.base_bot.SessionLocal')
    def test_session_scope_with_exception(self, mock_SessionLocal):
        # Create a mock session object
        mock_session = Mock()
        mock_SessionLocal.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Test Error")

        # Initialize BaseBot
        base_bot = BaseBot()

        # Directly test the context manager
        with base_bot.session_scope() as session:
            # No need to do anything, the side_effect will raise the error
            print('')

        # Assert rollback is called due to the exception
        mock_session.rollback.assert_called_once()

    @patch('lib.telegram.bots.base_bot.logging')
    def test_error_handler(self, mock_logging):
        # Initialize BaseBot
        base_bot = BaseBot()

        # Create mock objects for Update and CallbackContext
        mock_update = Mock(spec=Update)
        mock_context = Mock()
        mock_context.error = Exception("Test Error")

        # Call the error_handler method
        result = base_bot.error_handler(mock_update, mock_context)

        # Assert the logger called with the error
        mock_logging.getLogger.assert_called_once_with('lib.telegram.bots.base_bot')
        logger = mock_logging.getLogger.return_value
        logger.error.assert_called_once_with(msg="Exception while handling an update:", exc_info=mock_context.error)

        # Assert the return value of the error handler
        self.assertFalse(result)

    def test_ping(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_ping())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.telegram.bots.base_bot.CallbackContext')
    async def async_test_ping(self, mock_context):
        mock_update = Mock(spec=Update)
        mock_user = User(123, 'TestUser', False)
        mock_update.message = Mock(from_user=mock_user)

        # Use AsyncMock for the asynchronous method
        mock_context.bot.send_message = AsyncMock()

        await self.bot.ping(mock_update, mock_context)

        # Assert that send_message is called with correct arguments
        mock_context.bot.send_message.assert_awaited_with(123, 'pong')

    def test_finish(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_finish())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.telegram.bots.base_bot.CallbackContext')
    async def async_test_finish(self, mock_context):
        with patch('lib.telegram.bots.base_bot.BaseBot.session_scope') as mock_session_scope:
            mock_session = Mock()
            mock_session_scope.return_value.__enter__.return_value = mock_session

            mock_conversation = Mock(spec=Conversation)
            mock_conversation.id = 1
            mock_session.query().filter_by.return_value.first.return_value = mock_conversation

            # Mock OpenAI delete thread call
            with patch('openai.resources.beta.threads.Threads.delete') as mock_delete_thread:
                mock_delete_thread.return_value = None

                mock_update = Mock(spec=Update)
                mock_user = User(123, 'TestUser', False)
                mock_chat = Mock()
                mock_chat.id = 456
                mock_update.message = Mock(from_user=mock_user, chat=mock_chat)

                mock_context.bot.send_message = AsyncMock()

                await self.bot.finish(mock_update, mock_context)
                mock_context.bot.send_message.assert_awaited()

    def test_balance(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_balance())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.telegram.bots.base_bot.CallbackContext')
    async def async_test_balance(self, mock_context):
        mock_update = Mock(spec=Update)
        mock_user = User(123, 'TestUser', False)
        mock_chat = Mock()
        mock_chat.id = 456
        mock_update.message = Mock(from_user=mock_user, chat=mock_chat)

        mock_context.bot.send_message = AsyncMock()

        with patch('lib.telegram.bots.base_bot.BaseBot.session_scope') as mock_session_scope:
            mock_session = Mock()
            mock_session_scope.return_value.__enter__.return_value = mock_session
            mock_conversation = Mock(spec=Conversation)
            mock_conversation.balance = 10
            mock_session.query().filter_by().first.return_value = mock_conversation

            await self.bot.balance(mock_update, mock_context)

            # Assert that a message with the balance is sent to the user
            mock_context.bot.send_message.assert_called()

    def test_button(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_button())

        # Close the loop at the end of the test
        loop.close()

    async def async_test_button(self):
        base_bot = BaseBot()

        mock_update = Mock(spec=Update)
        mock_context = Mock(spec=CallbackContext)

        # Mocking the callback query and its methods
        mock_query = Mock(spec=CallbackQuery)
        mock_query.answer = AsyncMock()
        mock_query.data = 'balance'
        mock_update.callback_query = mock_query

        # Mocking the balance, send_invoice, and finish methods
        base_bot.balance = AsyncMock()
        base_bot.payment.send_invoice = AsyncMock()
        base_bot.finish = AsyncMock()

        # Test 'balance' callback data
        await base_bot.button(mock_update, mock_context)
        base_bot.balance.assert_awaited_once_with(mock_update, mock_context, from_button=True)

        # Reset mocks for next test
        mock_query.answer.reset_mock()
        base_bot.balance.reset_mock()

        # Test 'invoice' callback data
        mock_query.data = 'invoice'
        await base_bot.button(mock_update, mock_context)
        base_bot.payment.send_invoice.assert_awaited_once_with(mock_update, mock_context, from_button=True)

        # Reset mocks for next test
        mock_query.answer.reset_mock()
        base_bot.payment.send_invoice.reset_mock()

        # Test 'finish' callback data
        mock_query.data = 'finish'
        await base_bot.button(mock_update, mock_context)
        base_bot.finish.assert_awaited_once_with(mock_update, mock_context, from_button=True)

    def test_send_invoice(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_send_invoice())

        # Close the loop at the end of the test
        loop.close()

    async def async_test_send_invoice(self):
        base_bot = BaseBot()

        mock_update = Mock(spec=Update)
        mock_context = Mock(spec=CallbackContext)

        # Mocking the payment's send_invoice method
        base_bot.payment.send_invoice = AsyncMock()

        # Test the send_invoice call
        await base_bot.send_invoice(mock_update, mock_context)

        # Assert that payment's send_invoice method is called with the correct arguments
        base_bot.payment.send_invoice.assert_awaited_once_with(mock_update, mock_context, from_button=False)

    @patch('lib.telegram.bots.base_bot.Application')
    def test_run(self, mock_Application):
        # Mock the Application builder and its methods
        mock_builder = Mock()
        mock_Application.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = Mock()

        # Initialize BaseBot
        base_bot = BaseBot()

        # Mock the run_polling method
        mock_builder.build.return_value.run_polling = Mock()

        # Run the bot
        base_bot.run()

        # Assert that run_polling is called
        mock_builder.build.return_value.run_polling.assert_called_once()

if __name__ == '__main__':
    unittest.main()
