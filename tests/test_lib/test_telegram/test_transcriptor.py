import unittest
from unittest.mock import Mock, AsyncMock, patch, mock_open, ANY
from lib.telegram.transcriptor import Transcriptor
from asyncio import run

class TestTranscriptor(unittest.TestCase):

    def setUp(self):
        self.mock_openai_client = Mock()
        self.transcriptor = Transcriptor(self.mock_openai_client)

    def test_transcript_photo(self):
        file = Mock()
        file.file_path = "path/to/image"
        caption = "Caption for the image"
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Mocked Content"))]
        mock_response.usage = Mock(total_tokens=123)
        self.mock_openai_client.chat.completions.create.return_value = mock_response

        success = run(self.transcriptor.transcript_photo(file.file_path, caption))
        self.assertTrue(success)

    @patch('builtins.open', new_callable=mock_open)
    def test_transcript_voice(self, mock_file):
        mock_transcription = Mock(return_value="Mocked Transcription")
        self.mock_openai_client.audio.transcriptions.create = mock_transcription

        # Execute the transcript_voice method
        run(self.transcriptor.transcript_voice("path/to/audio"))

        # Verify that the OpenAI transcription method was called
        mock_transcription.assert_called_once_with(
            model="whisper-1",
            file=ANY,  # Use ANY from unittest.mock if the exact file object isn't important
            response_format="text",
            temperature='1.0'
        )

if __name__ == '__main__':
    unittest.main()
