import unittest
from unittest.mock import patch, MagicMock
from translator_bot import main

class TestTranslatorBot(unittest.TestCase):

    @patch('translator_bot.TranslatorBot')
    def test_main_initialization(self, mock_translator_bot_class):
        # Mock the TranslatorBot instance
        mock_bot_instance = MagicMock()
        mock_translator_bot_class.return_value = mock_bot_instance

        # Call the main function
        main()

        # Assert that the TranslatorBot was instantiated
        mock_translator_bot_class.assert_called_once()

        # Assert that the run method was called on the bot instance
        mock_bot_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
