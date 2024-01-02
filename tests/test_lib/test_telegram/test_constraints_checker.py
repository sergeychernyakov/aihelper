import unittest
from lib.telegram.constraints_checker import ConstraintsChecker
from lib.localization import Localization

class MockFile:
    def __init__(self, file_path, file_size, width=None, height=None):
        self.file_path = file_path
        self.file_size = file_size
        self.width = width
        self.height = height

class TestConstraintsChecker(unittest.TestCase):

    def setUp(self):
        Localization._translator = None

    ### check_photo_constraints
    def test_photo_extension_valid(self):
        file = MockFile(file_path="image.jpg", file_size=1024, width=1000, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertTrue(result)

    def test_photo_extension_invalid(self):
        file = MockFile(file_path="image.bmp", file_size=1024, width=1000, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertFalse(result)
        self.assertIn("Unsupported file type", message)

    def test_photo_size_valid(self):
        file = MockFile(file_path="image.jpg", file_size=1024, width=1000, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertTrue(result)

    def test_photo_size_exceeding(self):
        file = MockFile(file_path="image.jpg", file_size=ConstraintsChecker.MAX_FILE_SIZE + 1, width=1000, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertFalse(result)
        self.assertIn("The file size is too large", message)

    def test_photo_dimension_valid(self):
        file = MockFile(file_path="image.jpg", file_size=1024, width=1000, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertTrue(result)

    def test_photo_dimension_exceeding(self):
        file = MockFile(file_path="image.jpg", file_size=1024, width=ConstraintsChecker.MAX_DIMENSION_SIZE + 1, height=1000)
        result, message = ConstraintsChecker.check_photo_constraints(file, file)
        self.assertFalse(result)
        self.assertIn("Image dimensions are too large", message)

    ### check_voice_constraints
    def test_voice_extension_valid(self):
        file = MockFile(file_path="audio.mp3", file_size=1024)
        result, message = ConstraintsChecker.check_voice_constraints(file)
        self.assertTrue(result)

    def test_voice_extension_invalid(self):
        file = MockFile(file_path="audio.flac", file_size=1024)
        result, message = ConstraintsChecker.check_voice_constraints(file)
        self.assertFalse(result)
        self.assertIn("Unsupported file type", message)

    def test_voice_size_valid(self):
        file = MockFile(file_path="audio.mp3", file_size=1024)
        result, message = ConstraintsChecker.check_voice_constraints(file)
        self.assertTrue(result)

    def test_voice_size_exceeding(self):
        file = MockFile(file_path="audio.mp3", file_size=ConstraintsChecker.MAX_FILE_SIZE + 1)
        result, message = ConstraintsChecker.check_voice_constraints(file)
        self.assertFalse(result)
        self.assertIn("The file size is too large", message)

    ### check_document_constraints
    def test_document_extension_valid(self):
        file = MockFile(file_path="document.pdf", file_size=1024)
        result, message = ConstraintsChecker.check_document_constraints(file)
        self.assertTrue(result)

    def test_document_extension_invalid(self):
        file = MockFile(file_path="document.xyz", file_size=1024)
        result, message = ConstraintsChecker.check_document_constraints(file)
        self.assertFalse(result)
        self.assertIn("Unsupported file type", message)

    def test_document_size_valid(self):
        file = MockFile(file_path="document.pdf", file_size=1024)
        result, message = ConstraintsChecker.check_document_constraints(file)
        self.assertTrue(result)

    def test_document_size_exceeding(self):
        file = MockFile(file_path="document.pdf", file_size=ConstraintsChecker.MAX_FILE_SIZE + 1)
        result, message = ConstraintsChecker.check_document_constraints(file)
        self.assertFalse(result)
        self.assertIn("The file size is too large", message)

    def test_video_extension_valid(self):
        file = MockFile(file_path="video.mp4", file_size=1024)
        result, message = ConstraintsChecker.check_video_constraints(file)
        self.assertTrue(result)

    def test_video_extension_invalid(self):
        file = MockFile(file_path="video.mkv", file_size=1024)
        result, message = ConstraintsChecker.check_video_constraints(file)
        self.assertFalse(result)
        self.assertIn("Unsupported file type", message)

    def test_video_size_valid(self):
        file = MockFile(file_path="video.mp4", file_size=1024)
        result, message = ConstraintsChecker.check_video_constraints(file)
        self.assertTrue(result)

    def test_video_size_exceeding(self):
        file = MockFile(file_path="video.mp4", file_size=ConstraintsChecker.MAX_VIDEO_FILE_SIZE + 1)
        result, message = ConstraintsChecker.check_video_constraints(file)
        self.assertFalse(result)
        self.assertIn("The video file size is too large", message)

if __name__ == '__main__':
    unittest.main()
