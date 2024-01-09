from lib.telegram.message_handlers.base_handler import BaseHandler

class TextHandler(BaseHandler):

    def process_message(self, message: str) -> bool:
        """
        Sends the text message to the OpenAI thread for processing.
        """
        self.openai.beta.threads.messages.create(thread_id=self.thread_id, role="user", content=message)
        return True
