import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from lib.openai.function_handlers.send_email_handler import SendEmailHandler
from lib.email_sender import EmailSender

class TestSendEmailHandler(unittest.TestCase):

    def setUp(self):
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_conversation = Mock()

        self.handler = SendEmailHandler(self.mock_openai_client, self.mock_update, self.mock_context, self.mock_conversation)

    def test_handle_send_email(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_handle_send_email())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.email_sender._', return_value='Letter successfully sent.')
    async def async_test_handle_send_email(self, mock_send_email):
        tool_call_id = "tool_call_id"
        args = {"email": "test@example.com", "text": "Hello World", "attachment": "path/to/file"}

        # Execute the handler
        result = await self.handler.handle(tool_call_id, args)

        # Assertions
        mock_send_email.assert_called_once_with(args['email'], args['text'], args['attachment'])
        self.mock_context.bot.send_message.assert_awaited_with(self.mock_update.message.chat_id, _('Letter successfully sent.'))
        self.assertEqual(result, {
            "tool_call_id": tool_call_id,
            "output": _('Letter successfully sent. There is no need to reply to the message.')
        })

if __name__ == '__main__':
    unittest.main()
