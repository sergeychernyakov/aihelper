import time
import random
import json
from lib.telegram.answer import Answer
from lib.telegram.helpers import Helpers
from db.models.conversation import Conversation
from lib.telegram.image import Image
from lib.telegram.email_sender import EmailSender

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

            if run.status == 'requires_action':
                self.submit_tool_outputs(run)

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
        return run.id

    def create_thread(self, session, conversation):
        thread = self.openai.beta.threads.create()
        session.query(Conversation).filter_by(id=conversation.id).update({"thread_id": thread.id})
        session.commit()

    def recreate_thread(self, session, conversation):
        self.openai.beta.threads.delete(conversation.thread_id)
        self.create_thread(session, conversation)

    def cancel_run(self, thread_id, run_id):
        # Check if both thread_id and run_id are present and not None
        if thread_id and run_id:
            try:
                # Attempt to cancel the run
                run = self.openai.beta.threads.runs.cancel(
                    thread_id=thread_id,
                    run_id=run_id
                )
                # Add any additional logic here if needed, e.g., logging the cancellation
            except Exception as e:
                # Handle exceptions, e.g., log an error message
                print(f"Error occurred while cancelling the run: {e}")
        else:
            # Handle the case where thread_id or run_id is missing
            print("Cannot cancel run: Missing thread_id or run_id.")

    def submit_tool_outputs(self, run):
        tool_outputs = []

        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            tool_call_id = tool_call.id  # Access the id attribute
            function_name = tool_call.function.name  # Access the function name attribute
            arguments = tool_call.function.arguments  # Access the arguments attribute

            # Parse arguments if it's a JSON string
            args = json.loads(arguments)
            # Handle different function calls
            if function_name == 'generateImage':
                output = self._generate_image(tool_call_id, args)
            elif function_name == 'sendEmail':
                output = self._send_email(tool_call_id, args)
            else:
                # Handle other function calls or throw an error
                output = {
                    "tool_call_id": tool_call_id,
                    "output": '',
                }

            tool_outputs.append(output)

        # Submit tool outputs back to the OpenAI API
        self.openai.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

    # private

    def _send_email(self, tool_call_id, args):
        sender = EmailSender(self.openai)
        attachment = 'attachment'
        sender.send_email(args['email'], args['text'], attachment)
        return {
            "tool_call_id": tool_call_id,
            "output": f'Письмо спешно отправлено.'
        }

    def _generate_image(self, tool_call_id, args):
        # Assuming Image class has a generateImage method
        image = Image(self.openai)
        image_url, revised_prompt = image.generate(args['description'])  # Pass the description argument
        
        self.context.bot.send_photo(self.update.message.chat_id, image_url) # in some cases AI answers with wrong image url without params
        return {
            "tool_call_id": tool_call_id,
            "output": f'{image_url} - эта картинка уже отправлена пользователю в чат в телеграме. Переведите на украинский: {revised_prompt}.'
        }