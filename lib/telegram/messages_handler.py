import os
import requests
from pathlib import Path
from lib.constraints_checker import ConstraintsChecker
from lib.openai.tokenizer import Tokenizer
from lib.telegram.payment import Payment
from lib.localization import _

class MessagesHandler:
    def __init__(self, openai_client, update, context, conversation):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.conversation = conversation
        self.thread_id = conversation.thread_id
        self.tokenizer = Tokenizer()
        self.payment = Payment()

    def handle_text_message(self, message):
        try:
            # Process the message
            self.openai.beta.threads.messages.create(thread_id=self.thread_id, role="user", content=message)
            return True, _("Message processed successfully.")
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

            message = _("Image processed successfully")
            return True, message, file
        except Exception as e:
            print(f"Error in handle_photo_message: {e}")
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
                insufficient_balance_message = _("Insufficient balance to process the voice message.")
                print(insufficient_balance_message)
                await self.context.bot.send_message(self.update.message.chat_id, insufficient_balance_message)
                await self.payment.send_invoice(self.update, self.context, False)
                return False, insufficient_balance_message, None, amount

            # Define local file path for the voice message
            project_root = Path(__file__).parent.parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id
            
            os.makedirs(tmp_dir_path, exist_ok=True)
            local_file_path = tmp_dir_path / f'voice{Path(file_info.file_path).suffix}'

            # Download the voice message file using HTTP GET
            response = requests.get(file_info.file_path)
            if response.status_code == 200:
                with open(str(local_file_path), 'wb') as f:
                    f.write(response.content)
            else:
                failed_message = _('Failed to load the voice message')
                print(failed_message)
                return False, failed_message, None, None

            success_message = _("Voice processed successfully")
            return True, success_message, local_file_path, amount
        except Exception as e:
            print(f"Error in handle_voice_message: {e}")
            raise

    async def handle_video_message(self):
        try:
            # Logic to handle video messages
            video = self.update.message.video
            file_info = await self.context.bot.get_file(video.file_id)
            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent video: "{file_info.file_path}" {file_info.file_size}, duration: {video.duration}')

            success, message = ConstraintsChecker.check_video_constraints(file_info)
            if not success:
                return False, message, None

            # Check if the balance is sufficient
            amount = self.tokenizer.tokens_to_money_from_video(video.duration)
            if self.update.message.caption:
                amount += self.tokenizer.tokens_to_money_from_string(self.update.message.caption)

            if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
                message = _("Insufficient balance to process the video message.")
                print(message)
                await self.context.bot.send_message(self.update.message.chat_id, message)
                await self.payment.send_invoice(self.update, self.context, False)
                return False, message, None

            # Define local file path for the video message
            project_root = Path(__file__).parent.parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id
            
            os.makedirs(tmp_dir_path, exist_ok=True)
            local_file_path = tmp_dir_path / f'video{Path(file_info.file_path).suffix}'

            # Download the video message file using HTTP GET
            response = requests.get(file_info.file_path)
            if response.status_code == 200:
                with open(str(local_file_path), 'wb') as f:
                    f.write(response.content)
            else:
                failed_message = _('Failed to load the video message')
                print(failed_message)
                return False, failed_message, None

            success_message = _("Video processed successfully")
            return True, success_message, local_file_path
        except Exception as e:
            print(f"Error in handle_video_message: {e}")
            raise

    async def handle_document_message(self):
        try:
            document = self.update.message.document
            file_info = await self.context.bot.get_file(document.file_id)

            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent document: "{file_info.file_path}" {file_info.file_size}')

            success, message = ConstraintsChecker.check_document_constraints(file_info)
            if not success:
                return False, message, None

            # Define local file path for the document
            project_root = Path(__file__).parent.parent.parent.parent
            tmp_dir_path = project_root / 'tmp' / self.thread_id
            
            os.makedirs(tmp_dir_path, exist_ok=True)
            local_file_path = tmp_dir_path / f'document{Path(file_info.file_path).suffix}'

            # Download the document file using HTTP GET
            response = requests.get(file_info.file_path)
            if response.status_code == 200:
                with open(str(local_file_path), 'wb') as f:
                    f.write(response.content)
            else:
                failed_message = _('Failed to load the document')
                print(failed_message)
                return False, failed_message, None

            return True, _("Document processed successfully"), local_file_path
        except Exception as e:
            print(f"Error in handle_document_message: {e}")
            raise
