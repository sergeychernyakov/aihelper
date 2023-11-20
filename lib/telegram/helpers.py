import os
import shutil

class Helpers:

    @classmethod
    def cleanup_folder(cls, dir_path):
        # Check if the directory exists
        if os.path.exists(dir_path):
            # Delete directory and all its contents
            shutil.rmtree(dir_path)
        else:
            print(f'The directory {dir_path} does not exist!')
