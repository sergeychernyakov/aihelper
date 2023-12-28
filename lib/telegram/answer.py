import os
from pathlib import Path
from docx import Document
import aiohttp
from io import BytesIO
from lib.localization import _

class Answer:
    def __init__(self, openai_client, context, chat_id, thread_id):
        """
        Initialize the Answer object with necessary parameters.

        :param openai_client: The OpenAI client used for making API requests.
        :param context: The context of the bot, containing relevant information and utilities.
        :param chat_id: The ID of the Telegram chat where messages will be sent.
        :param thread_id: The ID of the thread for the conversation.
        """
        self.openai = openai_client
        self.context = context
        self.chat_id = chat_id
        self.thread_id = thread_id

    async def answer_with_text(self, message):
        """
        Send a text message to the Telegram chat.

        :param message: The content of the text message to be sent.
        """
        await self.context.bot.send_message(self.chat_id, message)

    async def answer_with_voice(self, message):
        """
        Send a voice message to the Telegram chat.

        This method generates a voice message using the OpenAI API
        and sends it directly to the chat without saving it to a temporary directory.

        :param message: The text content to be converted into a voice message.
        """
        # Generate a voice message using the OpenAI API
        response = self.openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=message
        )

        # Stream the audio data to a BytesIO object
        voice_data_bytes = response.read()
        voice_file = BytesIO(voice_data_bytes)
        voice_file.name = "voice_answer.mp3" # Set a name for the file to be sent
        voice_file.seek(0) # Reset the pointer to the beginning of the BytesIO object

        # Send the voice message to the Telegram chat
        await self.context.bot.send_voice(self.chat_id, voice=voice_file)

    async def answer_with_image(self, file_id):
        """
        Send an image to the Telegram chat.

        This method fetches an image from the OpenAI API using a file ID and
        sends it to the chat without saving it to a temporary directory.

        :param file_id: The ID of the file to fetch and send as an image.
        """
        async with self.openai.files.content(file_id) as response:
            if response.status == 200:
                image_data_bytes = await response.read()

                # Use BytesIO to create a file-like object from the bytes, which can be sent directly
                image_file = BytesIO(image_data_bytes)
                image_file.name = f"{file_id}.png"  # Set a name for the file to be sent

                await self.context.bot.send_photo(self.chat_id, photo=image_file)
            else:
                # Handle error in fetching the image
                await self.context.bot.send_message(self.chat_id, _("Failed to fetch image with file."))

    async def answer_with_annotation(self, annotation_data):
        """
        Send a document to the Telegram chat.

        This method fetches a document from the OpenAI API using annotation data,
        creates a file-like object in memory using BytesIO, and sends it to the chat
        without saving it to a temporary directory.

        :param annotation_data: A dictionary containing the file ID and the file path.
        """
        file_id = annotation_data['file_path']['file_id']
        file_extension = os.path.splitext(annotation_data['text'])[1]

        # Fetch the file content from the OpenAI API
        async with self.openai.files.content(file_id) as response:
            if response.status == 200:
                file_data_bytes = await response.read()

                # Use BytesIO to create a file-like object from the bytes
                document_file = BytesIO(file_data_bytes)
                document_file.name = f"{file_id}{file_extension}"  # Set a name for the file to be sent

                # Send the document to the Telegram chat
                await self.context.bot.send_document(self.chat_id, document_file)
            else:
                # Handle error in fetching the file
                print(f"Failed to fetch document with file_id {file_id}.")

    async def answer_with_document(self, text: str):
        """
        Send a document to the Telegram chat.

        This method creates a .docx document file with the given text and sends it directly
        to the chat using a BytesIO object, without saving it to a temporary directory.

        :param text: The text content to be written to the document.
        """
        # Create a new Document in memory
        doc = Document()
        doc.add_paragraph(text)

        # Use BytesIO to create a file-like object
        doc_file = BytesIO()
        doc.save(doc_file)
        doc_file.name = "translated_document.docx"  # Set a name for the file to be sent
        doc_file.seek(0)  # Reset the pointer to the beginning of the BytesIO object

        # Send the document to the Telegram chat
        await self.context.bot.send_document(self.chat_id, doc_file)
