

import time
import random
from lib.telegram.answer import Answer
from lib.telegram.helpers import Helpers
from db.models.conversation import Conversation

class RunsTreadsHandler:
    def __init__(self, openai_client, update, context, thread_id, assistant_id):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.thread_id = thread_id
        self.assistant_id = assistant_id
        self.answer = Answer(openai_client, context, update.message.chat_id, thread_id)

    ######## Work with OpenAI threads, runs #########   class RunsTreadsHandler
    def create_run(self):
        run = self.openai.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )

        while run.status !="completed":
            time.sleep(2)
            run = self.openai.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
            )

        messages = self.openai.beta.threads.messages.list(
            thread_id=self.thread_id
        )
        response_text = messages.data[0].content[0].text.value
        print(f'AI responded: {response_text}')

        # Define a threshold for a short message, e.g., 100 characters
        short_message_threshold = 100
        # Randomly choose to respond with voice 1 out of 10 times
        if len(response_text) <= short_message_threshold and random.randint(1, 10) == 1:
            self.answer.answer_with_voice(response_text)
        else:
            self.answer.answer_with_text(response_text)

        Helpers.cleanup_folder(f'tmp/{self.thread_id}')

    def create_thread(self, session, conversation):
        thread = self.openai.beta.threads.create()
        session.query(Conversation).filter_by(id=conversation.id).update({"thread_id": thread.id})
        session.commit()

    def recreate_thread(self, session, conversation):
        self.openai.beta.threads.delete(conversation.thread_id)
        self.create_thread(session, conversation)
