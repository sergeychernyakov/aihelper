from lib.openai.image import Image
from lib.telegram.payment import Payment
from lib.localization import _
from lib.openai.function_handlers.base_function_handler import BaseFunctionHandler

class GenerateImageHandler(BaseFunctionHandler):
    def __init__(self, openai_client, update, context, conversation):
        super().__init__(openai_client, update, context, conversation)

    async def handle(self, tool_call_id: int, args: dict) -> dict:
        # Check if the balance is sufficient
        amount = self.tokenizer.tokens_to_money_from_string(args['description'])
        amount += self.tokenizer.tokens_to_money_to_image()
        if not self.tokenizer.has_sufficient_balance_for_amount(amount, self.conversation.balance):
            message = _("Insufficient balance to process the generating image.")
            print(message)
            await self.context.bot.send_message(self.update.message.chat_id, message)
            payment = Payment()
            await payment.send_invoice(self.update, self.context, False)
            return {
                "tool_call_id": tool_call_id,
                "output": message
            }

        try:
            # Generate the image
            image = Image(self.openai)
            image_url, revised_prompt = image.generate(args['description'])

            # Update the balance
            amount += self.tokenizer.tokens_to_money_from_string(revised_prompt)
            print(f'---->>> Conversation balance decreased by: ${amount} for generating image.')
            self.conversation.balance -= amount

            await self.context.bot.send_photo(self.update.message.chat_id, image_url)
            return {
                "tool_call_id": tool_call_id,
                "output": f'{image_url} - this picture has already been sent to the user in the Telegram chat. There is no need to reply to the message.'
            }
        except Exception as e:
            # Handle content policy violation error
            if 'content_policy_violation' in str(e):
                error_message = _("Your request was rejected due to a content policy violation.")
                print(error_message)
                await self.context.bot.send_message(self.update.message.chat_id, error_message)
                return {
                    "tool_call_id": tool_call_id,
                    "output": error_message
                }
            else:
                raise e
