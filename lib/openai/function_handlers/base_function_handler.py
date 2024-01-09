class BaseFunctionHandler:
    def __init__(self, openai_client, update, context, conversation):
        self.openai = openai_client
        self.update = update
        self.context = context
        self.conversation = conversation

    async def handle(self, tool_call_id, args):
        """
        Handle the tool call.
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
