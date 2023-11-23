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

        # Verify the directory no longer exists
        self.assertFalse(os.path.exists(temp_dir))

        # Call the method on the non-existing directory
        Helpers.cleanup_folder(temp_dir)

        # Check the directory still does not exist (assertion remains the same as the folder is already deleted)
        self.assertFalse(os.path.exists(temp_dir))

if __name__ == '__main__':
    unittest.main()
