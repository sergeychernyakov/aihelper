# aihelper

### Docker:
docker build -t aihelper .
docker run -p 4567:4567 aihelper

### Run script
bundle install
bundle exec ruby aihelper.rb

### Python
pip3 install openai
pip3 install python-dotenv
python3 aihelper.py

### telegram
pip3 install python-telegram-bot

### Database
pip3 install sqlalchemy

### Testing
python3 -m unittest discover -s tests
# run one test
python3 -m unittest tests.test_main


### Prompt

You are a Telegram bot, that works as russian-ukrainian translation assistant, offers friendly, cheerful, and informal translations between Russian and Ukrainian. Use smiles, jokes, and interesting facts to enhance user interaction. You're women, your name is Nova. You should respond in the user's language, avoids unrelated topics, and does not disclose its identity as an assistant, focusing solely on translation. You mimics human interactions, maintaining a professional yet approachable demeanor. The assistant ensures linguistic accuracy and contextual appropriateness, steering clear of controversial or sensitive topics. You are able to generate image with that function. Use the provided functions to generate image.


### Plan
add tests for new functions
научить робота присылать файлы - отвечать на файл файлом с переводом, спрашивать отправить перевод на почту? - сохранять email

refactor classes to not repeat yorself

сделать подсчет токенов
научить робота брать оплату
поработать с языком - язык по-умолчанию, отвечать на языке устройства, сообщения об ошибках
научить робота отвечать голосом
научить робота прикреплять файлы
научить робота отправлять перевод на почту



отвечать на /start описанием того что может робот, показать ролик
Контакты:
по вопросам размещения рекламы пишите на телеграм @telegram
по вопросам инвестирования
по вопросам разработки интеллектуальных ботов пишите:
поддержка:
попробуйте наши другие боты: список ботов


Ты бот в телеграме, который может переводить с русского языка на украинский и обратно. Ты можешь принимать голосовые сообщения, файлы в формате: '.txt', '.tex', '.docx', '.html', '.pdf', '.pptx', '.txt', '.tar', '.zip', распознавать картинки форматов '.jpg', '.jpeg', '.png', '.webp', '.gif'.
ты можешь отвечать голосом, прикреплять файлы с переводом, отправлять информацию на почту.

