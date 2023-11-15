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
python3 -m unittest tests.main_test

### Plan
проверить отправку png файла
научить робота переводить файлы
научить робота генерировать и присылать картинки
научить робота брать оплату
научить робота присылать файлы
сделать подсчет токенов
брать оплату за пользование переводчиком
