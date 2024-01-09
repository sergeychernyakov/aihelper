import cv2
import base64
import os
from pathlib import Path
from lib.localization import _

class NewTranscriptor:
    MAX_MESSAGE_LENGTH = 3000

    """
    The Transcriptor class handles the transcription of different types of media (documents, images, voice recordings, and videos)
    sent through a Telegram bot. It utilizes the OpenAI API to process these media files and generates responses
    that are sent back to the user via the Telegram bot.
    """

    # Class constant for frame interval in video processing
    FRAME_INTERVAL = 60

    def __init__(self, openai_client):
        """
        Initialize the Transcriptor class.

        :param openai_client: OpenAI client instance for API calls.
        """
        self.openai = openai_client

    async def transcript_photo(self, file_path: str, caption: str):
        """
        Transcribe an image file and create a corresponding response.

        :param file_path: File path or URL of the image.
        :param caption: Caption or additional text information to accompany the image.
        :return: Transcription text and the number of tokens used.
        """
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": caption}, {"type": "image_url", "image_url": {"url": file_path, "detail": "low"}}]}
                ],
                max_tokens=100,
                temperature=1.0,
            )

            return response.choices[0].message.content, response.usage.total_tokens

        except Exception as e:
            print(f"Failed to transcribe the image message: {e}")
            raise

    async def transcript_voice(self, file_path: str) -> str:
        """
        Transcribe a voice file and create a corresponding response.

        :param file_path: Path to the voice file.
        :return: Transcription text and the number of tokens used.
        """
        try:
            with open(file_path, "rb") as audio_file:
                transcription = self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    temperature='1.0'
                )

            return transcription
        except Exception as e:
            print(f"Failed to transcribe the voice message: {e}")
            raise

    async def transcript_video(self, file_path: str, caption: str):
        """
        Transcribe a video file and create a corresponding response.

        :param file_path: Path to the video file.
        :param caption: Caption or additional text information to accompany the video.
        :return: Transcription text and the number of tokens used.
        """
        try:       
            # Extract frames from the video for transcription
            frames = self._extract_video_content(file_path)

            # Generate a video description using the extracted frames
            description, total_tokens = await self._generate_video_description(frames, caption)

            print(f'AI transcripted video: {description}')

            return description, total_tokens
        except Exception as e:
            print(f"Failed to transcribe video: {e}")
            raise

    # Private helper methods (these need to be implemented according to your specific requirements)

    def _extract_video_content(self, video_file_path):
        """
        Extracts frames from a video file at specified intervals and encodes them in base64 format.

        :param video_file_path: The file path of the video from which frames are to be extracted.
        :return: A list of base64 encoded strings representing the extracted frames.
        """
        if isinstance(video_file_path, Path):
            video_file_path = str(video_file_path)

        if not os.path.exists(video_file_path):
            raise ValueError(f"Invalid video file path: {video_file_path}")
        
        video = cv2.VideoCapture(video_file_path)
        if not video.isOpened():
            raise IOError(f"Failed to open video file: {video_file_path}")
        
        base64_frames = []
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.FRAME_INTERVAL)
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

    async def _generate_video_description(self, base64_frames, caption: str = None):
        """
        Generate a description for a video based on its frames.

        :param base64_frames: List of base64 encoded frames from the video.
        :param caption: Optional caption to provide context for the video description.
        :return: A string containing the generated description of the video and the number of tokens used.
        """
        prompt_messages = [
            {
                "role": "user",
                "content": [
                    caption or "These are frames from a video. Generate a compelling description for the video.",
                    *map(lambda x: {"image": x, "resize": 768}, base64_frames),
                ],
            },
        ]

        params = {
            "model": "gpt-4-vision-preview",
            "messages": prompt_messages,
            "max_tokens": 100,
            "temperature": 1.0,
        }

        response = self.openai.chat.completions.create(**params)
        return response.choices[0].message.content, response.usage.total_tokens


# Example of usage

# from lib.telegram.transcriptor import Transcriptor

# # Assuming necessary components are initialized
# openai_client = get_openai_client()  # Function to get an initialized OpenAI client

# # Create an instance of the Transcriptor
# transcriptor = Transcriptor(openai_client)

# # Example usage scenarios:

# # Scenario 1: Transcribing an image
# image_file_path = "/path/to/image.jpg"  # Replace with the actual image file path
# image_caption = "Describe this image"   # Caption for the image
# transcripted_text, tokens_used = await transcriptor.transcript_photo(image_file_path, image_caption)
# print(f"Transcribed text: {transcripted_text}, Tokens used: {tokens_used}")

# # Scenario 2: Transcribing a voice message
# voice_file_path = "/path/to/voice_message.ogg"  # Replace with the actual voice file path
# transcripted_text = await transcriptor.transcript_voice(voice_file_path)
# print(f"Transcribed text: {transcripted_text}")

# # Scenario 3: Transcribing a video
# video_file_path = "/path/to/video.mp4"  # Replace with the actual video file path
# video_caption = "Describe the content of this video"  # Caption for the video
# description, tokens_used = await transcriptor.transcript_video(video_file_path, video_caption)
# print(f"Video description: {description}, Tokens used: {tokens_used}")

# # Note: These functions (get_openai_client, etc.) are placeholders and need to be
# # defined according to your application's context. Also, the transcriptor methods are asynchronous and
# # should be awaited in an async environment.
