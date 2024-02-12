#!/usr/bin/env python3

import sys
import asyncio
import os
import logging
from lib.openai.services.post_creator import PostCreator
from lib.telegram.services.poster import Poster
from db.models.post import Post
from dotenv import load_dotenv

from db.engine import SessionLocal  # Import your SessionLocal

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    setup_logging()

    try:
        load_dotenv()
        telegram_token = os.getenv('DIET_TELEGRAM_BOT_TOKEN')
        assistant_id = os.getenv('DIET_ASSISTANT_ID')

        if not telegram_token or not assistant_id:
            logging.error("Environment variables DIET_TELEGRAM_BOT_TOKEN or DIET_ASSISTANT_ID are not set.")
            return

        logging.info("Creating Poster and PostCreator instances.")
        poster = Poster(telegram_token)
        post_creator = PostCreator(assistant_id=assistant_id)

        logging.info("Creating a new post.")
        post = asyncio.run(post_creator.create_post("Сделай здоровый рецепт из простых продуктовю, которые есть у каждого в холодиьнике, не более 900 символов."))

        # session = SessionLocal()
        # post = session.query(Post).order_by(Post.created_at.desc()).first()

        if post is None:
            logging.error("Failed to create a post.")
            return

        logging.info(f"Sending post to users: {post.text_content}")
        asyncio.run(poster.send_to_all(post))
        # asyncio.run(poster.send_to_all(post, user_ids=[6783964311, 6783964311, 5545639645, 6532446798]))

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
