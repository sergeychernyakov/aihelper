from lib.telegram.tokenizer import Tokenizer
from lib.telegram.text_extractor import TextExtractor
from decimal import Decimal
class Transcriptor:
    """
    The Transcriptor class handles the transcription of different types of media (documents, images, and voice recordings)
    sent through a Telegram bot. It utilizes the OpenAI API to process these media files and generates responses
    that are sent back to the user via the Telegram bot. It also manages the creation of messages in an OpenAI thread
    corresponding to the user's requests.
    """
    def __init__(self, openai_client, update, context, conversation):
        """
        Initialize the Transcriptor class.

        :param openai_client: OpenAI client instance for API calls.
        :param update: Telegram update object containing message details.
        :param context: Telegram context object for the bot.
        :param thread_id: Thread ID for the OpenAI conversation.
        :param assistant_id: Assistant ID for the OpenAI conversation.
        """
        self.openai = openai_client
        self.update = update
        self.context = context
        self.conversation = conversation
        self.thread_id = conversation.thread_id
        self.assistant_id = conversation.assistant_id
        self.tokenizer = Tokenizer()

    def __send_message(self, content):
        """
        Send a message to the Telegram chat.

        :param content: The content of the message to be sent.
        """
        self.context.bot.send_message(self.update.message.chat_id, content)

    def __create_thread_message(self, content, file_ids=None):
        """
        Create a message in the OpenAI thread.

        :param content: The content of the message to be created in the thread.
        :param file_ids: List of file IDs to be attached to the message (optional).
        """
        return self.openai.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=content,
            file_ids=file_ids if file_ids else []
        )

    def transcript_document(self, file_path: str):
        """
        Transcribe a document file and create a corresponding thread message.

        :param file_path: Path to the document file.
        :return: Tuple (Boolean, Message) indicating success and response message.
        """
        try:
            extracted_text = TextExtractor.extract_text(file_path)
            caption = self.update.message.caption or "Translate the text to Ukrainian: "
            self.__create_thread_message(f'{caption}: {extracted_text}')
            return True
        except Exception as e:
            raise

    def transcript_image(self, file):
        """
        Transcribe an image file and create a corresponding thread message.

        :param file: Telegram file object for the image.
        :return: Tuple (Boolean, Message) indicating success and response message.
        """
        try:
            caption = self.update.message.caption or "What's in this image? If there's text, extract it."
        
            #calculate caption
            amount = self.tokenizer.tokens_to_money_from_string(caption)
            amount += self.tokenizer.tokens_to_money_from_image()
            # Check if the balance is sufficient
            if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
                message = "Insufficient balance to process the image."
                print(message)
                self.context.bot.send_message(self.update.message.chat_id, message)
                return False

            response = self.openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": caption}, {"type": "image_url", "image_url": {"url": file.file_path, "detail": "low"}}]}
                ],
                max_tokens=100,
                temperature=1.0,
            )

            # Update the balance
            amount = self.tokenizer.tokens_to_money(response.usage.total_tokens)
            print(f'---->>> Conversation balance decreased by: ${amount} for image processing.')
            self.conversation.balance -= amount

            self.__send_message(response.choices[0].message.content)
            self.__create_thread_message('Translate to Ukrainian: ' + response.choices[0].message.content)
            return True, 'Image processed successfully'
        except Exception as e:
            raise

    def transcript_voice(self, file_path: str, amount: Decimal = 0):
        """
        Transcribe a voice file and create a corresponding thread message.

        :param file_path: Path to the voice file.
        :return: Tuple (Boolean, Message) indicating success and response message.
        """
        try:
            with open(file_path, "rb") as audio_file:
                transcription = self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    temperature='1.0'
                )

                # Update the balance
                print(f'---->>> Conversation balance decreased by: ${amount} for voice transcription.')
                self.conversation.balance -= amount

                self.__send_message(transcription)
                self.__create_thread_message('Translate to Ukrainian: ' + transcription)
            return True, 'Voice processed successfully'
        except Exception as e:
            return False, f"Failed to transcribe document: {e}"


# Example of usage

# # Initialize necessary components
# openai_client = get_openai_client()
# update = get_telegram_update()
# context = get_telegram_context()
# thread_id = "your_thread_id"  # Replace with actual thread ID
# assistant_id = "your_assistant_id"  # Replace with actual assistant ID

# # Create an instance of Transcriptor
# transcriptor = Transcriptor(openai_client, update, context, conversation)

# # Example usage scenarios
# # Scenario 1: Transcribing a document
# file_path = "/path/to/document.pdf"  # Replace with actual file path
# success, message = transcriptor.transcript_document(file_path)
# print(f"Transcription success: {success}, Message: {message}")

# # Scenario 2: Transcribing an image
# image_file = update.message.photo[-1]  # Assuming the last photo in the array is the one you want to transcribe
# transcriptor.transcript_image(image_file)

# # Scenario 3: Transcribing a voice message
# voice_file_path = "/path/to/voice_message.ogg"  # Replace with actual voice file path
# transcriptor.transcript_voice(voice_file_path)
