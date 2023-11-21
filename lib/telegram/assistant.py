
class Assistant:
    def __init__(self, openai_client, assistant_id):
        self.openai = openai_client
        self.assistant_id = assistant_id

    def add_function_to_assistant(self, name, description, instructions, properties=[], required=[]):
        self.openai.beta.assistants.update(
            self.assistant_id,
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

# Example of usage:
# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# from lib.telegram.assistant import Assistant

# load_dotenv()
# openai = OpenAI()
# assistant = Assistant(openai, os.getenv('URT_ASSISTANT_ID'))

# properties = { "description": {"type": "string", "description": "Image description (prompt) for dall-e-3."}}
# assistant.add_function_to_assistant('generateImage', 'Generate image', 'Now you are able to generate image with that function. Use the provided functions to generate image.', properties, ['description'])
