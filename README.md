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



### Plan
научить робота генерировать и присылать картинки

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

