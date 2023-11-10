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
