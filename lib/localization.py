import gettext
import os
from pathlib import Path

class Localization:
    _translator = None
    _current_language = None
    ALLOWED_LANGUAGES = ['en', 'ru', 'ua']  # Allowed languages
    _translation_cache = {}  # Cache for translations

    @classmethod
    def setup(cls, domain='aihelper', language=None):
        if language in cls.ALLOWED_LANGUAGES:
            cls._current_language = language
        else:
            cls._current_language = os.environ.get('LANGUAGE', 'en') if os.environ.get('LANGUAGE') in cls.ALLOWED_LANGUAGES else 'en'

        cache_key = cls._current_language

        if cache_key in cls._translation_cache:
            cls._translator = cls._translation_cache[cache_key]
            return

        # Define the locale directory
        project_root = Path(__file__).parent.parent
        locale_path = project_root / 'locale'

        # Bind the text domain
        gettext.bindtextdomain(domain, str(locale_path))
        gettext.textdomain(domain)

        # Load the translation for the current language
        translator = gettext.translation(domain, str(locale_path), languages=[cls._current_language], fallback=True)
        translator.install()
        cls._translator = translator
        cls._translation_cache[cache_key] = translator

    @classmethod
    def get_text(cls, message):
        if cls._translator:
            return cls._translator.gettext(message)
        else:
            return message

def change_language(language):
    Localization.setup(language=language)

# Setup the initial language
Localization.setup()
_ = Localization.get_text


# Example usage
# from lib.localization import _, change_language
# print(_("Top Up Balance"))
# change_language(ru)
# print(_("Top Up Balance"))
