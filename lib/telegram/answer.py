import os
from pathlib import Path
from docx import Document

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

    def answer_with_voice(self, message):
        """
        Send a voice message to the Telegram chat.

        This method generates a voice message using the OpenAI API,
        saves it to a temporary directory, and then sends it to the chat.

        :param message: The text content to be converted into a voice message.
        """
        voice_answer_folder = Path(__file__).parent.parent.parent / 'tmp' / self.thread_id
        voice_answer_path = voice_answer_folder / "voice_answer.mp3"

        os.makedirs(voice_answer_folder, exist_ok=True)

        response = self.openai.audio.speech.create(
            model="tts-1",  # tts-1-hd
            voice="nova",
            input=message
        )

        response.stream_to_file(voice_answer_path)

        voice_file = open(voice_answer_path, "rb")
        return self.context.bot.send_document(self.chat_id, voice_file)

    def answer_with_image(self, file_id):
        """
        Send an image to the Telegram chat.

        This method fetches an image from the OpenAI API using a file ID,
        saves it to a temporary directory, and then sends it to the chat.

        :param file_id: The ID of the file to fetch and send as an image.
        """
        tmp_folder = Path(__file__).parent.parent.parent / 'tmp'
        os.makedirs(tmp_folder, exist_ok=True)

        image_data = self.openai.files.content(file_id)
        image_data_bytes = image_data.read()

        image_path = tmp_folder / f"{file_id}.png"
        with open(image_path, "wb") as file:
            file.write(image_data_bytes)

        with open(image_path, "rb") as image_file:
            return self.context.bot.send_photo(self.chat_id, image_file)

    def answer_with_annotation(self, annotation_data):
        """
        Send a document to the Telegram chat.

        This method fetches a document from the OpenAI API using annotation data,
        which includes the file ID and the file path with the extension.
        It then saves the document to a temporary directory and sends it to the chat.

        :param annotation_data: A dictionary containing the file ID and the file path.
        """
        tmp_folder = Path(__file__).parent.parent.parent / 'tmp'
        os.makedirs(tmp_folder, exist_ok=True)

        file_id = annotation_data['file_path']['file_id']
        file_extension = os.path.splitext(annotation_data['text'])[1]

        file_data = self.openai.files.content(file_id)
        file_data_bytes = file_data.read()

        file_path = tmp_folder / f"{file_id}{file_extension}"
        with open(file_path, "wb") as file:
            file.write(file_data_bytes)

        with open(file_path, "rb") as document_file:
            return self.context.bot.send_document(self.chat_id, document_file)

    def answer_with_document(self, text: str):
        """
        Send a document to the Telegram chat.

        This method creates a .docx document file with the given text, 
        saves it to a temporary directory specific to the thread ID, 
        and then sends it to the chat.

        :param text: The text content to be written to the document.
        """
        # Define the temporary directory for this thread
        tmp_folder = Path(__file__).parent.parent.parent / 'tmp' / self.thread_id
        os.makedirs(tmp_folder, exist_ok=True)

        # Define the file path for the new document
        document_path = tmp_folder / "output_document.docx"

        # Create a new Document
        doc = Document()
        doc.add_paragraph(text)

        # Save the document
        doc.save(document_path)

        # Send the document to the Telegram chat
        with open(document_path, "rb") as file_to_send:
            return self.context.bot.send_document(self.chat_id, file_to_send)
