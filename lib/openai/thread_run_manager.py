import time
import json
import asyncio
import inflection
import random
from lib.telegram.answer import Answer
from db.models.conversation import Conversation
from lib.openai.image import Image
from lib.email_sender import EmailSender
from lib.openai.tokenizer import Tokenizer
from datetime import timedelta
from decimal import Decimal
from lib.telegram.payment import Payment
from lib.localization import _
import lib.openai.function_handlers.base_function_handler as fh_base

class ThreadRunManager:
    MAX_RUN_DURATION = 3600  # 60 minutes

    def __init__(self, openai_client, update, context, conversation, session, chat_id):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.session = session
        self.conversation = conversation
        self.thread_id = conversation.thread_id
        self.assistant_id = conversation.assistant_id
        self.answer = Answer(openai_client, context, chat_id, self.thread_id)
        self.tokenizer = Tokenizer()
        self.thread_recreation_interval = timedelta(hours=1)
        self.payment = Payment()

    # Run handling

    async def manage_run(self):
        run_id = await self.create_run()
        await self.process_run(run_id)

    async def create_run(self):
        run = self.openai.beta.threads.runs.create(
            thread_id=self.thread_id, assistant_id=self.assistant_id)
        return run.id

    async def process_run(self, run_id):
        start_time = time.time()
        run = await self.wait_for_run_completion(run_id, start_time)
        if run:
            await self.handle_run_response(run)

    def cancel_run(self, thread_id, run_id):
        if not thread_id or not run_id:
            print("Failed to cancel run with invalid IDs.")
            return

        try:
            self.openai.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        except Exception as e:
            print(f"Error occurred while cancelling the run: {e}")

    # Thread handling

    def create_thread(self, session, conversation):
        thread = self.openai.beta.threads.create()
        self.thread_id = thread.id
        conversation.thread_id = thread.id
        session.query(Conversation).filter_by(id=conversation.id).update({"thread_id": thread.id})
        session.commit()

    def recreate_thread(self, session, conversation):
        self.openai.beta.threads.delete(conversation.thread_id)
        self.create_thread(session, conversation)

    async def wait_for_run_completion(self, run_id, start_time):
        while time.time() - start_time < self.MAX_RUN_DURATION:
            run = self.openai.beta.threads.runs.retrieve(
                thread_id=self.thread_id, run_id=run_id)
            if run.status == "completed":
                return run
            elif run.status == 'requires_action':
                await self.submit_tool_outputs(run)
            await asyncio.sleep(3)
        self.cancel_run(self.thread_id, run_id)
        return None

    async def handle_run_response(self, run):
        messages = self.openai.beta.threads.messages.list(thread_id=self.thread_id)
        for content in messages.data[0].content:
            if content.type == 'text':
                await self._process_text_content(content)
            elif content.type == 'image_file':
                await self._process_image_content(content)

    async def _process_text_content(self, content):
        """
        Process text content from the OpenAI thread message.
        Decrease the conversation balance based on text length and sends the response back to the user.

        :param content: Content object containing text details.
        """
        response_text = content.text.value
        print(f'AI responded: {response_text}')

        # Decrease balance for the output text
        amount = self.tokenizer.tokens_to_money_from_string(response_text, "output")
        print(f'---->>> Conversation balance decreased by: {amount} for output text')
        self.conversation.balance -= amount

        # Define a threshold for a short message
        short_message_threshold = 100
        if len(response_text) <= short_message_threshold and random.randint(1, 10) == 1:
            await self.answer.answer_with_voice(response_text)

            # Update the balance for output voice
            amount = self.tokenizer.tokens_to_money_to_voice(response_text)
            print(f'---->>> Conversation balance decreased by: {amount} for output voice')
            self.conversation.balance -= amount
        else:
            await self.answer.answer_with_text(response_text)

        # Check for annotations and send document if present
        if 'annotations' in content.text:
            annotation_data = content.text.annotations[0]
            await self.answer.answer_with_annotation(annotation_data)

            # Decrease balance for output document
            amount = Decimal(0.001)
            print(f'---->>> Conversation balance decreased by: {amount} for document generated by AI.')
            self.conversation.balance -= amount

    async def _process_image_content(self, content):
        """
        Process image content from the OpenAI thread message.
        Decrease the conversation balance for the image and send the image back to the user.

        :param content: Content object containing image file details.
        """
        file_id = content.image_file.file_id
        await self.answer.answer_with_image(file_id)

        # Decrease balance for the output image
        amount = self.tokenizer.tokens_to_money_to_image()
        print(f'---->>> Conversation balance decreased by: {amount} for image generated by AI.')
        self.conversation.balance -= amount

    def _default_tool_function(self, tool_call_id, args):
        """
        Default function to handle unknown tool calls.

        :param tool_call_id: Identifier for the tool call.
        :param args: Arguments for the tool call.
        :return: A dictionary indicating an empty output for unknown tool calls.
        """
        return {
            "tool_call_id": tool_call_id,
            "output": ''
        }

    async def _handle_tool_call(self, tool_call):
        function_name = tool_call.function.name

        # Ensure function_name is a string
        if not isinstance(function_name, str):
            raise TypeError(f"Expected function_name to be a string, got {type(function_name)}")

        args = json.loads(tool_call.function.arguments)

        # Convert function name from camel case to snake case for the module
        module_name = inflection.underscore(function_name) + '_handler'  # Append '_handler'

        # Convert function name to handler class name (e.g., "generate_image" -> "GenerateImageHandler")
        handler_class_name = inflection.camelize(function_name) + 'Handler'

        try:
            # Dynamically import the handler class
            module = __import__(f'lib.openai.function_handlers.{module_name}', fromlist=[handler_class_name])
            handler_class = getattr(module, handler_class_name, fh_base.BaseFunctionHandler)

            # Instantiate the handler class
            handler = handler_class(self.openai, self.update, self.context, self.conversation)
            return await handler.handle(tool_call.id, args)
        except ModuleNotFoundError as e:
            print(f"Module not found: {e}")
            # Handle the error or return a default response

    async def submit_tool_outputs(self, run):
        tool_outputs = []
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            output = await self._handle_tool_call(tool_call)
            tool_outputs.append(output)

        self.openai.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
