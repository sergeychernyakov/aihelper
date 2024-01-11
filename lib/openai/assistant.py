import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Assistant:
    
    ASSISTANT_ID = None

    def __init__(self, openai_client=None):
        """
        Initializes the Assistant class with an OpenAI client and an assistant ID.
        If not provided, it initializes the OpenAI client and fetches the assistant ID from environment variables.
        """
        self.openai = openai_client if openai_client else OpenAI()

        if not self.ASSISTANT_ID:
            raise ValueError("Assistant ID is not provided and not found in environment variables.")

    def get_openai_client(self):
        """
        Returns the OpenAI client instance.
        """
        return self.openai

    def add_function_to_assistant(self, name, description, instructions, properties=[], required=[]):
        """
        Adds a function to the assistant with the specified details.
        """
        self.openai.beta.assistants.update(
            self.ASSISTANT_ID,
            instructions=instructions,
            model="gpt-4-1106-preview",
            tools=[{
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }]
        )

    def prompt(self):
        """
        Retrieves the current assistant's instructions.
        """
        assistant_details = self.openai.beta.assistants.retrieve(self.ASSISTANT_ID)
        if hasattr(assistant_details, 'instructions'):
            return assistant_details.instructions
        else:
            raise AttributeError("Assistant object does not have 'instructions' attribute")


# Example of usage:
# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# from lib.telegram.assistant import Assistant

# load_dotenv()
# openai = OpenAI()
# assistant = Assistant()

# properties = { "description": {"type": "string", "description": "Image description (prompt) for dall-e-3."}}
# assistant.add_function_to_assistant('generateImage', 'Generate image', 'Now you are able to generate image with that function. Use the provided functions to generate image.', properties, ['description'])
