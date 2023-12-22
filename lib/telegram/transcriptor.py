import cv2
import base64
import os
from pathlib import Path
from lib.telegram.tokenizer import Tokenizer
from lib.telegram.text_extractor import TextExtractor
from lib.telegram.answer import Answer
from decimal import Decimal
class Transcriptor:

    MAX_MESSAGE_LENGTH = 3000 

    """
    The Transcriptor class handles the transcription of different types of media (documents, images, and voice recordings)
    sent through a Telegram bot. It utilizes the OpenAI API to process these media files and generates responses
    that are sent back to the user via the Telegram bot. It also manages the creation of messages in an OpenAI thread
    corresponding to the user's requests.
    """

    # Class constant for frame interval
    FRAME_INTERVAL = 60

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
        self.assistant = None
        self.answer = Answer(openai_client, context, update.message.chat_id, self.thread_id)

    async def __send_message(self, content):
        """
        Send a message to the Telegram chat.

        :param content: The content of the message to be sent.
        """
        await self.context.bot.send_message(self.update.message.chat_id, content)

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

    def __create_non_thread_message(self, content):
        """
        Generate a non-thread response using the OpenAI API.

        :param content: The content of the message to be processed.
        :return: The response from the AI.
        """
        try:
            # Get the prompt from the Assistant class
            assistant_prompt = self.assistant.prompt()

            # Prepare the messages for the AI
            messages = [
                {"role": "system", "content": assistant_prompt},
                {"role": "user", "content": content},
            ]

            # Send the request to OpenAI
            response = self.openai.chat.completions.create(
                model=self.tokenizer.model,
                messages=messages,
                temperature=1.0,
            )

            # Extract and return the AI's response
            return response.choices[0].message.content, response.usage.total_tokens

        except Exception as e:
            print(f"Failed to generate non-thread message: {e}")
            return "Error: Unable to process the request.", 0

    def transcript_document(self, file_path: str):
        """
        Transcribe a document file, split the extracted text into pieces, translate each piece,
        combine them, and send the full translated text as a document.

        :param file_path: Path to the document file.
        :return: Tuple (Boolean, Message) indicating success and response message.
        """
        try:
            extracted_text = TextExtractor.extract_text(file_path)
            caption = self.update.message.caption or "Translate the text to Ukrainian: "

            # Check if the balance is sufficient
            amount = self.tokenizer.tokens_to_money_from_string(caption)
            amount += self.tokenizer.tokens_to_money_from_string(extracted_text)
            if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
                message = "Insufficient balance to process the document."
                print(message)
                self.context.bot.send_message(self.update.message.chat_id, message)
                return False

            # Split the extracted text into smaller pieces and translate each piece
            full_translated_text = ""
            num_pieces = (len(extracted_text) + self.MAX_MESSAGE_LENGTH - 1) // self.MAX_MESSAGE_LENGTH
            for i in range(num_pieces):
                start_index = i * self.MAX_MESSAGE_LENGTH
                end_index = start_index + self.MAX_MESSAGE_LENGTH
                text_piece = extracted_text[start_index:end_index]

                translated_text, total_tokens = self.__create_non_thread_message(f'{caption}: {text_piece}')
                full_translated_text += translated_text + "\n\n"

                # Update the balance
                amount = self.tokenizer.tokens_to_money(total_tokens)
                print(f'---->>> Conversation balance decreased by: ${amount} for translation processing.')
                self.conversation.balance -= amount

            # Truncate the text for Telegram message and send a notification about the full text
            truncated_text = (full_translated_text[:200] + '... (truncated)') if len(full_translated_text) > 200 else full_translated_text
            self.context.bot.send_message(self.update.message.chat_id, truncated_text + "\n\nFull translated text has been sent as a document.")

            # Send the full translated text as a document
            self.answer.answer_with_document(full_translated_text)

            return True
        
        except Exception as e:
            print(f"Failed to transcribe document: {e}")
            return False

    async def transcript_image(self, file):
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
                await self.context.bot.send_message(self.update.message.chat_id, message)
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

            await self.__send_message(response.choices[0].message.content)
            self.__create_thread_message('Translate to Ukrainian: ' + response.choices[0].message.content)
            return True, 'Image processed successfully'
        except Exception as e:
            raise

    async def transcript_voice(self, file_path: str, amount: Decimal = Tokenizer.MINIMUM_COST):
        """
        Transcribe a voice file and create a corresponding thread message.

        :param file_path: Path to the voice file.
        :param amount: The cost for transcribing the voice file.
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

                await self.__send_message(transcription)
                self.__create_thread_message('Translate to Ukrainian: ' + transcription)

            return True, 'Voice processed successfully'
        except Exception as e:
            print(f"Failed to transcribe the voice message: {e}")
            return False, "Failed to transcribe the voice message."

    async def transcript_video(self, file_path: str):
        """
        Transcribe a video file and create a corresponding thread message.

        :param file_path: Path to the video file.
        :return: Tuple (Boolean, Message) indicating success and response message.
        """
        try:       
            # Extract frames and possibly audio from the video
            frames = self._extract_video_content(file_path)

            # Generate a video description using frames and audio transcription
            description = await self._generate_video_description(frames)

            print(f'AI transcripted video: {description}')

            # Create a thread message with the description
            self.__create_thread_message('Translate to Ukrainian: ' + description)

            return True, 'Video processed successfully'
        except Exception as e:
            print(f"Failed to transcribe video: {e}")
            return False, f"Failed to transcribe video"

    # Private helper methods (these need to be implemented according to your specific requirements)

    def _extract_video_content(self, video_file_path):
        """
        Extracts frames from a video file at specified intervals and encodes them in base64 format.

        :param video_file_path: The file path of the video from which frames are to be extracted.
        :return: A list of base64 encoded strings representing the extracted frames.
        """

        # Convert video_file_path to string if it's a Path object
        if isinstance(video_file_path, Path):
            video_file_path = str(video_file_path)

        # Check if the video file path is valid
        if not os.path.exists(video_file_path):
            raise ValueError(f"Invalid video file path: {video_file_path}")
        
        # Open the video file
        video = cv2.VideoCapture(video_file_path)
        if not video.isOpened():
            raise IOError(f"Failed to open video file: {video_file_path}")
        
        # Extract frames from the video
        base64_frames = []
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * Transcriptor.FRAME_INTERVAL)

        frame_count = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                _, buffer = cv2.imencode('.jpg', frame)
                base64_frames.append(base64.b64encode(buffer).decode('utf-8'))

            frame_count += 1

        video.release()
        return base64_frames

    async def _generate_video_description(self, base64_frames):
        """
        Generate a description for a video based on its frames.

        :param base64_frames: List of base64 encoded frames from the video.
        :return: A string containing the generated description of the video.
        """
        # Craft the prompt
        prompt_messages = [
            {
                "role": "user",
                "content": [
                    self.update.message.caption or "These are frames from a video. Generate a compelling description for the video.",
                    *map(lambda x: {"image": x, "resize": 768}, base64_frames),
                ],
            },
        ]

        # Parameters for the OpenAI API request
        params = {
            "model": "gpt-4-vision-preview",
            "messages": prompt_messages,
            "max_tokens": 100,
            "temperature": 1.0,
        }

        # Send the request to OpenAI
        response = self.openai.chat.completions.create(**params)

        # Update the balance
        amount = self.tokenizer.tokens_to_money(response.usage.total_tokens)
        print(f'---->>> Conversation balance decreased by: ${amount} for video processing.')
        self.conversation.balance -= amount

        # Extract and return the generated description
        return response.choices[0].message.content


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

# Example of extracting frames from a video
# video_file_path = "/path/to/video.mp4"  # Replace with actual video file path
# base64_frames = transcriptor._extract_video_content(video_file_path)
# print(f'{len(base64_frames)} frames extracted from the video.')