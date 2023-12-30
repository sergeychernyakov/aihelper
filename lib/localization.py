import gettext
import os
from pathlib import Path

class _Localization:
    _translator = None
    _current_language = None

    @classmethod
    def setup(cls, domain='aihelper', language=None):
        if language is not None:
            cls._current_language = language
        else:
            cls._current_language = os.environ.get('LANGUAGE', 'en')

        # Define the locale directory
        project_root = Path(__file__).parent.parent
        locale_path = project_root / 'locale'

        # Bind the text domain
        gettext.bindtextdomain(domain, str(locale_path))
        gettext.textdomain(domain)

        # Load the translation for the current language
        cls._translator = gettext.translation(domain, str(locale_path), languages=[cls._current_language], fallback=True)
        cls._translator.install()

    @classmethod
    def get_text(cls, message):
        if cls._translator:
            return cls._translator.gettext(message)
        else:
            return message

def change_language(language):
    _Localization.setup(language=language)

# Setup the initial language
_Localization.setup()
_ = _Localization.get_text


# Example usage
# import os
# from lib.localization import _
# os.environ['LANGUAGE'] = 'ru'

# print(_("Top Up Balance"))
