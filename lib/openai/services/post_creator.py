import asyncio
from typing import Optional
from db.engine import SessionLocal
from db.models.post import Post
from openai import OpenAI
from lib.openai.image import Image

class PostCreator:
    """
    Class responsible for creating posts by interacting with OpenAI and saving them to the database.
    """

    def __init__(self, assistant_id: Optional[str] = None, model="gpt-3.5-turbo"):
        """
        Initializes the PostCreator with required components.

        :param assistant_id: Optional[str] - The ID of the assistant to use for OpenAI interactions.
        """
        if not assistant_id:
            raise ValueError("Assistant ID is required for PostCreator.")

        self.model = model
        self.assistant_id = assistant_id
        self.openai = OpenAI()
        self.image = Image(self.openai)

    async def create_post(self, message: str, prompt: str = '', language: str = 'ru') -> Optional[Post]:
        """
        Creates a post based on the given prompt by interacting with OpenAI.

        :param prompt: str - The prompt to send to OpenAI.
        :return: Optional[Post] - The created Post object or None if creation failed.
        """
        # Send the prompt to OpenAI and get a response
        text_content = self._create_openai_non_thread_message(message=message, prompt=prompt)

        title = self._create_openai_non_thread_message(message='Сделай заголовок для этого текста: ' + text_content, prompt=prompt)

        # Here you'd include your logic for image generation if needed
        # For now, we'll assume no image is generated
        image_url, revised_prompt = self.image.generate(text_content)

        # Create and save the post to the database
        session = SessionLocal()
        try:
            post = Post(
                text_content=text_content,
                image_url=image_url,
                assistant_id=self.assistant_id,
                language_code=language,
                title=title
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            return post
        except Exception as e:
            print(f"An error occurred while creating a post: {e}")
            return None
        finally:
            session.close()

    def _create_openai_non_thread_message(self, message: str, prompt: Optional[str] = None):
        """
        Generate a non-thread response using the OpenAI API.

        :param message: str - The content of the user's message to be processed.
        :param prompt: Optional[str] - An optional system prompt to provide context.
        :return: The response from the AI.
        """
        try:
            # Prepare the messages for the AI
            messages = []
            if prompt:
                messages.append({"role": "system", "content": prompt})
            messages.append({"role": "user", "content": message})

            # Send the request to OpenAI
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=1.0,
            )

            # Extract and return the AI's response
            return response.choices[0].message.content

        except Exception as e:
            print(f"Failed to generate non-thread message: {e}")
            raise e

# # Example usage
# import asyncio
# import os
# from lib.openai.services.post_creator import PostCreator
# from lib.telegram.services.poster import Poster
# from db.models.post import Post
# from dotenv import load_dotenv

# load_dotenv()

# assistant_id = os.getenv('DIET_ASSISTANT_ID')

# post_creator = PostCreator(assistant_id=assistant_id)
# asyncio.run(post_creator.create_post("Сделай здоровый рецепт из простых продуктовю, которые есть у каждого в холодиьнике."))
