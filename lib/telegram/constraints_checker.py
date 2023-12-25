import os

class ConstraintsChecker:
    MAX_FILE_SIZE = 5.0 * 1024 * 1024  # 5 MB in bytes
    ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    ALLOWED_VOICE_EXTENSIONS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.oga'} 
    ALLOWED_FILE_EXTENSIONS = {'.txt', '.tex', '.docx', '.doc', '.html', '.rtf', '.rtfd', '.pdf', '.pptx', '.txt', '.tar', '.zip'}
    MAX_DIMENSION_SIZE = 2000  # Max pixels for the longest side of the photo

    # New allowed video extensions and max file size
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv'}
    MAX_VIDEO_FILE_SIZE = 20.0 * 1024 * 1024  # 10 MB in bytes

    @classmethod
    def check_photo_constraints(cls, file, photo):
        extension_check = cls._check_file_extension(os.path.splitext(file.file_path)[1].lower(), cls.ALLOWED_PHOTO_EXTENSIONS)
        if not extension_check[0]:
            return extension_check

        size_check = cls._check_file_size(file.file_size)
        if not size_check[0]:
            return size_check

        if photo.width > cls.MAX_DIMENSION_SIZE or photo.height > cls.MAX_DIMENSION_SIZE:
            return False, "Image dimensions are too large."
        return True, ""

    @classmethod
    def check_voice_constraints(cls, file):
        extension_check = cls._check_file_extension(os.path.splitext(file.file_path)[1].lower(), cls.ALLOWED_VOICE_EXTENSIONS)
        if not extension_check[0]:
            return extension_check

        return cls._check_file_size(file.file_size)

    @classmethod
    def check_document_constraints(cls, file):
        extension_check = cls._check_file_extension(os.path.splitext(file.file_path)[1].lower(), cls.ALLOWED_FILE_EXTENSIONS)
        if not extension_check[0]:
            return extension_check

        return cls._check_file_size(file.file_size)

   # New method for checking video constraints
    @classmethod
    def check_video_constraints(cls, file):
        extension_check = cls._check_file_extension(os.path.splitext(file.file_path)[1].lower(), cls.ALLOWED_VIDEO_EXTENSIONS)
        if not extension_check[0]:
            return extension_check

        return cls._check_video_file_size(file.file_size)

    # Protected methods

    # Additional helper method for checking video file size
    @classmethod
    def _check_video_file_size(cls, file_size):
        if file_size > cls.MAX_VIDEO_FILE_SIZE:
            max_size_mb = cls.MAX_VIDEO_FILE_SIZE / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            return False, f'The video file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
        return True, ""

    @classmethod
    def _check_file_extension(cls, file_extension, allowed_extensions):
        if file_extension not in allowed_extensions:
            allowed_extensions_str = ", ".join(allowed_extensions)
            return False, f"Unsupported file type. Allowed types: {allowed_extensions_str}."
        return True, ""

    @classmethod
    def _check_file_size(cls, file_size):
        if file_size > cls.MAX_FILE_SIZE:
            max_size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            return False, f'The file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
        return True, ""
