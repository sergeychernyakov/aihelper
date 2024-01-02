import unittest
from unittest.mock import MagicMock
from lib.openai.assistant import Assistant

class TestAssistantClass(unittest.TestCase):
    
    def setUp(self):
        # Mocking the OpenAI's API client
        self.mock_openai_client = MagicMock()
        self.assistant_id = 'test-assistant-id'
        self.assistant = Assistant(self.mock_openai_client, self.assistant_id)

    def test_add_function_to_assistant(self):
        # Test adding a function to the assistant
        self.assistant.add_function_to_assistant(
            'generateImage', 
            'Generate image', 
            'Now you are able to generate an image with that function. Use the provided functions to generate an image.',
            properties={"description": {"type": "string", "description": "Image description (prompt) for dall-e-3."}},
            required=['description']
        )

        # Verify if the openai client was called correctly
        self.mock_openai_client.beta.assistants.update.assert_called_once_with(
            self.assistant_id,
            instructions='Now you are able to generate an image with that function. Use the provided functions to generate an image.',
            model="gpt-4-1106-preview",
            tools=[{
                "type": "function",
                "function": {
                  "name": "generateImage",
                  "description": "Generate image",
                  "parameters": {
                    "type": "object",
                    "properties": {"description": {"type": "string", "description": "Image description (prompt) for dall-e-3."}},
                    "required": ['description']
                  }
                }
            }]
        )

# Add more tests as necessary

if __name__ == '__main__':
    unittest.main()
