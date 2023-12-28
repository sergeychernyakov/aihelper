import gettext
import os
from pathlib import Path

class _Localization:
    _translator = None
    _initialized = False

    @classmethod
    def setup(cls, domain='aihelper', locale_dir='locale', default_language='en'):
        if cls._initialized:
            return cls._get_text

        # Define the locale directory
        project_root = Path(__file__).parent.parent
        locale_path = project_root / locale_dir

        # Bind the text domain
        gettext.bindtextdomain(domain, str(locale_path))
        gettext.textdomain(domain)

        # Set the default language
        os.environ['LANGUAGE'] = default_language

        # Load the translation
        cls._translator = gettext.translation(domain, str(locale_path), languages=[default_language], fallback=True)
        cls._translator.install()

        cls._initialized = True
        return cls._get_text

    @classmethod
    def _get_text(cls, message):
        if cls._translator:
            return cls._translator.gettext(message)
        else:
            return message

def setup_localization(domain='aihelper', locale_dir='locale', default_language='en'):
    return _Localization.setup(domain, locale_dir, default_language)

_ = setup_localization()
