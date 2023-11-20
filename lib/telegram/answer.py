import os
from pathlib import Path

class Answer:
    def __init__(self, openai_client, context, chat_id, thread_id):
        self.openai = openai_client
        self.context = context
        self.chat_id = chat_id
        self.thread_id = thread_id

    def answer_with_text(self, message):
        self.context.bot.send_message(self.chat_id, message)

    def answer_with_voice(self, message):
        voice_answer_folder = Path(__file__).parent / 'tmp' / self.thread_id
        voice_answer_path = voice_answer_folder / "voice_answer.mp3"

        os.makedirs(voice_answer_folder, exist_ok=True)

        response = self.openai.audio.speech.create(
            model="tts-1", # tts-1-hd
            voice="nova",
            input=message
        )

        response.stream_to_file(voice_answer_path)

        voice_file = open(voice_answer_path, "rb")
        return self.context.bot.send_document(self.chat_id, voice_file)
