import unittest
from unittest import mock
from main import check_file_constraints, handle_text_message, create_conversation
from unittest.mock import Mock

def create_mock_file_and_photo(file_extension=".jpg", file_size=1024, width=1000, height=1000):
    mock_file = Mock()
    mock_file.file_path = f"test{file_extension}"
    mock_file.file_size = file_size

    mock_photo = Mock()
    mock_photo.width = width
    mock_photo.height = height

    return mock_file, mock_photo

def create_mock_update(text="Test message", user_id=12345, first_name="Test", username="testuser"):
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = text
    mock_update.message.from_user = Mock()
    mock_update.message.from_user.id = user_id
    mock_update.message.from_user.first_name = first_name
    mock_update.message.from_user.username = username

    return mock_update

class TestTelegramBotFunctions(unittest.TestCase):

    def test_check_file_constraints(self):
        # Assuming you have a way to create a mock 'file' and 'photo' object
        mock_file, mock_photo = create_mock_file_and_photo()  # You need to define this helper function

        # Test for a valid file
        success, message = check_file_constraints(mock_file, mock_photo)
        self.assertTrue(success)
        self.assertEqual(message, "")

        # Test for an invalid file type
        mock_file_invalid, _ = create_mock_file_and_photo(file_extension=".txt")
        success, message = check_file_constraints(mock_file_invalid, mock_photo)
        self.assertFalse(success)
        self.assertEqual(message, "Unsupported file type.")

    @mock.patch('main.openai')
    def test_handle_text_message(self, mock_openai):
        # Create a mock update and thread_id
        mock_update = create_mock_update()
        mock_thread_id = "12345"
        handle_text_message(mock_update, mock_thread_id)
        mock_openai.beta.threads.messages.create.assert_called_with(
            thread_id=mock_thread_id,
            role="user",
            content=mock_update.message.text
        )

        # Assert if successful_interaction is set to True
        self.assertTrue(successful_interaction)


    @mock.patch('main.SessionLocal')
    def test_create_conversation(self, mock_session):
        # Create a mock update
        mock_update = create_mock_update()  # You need to define this helper function

        # Call the function
        conversation = create_conversation(mock_session, mock_update)

        # Assert if conversation has correct attributes
        self.assertEqual(conversation.user_id, mock_update.message.from_user.id)
        self.assertEqual(conversation.language_code, mock_update.message.from_user.language_code)
        # ... other assertions ...


if __name__ == '__main__':
    unittest.main()
