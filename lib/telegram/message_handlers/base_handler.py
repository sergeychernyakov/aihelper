from lib.openai.tokenizer import Tokenizer
from lib.telegram.payment import Payment
from lib.telegram.new_transcriptor import NewTranscriptor
from lib.openai.assistant import Assistant
from lib.telegram.answer import Answer
from lib.constraints_checker import ConstraintsChecker
from decimal import Decimal
import os
import requests
from io import BytesIO
from pathlib import Path

class BaseHandler:

    MESSAGE_TYPE = 'photo'

    def __init__(self, openai_client, update, context, conversation):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.conversation = conversation
        self.thread_id = conversation.thread_id
        self.tokenizer = Tokenizer()
        self.payment = Payment()
        self.transcriptor = NewTranscriptor(self.openai)
        self.assistant = Assistant()
        self.answer = Answer(openai_client, context, update.message.chat_id, self.thread_id)

    async def _send_chat_message(self, content):
        """
        Send a message to the Telegram chat.

        :param content: The content of the message to be sent.
        """
        await self.answer.answer_with_text(content)
        
    def _create_openai_thread_message(self, content, file_ids=None):
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

    def _create_openai_non_thread_message(self, content):
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
            return _("Error: Unable to process the request."), 0

    async def _check_constraints(self, file_info, *args) -> bool:
        """
        Check if the content meets the defined constraints based on its type.

        :param file_info: File information object.
        :param args: Additional arguments to be passed to the check method.
        :return: Boolean indicating if the content meets the constraints.
        """
        # Dynamically get the correct constraint check method based on MESSAGE_TYPE
        check_method = getattr(ConstraintsChecker, f'check_{self.MESSAGE_TYPE}_constraints')

        # Call the method with unpacked arguments
        success, message = check_method(file_info, *args)

        if not success:
            await self.context.bot.send_message(self.update.message.chat_id, message)
        return success

    async def _check_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if there is sufficient balance to process.
        
        :param amount: The amount.
        :return: Boolean indicating if there is sufficient balance.
        """
        if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
            message = _(f"Insufficient balance to process the {self.MESSAGE_TYPE}.")
            print(message)
            await self._send_chat_message(message)
            await self.payment.send_invoice(self.update, self.context, False)
            return False

        return True

    async def _download_file(self, file_path: str) -> str:
        """Download the file from the given URL."""
        project_root = Path(__file__).parent.parent.parent.parent
        tmp_dir_path = project_root / 'tmp' / self.thread_id
        os.makedirs(tmp_dir_path, exist_ok=True)
        file_extension = Path(file_path).suffix
        local_file_path = tmp_dir_path / f'{self.MESSAGE_TYPE}{file_extension}'

        response = requests.get(file_path)
        if response.status_code == 200:
            with open(str(local_file_path), 'wb') as f:
                f.write(response.content)
            return str(local_file_path)
        else:
            print(_(f'Failed to download the {self.MESSAGE_TYPE}'))
            return ""

    def _download_file_to_stream(self, file_url: str) -> BytesIO:
        """Download the file and return a BytesIO object."""
        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                # Read content into BytesIO
                file_stream = BytesIO(response.content)
                file_stream.seek(0)  # Move to the beginning of the file-like object
                return file_stream
            else:
                print(f"Failed to download {self.MESSAGE_TYPE}: HTTP Status {response.status_code}")
                return BytesIO()  # Return an empty BytesIO object
        except Exception as e:
            print(f"Exception occurred during file download: {e}")
            return BytesIO()  # Return an empty BytesIO object

    def _log_user_interaction(self, file):
        user_info = f'{self.update.message.from_user.first_name}({self.update.message.from_user.username})'
        file_info = f'"{file.file_path}" size: {file.file_size} bytes'
        additional_info = ""

        if self.MESSAGE_TYPE == 'photo' and hasattr(self.update.message, 'photo'):
            photo = self.update.message.photo[-2]  # Assuming the last photo in the array is the one you want to log
            additional_info = f', dimensions: {photo.width}x{photo.height}'
        elif self.MESSAGE_TYPE == 'voice' and hasattr(self.update.message, 'voice'):
            voice = self.update.message.voice
            additional_info = f', duration: {voice.duration}s'
        elif self.MESSAGE_TYPE == 'video' and hasattr(self.update.message, 'video'):
            video = self.update.message.video
            additional_info = f', duration: {video.duration}s'
        elif self.MESSAGE_TYPE == 'document' and hasattr(self.update.message, 'document'):
            document = self.update.message.document
            additional_info = f', file name: "{document.file_name}"'

        caption = f', caption: "{self.update.message.caption}"' if self.update.message.caption else ""
        log_message = f'{user_info} sent {self.MESSAGE_TYPE}: {file_info}{additional_info}{caption}'
        print(log_message)

    def _update_balance(self, total_tokens: int, amount: Decimal = 0):
        """Update the user's balance based on the number of tokens processed.
        
        :param total_tokens: The number of tokens used in the transcription process.
        """
        amount += self.tokenizer.tokens_to_money(total_tokens)
        print(f'---->>> Conversation balance decreased by: ${amount} for {self.MESSAGE_TYPE} processing.')
        self.conversation.balance -= amount

    def handle_message(self, *args) -> bool:
        try:
            return self.process_message(*args)
        except Exception as e:
            print(f"Error in handle_message: {e}")
            raise
