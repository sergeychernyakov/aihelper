import unittest
from unittest.mock import Mock, AsyncMock, patch
from lib.telegram.bots.translator_bot import TranslatorBot
from telegram import Update, User, Message, CallbackQuery
from datetime import datetime, timedelta
from decimal import Decimal

class TestTranslatorBot(unittest.TestCase):

    @patch('lib.telegram.bots.translator_bot.RunsTreadsHandler')
    @patch('lib.telegram.bots.translator_bot.MessagesHandler')
    @patch('lib.telegram.bots.translator_bot.Transcriptor')
    async def test_message_handler(self, mock_transcriptor, mock_messages_handler, mock_runs_treads_handler):
        # Setup mocks
        bot = TranslatorBot()
        mock_update = Mock(spec=Update)
        mock_context = Mock()
        mock_user = User(123, 'TestUser', False)
        mock_chat = Mock()
        mock_chat.id = 456
        mock_message = Message(1, mock_user, datetime.now(), mock_chat, text='Hello')
        mock_update.message = mock_message

        # Call the message_handler method
        await bot.message_handler(mock_update, mock_context)

        # Assert that the necessary handlers are called
        mock_runs_treads_handler.assert_called_once()
        mock_messages_handler.assert_called_once()
        mock_transcriptor.assert_called_once()

    async def test_start(self):
        bot = TranslatorBot()
        mock_update = Mock(spec=Update)
        mock_context = Mock()
        mock_user = User(123, 'TestUser', False)
        mock_chat = Mock()
        mock_chat.id = 456
        mock_message = Message(1, mock_user, datetime.now(), mock_chat)
        mock_update.message = mock_message

        # Call the start method
        await bot.start(mock_update, mock_context)

if __name__ == '__main__':
    unittest.main()
