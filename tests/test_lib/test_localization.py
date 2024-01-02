import unittest
from unittest.mock import patch, MagicMock, ANY
from lib.localization import Localization

class TestLocalization(unittest.TestCase):

    def setUp(self):
        # Reset the state of Localization class before each test
        Localization._translator = None
        Localization._current_language = None
        Localization._translation_cache = {}

    @patch('lib.localization.os.environ')
    @patch('lib.localization.gettext')
    def test_setup_with_allowed_language(self, mock_gettext, mock_env):
        # Mock environment variable and gettext behavior
        mock_env.get.return_value = 'en'
        translation = MagicMock()
        mock_gettext.translation.return_value = translation

        # Use an allowed language ('ru' or 'ua')
        Localization.setup(language='ru')
        mock_gettext.translation.assert_called_with('aihelper', ANY, languages=['ru'], fallback=True)
        self.assertEqual(Localization._current_language, 'ru')

    @patch('lib.localization.gettext')
    def test_get_text(self, mock_gettext):
        # Setup mock translator
        mock_translator = MagicMock()
        mock_translator.gettext.return_value = 'Saldo'
        Localization._translator = mock_translator

        translated_text = Localization.get_text("Top Up Balance")
        mock_translator.gettext.assert_called_once_with("Top Up Balance")
        self.assertEqual(translated_text, 'Saldo')

    @patch('lib.localization.os.environ')
    @patch('lib.localization.gettext')
    def test_default_language_setup(self, mock_gettext, mock_env):
        mock_env.get.return_value = 'en'
        translation = MagicMock()
        mock_gettext.translation.return_value = translation

        Localization.setup()
        mock_gettext.translation.assert_called_with('aihelper', ANY, languages=['en'], fallback=True)
        self.assertEqual(Localization._current_language, 'en')

    @patch('lib.localization.gettext')
    def test_unavailable_language(self, mock_gettext):
        mock_gettext.translation.return_value = MagicMock()
        Localization.setup(language='xx')  # 'xx' represents an unavailable language
        self.assertEqual(Localization._current_language, 'en')  # Should default to 'en'

    @patch('lib.localization.gettext')
    def test_language_caching(self, mock_gettext):
        mock_translation = MagicMock()
        mock_gettext.translation.return_value = mock_translation

        Localization.setup(language='ru')
        mock_gettext.translation.assert_called_once_with('aihelper', ANY, languages=['ru'], fallback=True)
        mock_gettext.translation.reset_mock()
        Localization.setup(language='ru')
        mock_gettext.translation.assert_not_called()

if __name__ == '__main__':
    unittest.main()
