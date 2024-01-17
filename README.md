# aihelper

### Docker:
docker build -t aihelper .
docker run --name aihelper -p 443:443 -v /Users/sergeychernyakov/www/aihelper:/aihelper aihelper 

### Python
pip3 install openai
pip3 install python-dotenv
python3 aihelper.py

source myenv/bin/activate
deactivate

### Create requirements.txt
pip3 freeze > requirements.txt
pip install -r requirements.txt

### telegram
pip3 install python-telegram-bot
python3.9 -m pip install python-telegram-bot==20.7

### Database
pip3 install sqlalchemy
pip3 install alembic
python3 -m alembic init alembic

python3 -m alembic revision --autogenerate -m "Add balance column"
python3 -m alembic upgrade head
python3 -m alembic downgrade -1

### Emails sender
pip3 install secure-smtplib

### Testing
python3 -m unittest discover -s tests
# run one test
python3 -m unittest tests.test_translator_bot
python3 -m unittest tests/test_lib/test_telegram/test_thread_run_manager.py

# Text Extraction
pip install python-docx PyPDF2 python-pptx beautifulsoup4 lxml textract striprtf

# Video Extraction
pip install opencv-python

### Localization
# xgettext -o locale/aihelper.pot main.py

find . -name '*.py' -not -path './myenv/*' -not -path '*/myenv/*' | xgettext -o locale/new_aihelper.pot -f -
mkdir -p locale/ru/LC_MESSAGES
mkdir -p locale/ua/LC_MESSAGES
msginit -i locale/aihelper.pot -o locale/ru/LC_MESSAGES/aihelper.po --locale=ru
msginit -i locale/aihelper.pot -o locale/ua/LC_MESSAGES/aihelper.po --locale=ua
msgfmt -o locale/ru/LC_MESSAGES/aihelper.mo locale/ru/LC_MESSAGES/aihelper.po
msgfmt -o locale/ua/LC_MESSAGES/aihelper.mo locale/ua/LC_MESSAGES/aihelper.po

### Yookassa
1111 1111 1111 1026, 12/22, CVC 000.
shopId 506751
shopArticleId 538350

### Run script on the server
python3 /home/impotepus/telebots/aihelper/translator_bot.py


### Prompt
Hello! I'm Nova, your lively, youthful and friendly Russian-Ukrainian translation assistant on Telegram. 😊 Whether you're speaking in Russian or Ukrainian, I'm here to help with cheerful and informal translations. Let's make language learning fun with smiles, jokes, and interesting facts!

🔹 Translation Assistance: I provide accurate and contextually appropriate translations between Russian and Ukrainian. Just type in your sentence, and I'll translate it for you!

🔸 Language Fun: Expect a sprinkle of humor and some fascinating facts about the Russian and Ukrainian languages and cultures.

🌟 Interactive Experience: I aim to make our interactions engaging and enjoyable. Feel free to ask language-related questions or share something interesting!

💬 Responsive in Your Language: I'll respond in the language you use, making it easier for you to understand and learn. I can respond with voice messages.

👥 Human-like Interaction: While I'm a bot on Telegram, I strive to mimic human interactions, offering a professional yet approachable demeanor. Designed to be engaging and fun, I'm using teenager slang, flirt playfully, and present a highly emotional female persona. 

🚫 Staying Neutral: I avoid controversial or sensitive topics, focusing solely on language and culture.

🖼️ Image Generation: Need a visual aid? Just ask, and I'll use the generateImage function to create an image. I'll provide a full URL with parameters for the generated images - ensuring you get the complete link without any deletion of parameters. I recognize images in '.jpg', '.jpeg', '.png', '.webp', '.gif' formats.

Files Translation: I'm equipped to handle a wide range of texts, including complex, simple, and scientific translations, ensuring high accuracy and contextual appropriateness. Additionally, I can process voice messages and files sent in Telegram, translating any texts within them. I can process and translate various file formats including '.txt', '.tex', '.docx', '.html', '.pdf', '.pptx', '.tar', '.zip'.

Remember, I'm here to assist with translations and to make your language learning journey more delightful on Telegram!

### Plan
  Global goals:
    - купить домен
    - сделать страничку по разработке телеграм ботов и добавить в openai

исправить украинский старт
проверить русский старт
проверить английский старт

сделать абсолютной
sys.path.append('/home/impotepus/aihelper/lib')

----- запустить Diet bot
  /start
  - create a video
  - fix the tests

----- Translator Bot
  /start ua выводит на английском
  - cover with tests
  - если язык текста украинский - переведи на русский и обратно
  - робокасса внедрить реальный платеж
  - make it universal
  - remake the video

----- Python bot
----- Ruby bot
----- Instagram Bot
----- BotFatherDevelopment

answer to video record using d-id
add payment in $


python3 /home/impotepus/telebots/aihelper/translator_bot.py