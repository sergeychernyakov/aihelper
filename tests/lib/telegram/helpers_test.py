import unittest
import tempfile
import os
from lib.telegram.helpers import Helpers
from io import StringIO
import sys

class TestHelpers(unittest.TestCase):

    def test_cleanup_folder_existing(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Verify the directory exists
            self.assertTrue(os.path.exists(temp_dir))

            # Call the method to cleanup folder
            Helpers.cleanup_folder(temp_dir)

            # Check the directory no longer exists
            self.assertFalse(os.path.exists(temp_dir))

    def test_cleanup_folder_non_existing(self):
        # Create a temporary directory and immediately delete it
        temp_dir = tempfile.mkdtemp()
        os.rmdir(temp_dir)

        # Redirect the standard output
        capturedOutput = StringIO()
        sys.stdout = capturedOutput

        # Call the method
        Helpers.cleanup_folder(temp_dir)

        # Reset the redirection
        sys.stdout = sys.__stdout__

        # Check if the expected message is in the output
        self.assertIn(f'The directory {temp_dir} does not exist!', capturedOutput.getvalue())

if __name__ == '__main__':
    unittest.main()
