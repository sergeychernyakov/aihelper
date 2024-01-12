import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from lib.openai.function_handlers.generate_image_handler import GenerateImageHandler
from decimal import Decimal
from db.models.conversation import Conversation

class TestGenerateImageHandler(unittest.TestCase):
    
    def setUp(self):
        # Mock dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.bot.send_photo = AsyncMock()

        # Mock conversation object with balance attribute
        self.mock_conversation = Mock(spec=Conversation)
        self.mock_conversation.balance = Decimal('10.0')

        # Initialize the handler
        self.handler = GenerateImageHandler(self.mock_openai_client, self.mock_update, self.mock_context, self.mock_conversation)

    def test_handle_with_insufficient_balance(self):
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the asynchronous test using the new event loop
        loop.run_until_complete(self.async_test_handle_with_insufficient_balance())

        # Close the loop at the end of the test
        loop.close()

    @patch('lib.openai.tokenizer.Tokenizer')
    async def async_test_handle_with_insufficient_balance(self, mock_tokenizer):
        # Mock the tokenizer methods
        mock_tokenizer_instance = mock_tokenizer.return_value
        mock_tokenizer_instance.tokens_to_money_from_string.return_value = 5.0
        mock_tokenizer_instance.tokens_to_money_to_image.return_value = 6.0
        mock_tokenizer_instance.has_sufficient_balance_for_amount.return_value = False

        # Define tool call ID and arguments
        tool_call_id = "tool_call_id"
        args = {"description": "test image description"}

        # Execute the handler
        result = await self.handler.handle(tool_call_id, args)

        # Assertions
        self.mock_context.bot.send_message.assert_awaited()
        self.mock_context.bot.send_photo.assert_not_awaited()
        self.assertEqual(result, {
            "tool_call_id": tool_call_id,
            "output": "Insufficient balance to process the generating image."
        })

if __name__ == '__main__':
    unittest.main()
