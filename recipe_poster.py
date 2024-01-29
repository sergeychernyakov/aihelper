#!/usr/bin/env python3

import sys

# Adjust the path as necessary
sys.path.append('/home/impotepus/aihelper/lib')

import asyncio
import os
from lib.openai.services.post_creator import PostCreator
from lib.telegram.services.poster import Poster
from db.models.post import Post
from dotenv import load_dotenv

def main():
    load_dotenv()
    telegram_token = os.getenv('DIET_TELEGRAM_BOT_TOKEN')
    assistant_id = os.getenv('DIET_ASSISTANT_ID')
    poster = Poster(telegram_token)
    post_creator = PostCreator(assistant_id=assistant_id)
    post = asyncio.run(post_creator.create_post("Сделай здоровый рецепт из простых продуктовю, которые есть у каждого в холодиьнике."))

    # asyncio.run(poster.send_to_all(post))
    asyncio.run(poster.send_to_all(post, user_ids = [6783964311,5545639645,6532446798]))

if __name__ == "__main__":
    main()
