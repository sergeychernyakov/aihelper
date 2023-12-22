import os
import requests
from pathlib import Path
from lib.telegram.constraints_checker import ConstraintsChecker
from lib.telegram.tokenizer import Tokenizer

class MessagesHandler:
    def __init__(self, openai_client, update, context, conversation):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.conversation = conversation
        self.thread_id = conversation.thread_id
        self.tokenizer = Tokenizer()

    def handle_text_message(self, message):
        try:
            # Process the message
            self.openai.beta.threads.messages.create(thread_id=self.thread_id, role="user", content=message)
            return True, "Message processed successfully."
        except Exception as e:
            print(f"Error in handle_text_message: {e}")
            raise

    async def handle_photo_message(self):
        try:
            # take the photo near to 512x512px for vision low res mode
            photo = self.update.message.photo[-2]
            file = await self.context.bot.get_file(photo.file_id)

            # fix check_file_constraints
            success, message = ConstraintsChecker.check_photo_constraints(file, photo)
            if not success:
                return False, message, None

            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size} {photo.width}x{photo.height} "{self.update.message.caption}"')

            message = "Image processed successfully"
            return True, message, file
        except Exception as e:
            raise

    async def handle_voice_message(self):
        try:
            # Extract voice message details
            voice = self.update.message.voice
            file_info = await self.context.bot.get_file(voice.file_id)

            # Check constraints on the voice message
            success, message = ConstraintsChecker.check_voice_constraints(file_info)
            if not success:
                return False, message, None, None

            # Calculate the cost of processing the voice message
            amount = self.tokenizer.tokens_to_money_from_voice(voice.duration)
            if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
                insufficient_balance_message = "Insufficient balance to process the voice message."
                print(insufficient_balance_message)
                await self.context.bot.send_message(self.update.message.chat_id, insufficient_balance_message)
                return False, insufficient_balance_message, None, amount

            # Define local file path for the voice message
            project_root = Path(__file__).parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id
            os.makedirs(tmp_dir_path, exist_ok=True)
            local_file_path = tmp_dir_path / f'voice{Path(file_info.file_path).suffix}'

            # Download the voice message file using HTTP GET
            file_url = f'https://api.telegram.org/file/bot{self.context.bot.token}/{file_info.file_path}'
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(str(local_file_path), 'wb') as f:
                    f.write(response.content)

            success_message = "Voice processed successfully"
            return True, success_message, local_file_path, amount
        except Exception as e:
            print(f"Error in handle_voice_message: {e}")
            raise

    def handle_video_message(self):
        try:
            # Logic to handle video messages
            video = self.update.message.video
            file = self.context.bot.get_file(video.file_id)
            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent video: "{file.file_path}" {file.file_size}, duration: {video.duration}')

            success, message = ConstraintsChecker.check_video_constraints(file)
            if not success:
                return False, message, None

            # Check if the balance is sufficient
            amount = self.tokenizer.tokens_to_money_from_string(self.update.message.caption)
            amount += self.tokenizer.tokens_to_money_from_video(video.duration)
            if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
                message = "Insufficient balance to process the video message."
                print(message)
                self.context.bot.send_message(self.update.message.chat_id, message)
                return False, message, None

            # Extract file extension
            _, file_extension = os.path.splitext(file.file_path)

            # Determine the project root directory
            project_root = Path(__file__).parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id

            # Ensure the directory exists before trying to download
            os.makedirs(tmp_dir_path, exist_ok=True)

            # Download the file to the desired location with the extracted extension
            download_path = tmp_dir_path / f'video{file_extension}'
            file.download(download_path)

            message = "Video processed successfully"
            return True, message, download_path
        except Exception as e:
            print(f"Error in handle_video_message: {e}")
            raise

    def handle_document_message(self):
        try:
            document = self.update.message.document
            file = self.context.bot.get_file(document.file_id)

            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent document: "{file.file_path}" {file.file_size}')

            success, message = ConstraintsChecker.check_document_constraints(file)
            if not success:
                return False, message, None

            # Extract file extension
            _, file_extension = os.path.splitext(file.file_path)

            # Determine the project root directory
            project_root = Path(__file__).parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id

            # Ensure the directory exists before trying to download
            os.makedirs(tmp_dir_path, exist_ok=True)

            # Download the file to the desired location with the extracted extension
            download_path = tmp_dir_path / f'document{file_extension}'
            file.download(download_path)

            message = "Document processed successfully"
            return True, message, download_path
        except Exception as e:
            raise
