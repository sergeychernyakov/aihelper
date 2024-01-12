from lib.email_sender import EmailSender
from lib.localization import _
from lib.openai.function_handlers.base_function_handler import BaseFunctionHandler

class SendEmailHandler(BaseFunctionHandler):
    def __init__(self, openai_client, update, context, conversation):
        super().__init__(openai_client, update, context, conversation)

    async def handle(self, tool_call_id, args):
        # Logic to send an email based on provided arguments
        sender = EmailSender()  # Assuming EmailSender does not need openai_client
        sender.send_email(args['email'], args['text'], args.get('attachment'))
        await self.context.bot.send_message(self.update.message.chat_id, _('Letter successfully sent.'))
        return {
            "tool_call_id": tool_call_id,
            "output": _('Letter successfully sent. There is no need to reply to the message.')
        }
