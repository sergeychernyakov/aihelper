import unittest
from unittest.mock import MagicMock
from lib.openai.assistant import Assistant

class TestAssistantClass(unittest.TestCase):
    
    def setUp(self):
        # Mocking the OpenAI's API client
        self.mock_openai_client = MagicMock()

    def test_raise_error_without_assistant_id(self):
        # Temporarily remove ASSISTANT_ID if set
        original_id = Assistant.ASSISTANT_ID
        Assistant.ASSISTANT_ID = None

        # Test that ValueError is raised
        with self.assertRaises(ValueError) as context:
            Assistant(self.mock_openai_client)

        # Verify the error message
        self.assertEqual(str(context.exception), "Assistant ID is not provided and not found in environment variables.")

        # Restore original ASSISTANT_ID after the test
        Assistant.ASSISTANT_ID = original_id

    def test_add_function_to_assistant(self):
        # Set ASSISTANT_ID for testing
        Assistant.ASSISTANT_ID = 'test-assistant-id'

        # Initialize Assistant instance
        self.assistant = Assistant(self.mock_openai_client)
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
            'test-assistant-id',
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
