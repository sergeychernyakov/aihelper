class Transcriptor:
    def __init__(self, openai_client, update, context, thread_id, assistant_id):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.thread_id = thread_id
        self.assistant_id = assistant_id

    def transcript_document(self, file_path):
        try:
            caption = self.update.message.caption or "Что в этом файле? Если в файле есть текст, переведи его на украинский язык."
            file = self.openai.files.create(
                file=open(file_path, "rb"),
                purpose='assistants'
            )
            self.openai.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=caption,
                file_ids=[file.id]
            )
            return True, 'File sent for transcription'
        except Exception as e:
            raise

    def transcript_image(self, file):
        try:
            caption = self.update.message.caption or "Что на этой картинке? Если на картинке есть текст - выведи его."
            response = self.openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": caption}, {"type": "image_url", "image_url": {"url": file.file_path, "detail": "low"}}]}
                ],
                max_tokens=100
            )
            self.context.bot.send_message(
                self.update.message.chat_id,
                response.choices[0].message.content
            )
        except Exception as e:
            raise

    def transcript_voice(self, file_path):
        try:
            audio_file = open(file_path, "rb")
            transcription = self.openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            self.context.bot.send_message(
                self.update.message.chat_id,
                transcription
            )
        except Exception as e:
            raise
