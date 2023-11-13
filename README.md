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


Done! Congratulations on your new bot. You will find it at t.me/AiHelper_GptBot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

Use this token to access the HTTP API:
TELEGRAM_TOKEN_REDACTED
Keep your token secure and store it safely, it can be used by anyone to control your bot.

For a description of the Bot API, see this page: https://core.telegram.org/bots/api