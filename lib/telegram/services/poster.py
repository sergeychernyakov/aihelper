from typing import List, Optional
from telegram.ext import Application
from telegram.error import BadRequest, Forbidden
from db.engine import SessionLocal
from db.models.conversation import Conversation
from db.models.post import Post

class Poster:
    def __init__(self, telegram_token: str):
        """
        Initialize the Poster class.

        :param telegram_token: str - The token used for the Telegram bot.
        """
        # Initialize Telegram Application with the provided bot token
        self.application = Application.builder().token(telegram_token).build()

    async def send_to_all(self, post: Post, user_ids: Optional[List[int]] = None):
        """
        Asynchronously send a post to a specified list of users or all users.

        :param post: Post - The post object containing the message to be sent.
        :param user_ids: Optional[List[int]] - A list of user IDs to whom the message will be sent.
                         If None, the message is sent to all users in the database.
        """
        session = SessionLocal()
        try:
            conversations = None
            if user_ids is None:
                # Fetch conversations with disabled = False
                conversations = session.query(Conversation).filter(Conversation.disabled == False).all()
                user_ids = [conv.user_id for conv in conversations]
            
            for user_id in user_ids:
                try:
                    # Send text message
                    await self.application.bot.send_message(chat_id=user_id, text=post.text_content)
                    post.message_count += 1  # Increment message count for text
                    
                    # Send photo only if the photo URL is present
                    if post.image_url:
                        await self.application.bot.send_photo(chat_id=user_id, photo=post.image_url)
                        post.message_count += 1  # Increment message count for photo

                except BadRequest as e:
                    print(f"BadRequest: Failed to send message to chat_id {user_id}: {e}")
                except Forbidden as e:
                    print(f"Forbidden: The bot was blocked by the user {user_id}: {e}")
                    # Disable the conversation for this user_id
                    if conversations:
                        blocked_conversation = next((conv for conv in conversations if conv.user_id == user_id), None)
                        if blocked_conversation:
                            blocked_conversation.disabled = True

            # Commit any changes to the database
            session.commit()

        finally:
            # Close the session
            session.close()

# Usage example (replace the telegram_token with your actual value)
# import asyncio
# import os
# from lib.telegram.services.poster import Poster
# from db.models.post import Post

# telegram_token = os.getenv('DIET_TELEGRAM_BOT_TOKEN')
# poster = Poster(telegram_token)

# # Assuming you have a Post object
# post = Post(text_content="Hello, this is a test message!")

# # Example sending the post to all users
# asyncio.run(poster.send_to_all(post))

# # Example sending the post to specific users
# specific_user_ids = [6532446798, 5545639645, 6783964311]
# asyncio.run(poster.send_to_all(post, user_ids=specific_user_ids))
