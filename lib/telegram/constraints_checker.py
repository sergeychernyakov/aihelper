import os

class ConstraintsChecker:
    MAX_FILE_SIZE = 5.0 * 1024 * 1024  # 5 MB in bytes
    ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    ALLOWED_VOICE_EXTENSIONS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.oga'} 
    ALLOWED_FILE_EXTENSIONS = {'.txt', '.tex', '.docx', '.html', '.pdf', '.pptx', '.txt', '.tar', '.zip'}
    MAX_DIMENSION_SIZE = 2000  # Max pixels for the longest side of the photo

    @classmethod
    def check_photo_constraints(cls, file, photo):
        result, message = cls._check_extension_and_size(
            os.path.splitext(file.file_path)[1], 
            cls.ALLOWED_PHOTO_EXTENSIONS, 
            file.file_size
        )
        if not result:
            return result, message

        if photo.width > cls.MAX_DIMENSION_SIZE or photo.height > cls.MAX_DIMENSION_SIZE:
            return False, "Image dimensions are too large."
        return True, ""

    @classmethod
    def check_voice_constraints(cls, file):
        return cls._check_extension_and_size(
            os.path.splitext(file.file_path)[1], 
            cls.ALLOWED_VOICE_EXTENSIONS, 
            file.file_size
        )

    @classmethod
    def check_document_constraints(cls, file):
        return cls._check_extension_and_size(
            os.path.splitext(file.file_path)[1], 
            cls.ALLOWED_FILE_EXTENSIONS, 
            file.file_size
        )

    # private

    @classmethod
    def _check_extension_and_size(cls, file_extension, allowed_extensions, file_size):
        if file_extension.lower() not in allowed_extensions:
            allowed_extensions_str = ", ".join(allowed_extensions)
            return False, f"Unsupported file type. Allowed types: {allowed_extensions_str}."

        if file_size > cls.MAX_FILE_SIZE:
            max_size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            return False, f'The file size is too large: {file_size_mb:.2f} MB. Max allowed is {max_size_mb:.2f} MB.'
        return True, ""
