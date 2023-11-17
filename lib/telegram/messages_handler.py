import os
from lib.telegram.constraints_checker import ConstraintsChecker

class MessagesHandler:
    def __init__(self, openai_client, update, context, thread_id):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.thread_id = thread_id

    ######### Handlers for different types of messages #########
    def handle_text_message(self, message):
        try:
            # Logic to handle text messages and execute OpenAI API calls
            self.openai.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=message
            )

            return True  # Return True on successful execution
        except Exception as e:
            raise

    def handle_photo_message(self):
        try:
            # take the photo near to 512x512px for vision low res mode
            photo = self.update.message.photo[-2]
            file = self.context.bot.get_file(photo.file_id)
            print(f"Function - Mock File ID: {id(file)}, Mock Photo ID: {id(photo)}")

            # fix check_file_constraints
            success, message = ConstraintsChecker.check_photo_constraints(file, photo)
            if not success:
                return False, message, None

            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent image: "{file.file_path}" {file.file_size} {photo.width}x{photo.height} "{self.update.message.caption}"')

            message = "Image processed successfully"
            return True, message, file
        except Exception as e:
            raise

    def handle_voice_message(self):
        try:
            # Logic to handle voice messages and execute OpenAI API calls
            voice = self.update.message.voice
            file = self.context.bot.get_file(voice.file_id)

            print(f'{self.update.message.from_user.first_name}({self.update.message.from_user.username}) sent voice: "{file.file_path}" {file.file_size}')

            success, message = ConstraintsChecker.check_voice_constraints(file)
            if not success:
                return False, message, None

            # Extract file extension
            _, file_extension = os.path.splitext(file.file_path)

            # Ensure the directory exists before trying to download
            download_dir_path = f'tmp/{self.thread_id}'
            os.makedirs(download_dir_path, exist_ok=True)

            # Download the file to the desired location with the extracted extension
            download_path = f'{download_dir_path}/voice{file_extension}'
            file.download(download_path)

            message = "Voice processed successfully"
            return True, message, download_path
        except Exception as e:
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

            # Ensure the directory exists before trying to download
            download_dir_path = f'tmp/{self.thread_id}'
            os.makedirs(download_dir_path, exist_ok=True)

            # Download the file to the desired location with the extracted extension
            download_path = f'{download_dir_path}/document{file_extension}'
            file.download(download_path)

            message = "Voice processed successfully"
            return True, message, download_path
        except Exception as e:
            raise
