import os
import shutil
import re

class Helpers:

    @classmethod
    def cleanup_folder(cls, dir_path):
        # Check if the directory exists
        if os.path.exists(dir_path):
            # Delete directory and all its contents
            shutil.rmtree(dir_path)
        else:
            print(f'The directory {dir_path} does not exist!')

    @classmethod
    def get_thread_id_and_run_id_from_string(cls, string):
        pattern = r"(thread_[a-zA-Z0-9]+).*(run_[a-zA-Z0-9]+)"
        match = re.search(pattern, string)
        if match:
            thread_id = match.group(1)
            run_id = match.group(2)
            return thread_id, run_id
        else:
            return None, None
