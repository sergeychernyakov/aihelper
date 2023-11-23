import unittest
from unittest.mock import MagicMock
from lib.telegram.image import Image

class TestImageClass(unittest.TestCase):
    
    def setUp(self):
        # Mocking OpenAI's API client
        self.mock_openai = MagicMock()
        self.image = Image(self.mock_openai)

    def test_initialization(self):
        self.assertIsNotNone(self.image)
        self.assertEqual(self.image.openai, self.mock_openai)

    def test_successful_generate(self):
        # Mocking a successful response
        self.mock_openai.images.generate.return_value = MagicMock(
            data=[MagicMock(url='http://example.com/image.png', revised_prompt='Generated Image Description')]
        )
        url, revised_prompt = self.image.generate('test description')
        self.assertEqual(url, 'http://example.com/image.png')
        self.assertEqual(revised_prompt, 'Generated Image Description')

    def test_generate_no_image(self):
        # Mocking a response with no image
        self.mock_openai.images.generate.return_value = MagicMock(data=[])
        url, revised_prompt = self.image.generate('test description')
        self.assertEqual(url, 'No image generated')
        self.assertEqual(revised_prompt, '')

    def test_generate_exception(self):
        # Mocking an exception
        self.mock_openai.images.generate.side_effect = Exception("Test Exception")
        response, revised_prompt = self.image.generate('test description')
        self.assertTrue("Error in generating image: Test Exception" in response)
        self.assertEqual(revised_prompt, '')

# Add more tests as necessary

if __name__ == '__main__':
    unittest.main()
