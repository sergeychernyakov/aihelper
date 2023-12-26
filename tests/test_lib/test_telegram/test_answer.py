import unittest
from unittest.mock import Mock, AsyncMock, patch, mock_open
import tempfile
import shutil  # Import shutil module
import os
from lib.telegram.answer import Answer
import asyncio

class TestAnswer(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock the dependencies
        self.mock_openai_client = Mock()
        self.mock_context = Mock()
        self.mock_bot = Mock()
        self.mock_context.bot = self.mock_bot
        self.answer = Answer(self.mock_openai_client, self.mock_context, 'chat_id', 'thread_id')
        self.temp_dir = None
        self.mock_bot.send_message = AsyncMock()

    async def test_answer_with_text(self):
        message = "Hello, world!"
        await self.answer.answer_with_text(message)
        self.mock_bot.send_message.assert_awaited_once_with('chat_id', message)

    async def test_answer_with_voice(self):
        message = "Hello, world!"

        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.read.return_value = b'Some audio bytes'  # Corrected to return bytes directly
        self.mock_openai_client.audio.speech.create.return_value = mock_response

        # Ensure send_voice is an AsyncMock
        self.mock_bot.send_voice = AsyncMock()

        # Call the answer_with_voice method
        await self.answer.answer_with_voice(message)

        # Verify that the OpenAI API was called correctly
        self.mock_openai_client.audio.speech.create.assert_called_once_with(
            model="tts-1", voice="nova", input=message
        )

        # Verify that the Telegram bot's send_voice method was called
        self.mock_bot.send_voice.assert_awaited_once()

    def tearDown(self):
        # Cleanup code to delete the test folder
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Failed to delete temporary directory: {e}")


if __name__ == '__main__':
    unittest.main()
