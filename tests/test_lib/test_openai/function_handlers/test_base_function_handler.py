import unittest
from unittest.mock import Mock
from lib.openai.tokenizer import Tokenizer
from lib.openai.function_handlers.base_function_handler import BaseFunctionHandler

class TestBaseFunctionHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Mocking dependencies
        self.mock_openai_client = Mock()
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_conversation = Mock()
        self.mock_tokenizer = Mock(spec=Tokenizer)

        # Instantiate the BaseFunctionHandler
        self.handler = BaseFunctionHandler(
            self.mock_openai_client,
            self.mock_update,
            self.mock_context,
            self.mock_conversation
        )

    async def test_initialization(self):
        self.assertEqual(self.handler.openai, self.mock_openai_client)
        self.assertEqual(self.handler.update, self.mock_update)
        self.assertEqual(self.handler.context, self.mock_context)
        self.assertEqual(self.handler.conversation, self.mock_conversation)
        self.assertIsInstance(self.handler.tokenizer, Tokenizer)

    async def test_handle_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await self.handler.handle('tool_call_id', {})

if __name__ == '__main__':
    unittest.main()
