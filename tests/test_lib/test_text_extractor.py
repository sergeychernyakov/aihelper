import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
from lib.text_extractor import TextExtractor

class TestTextExtractor(unittest.TestCase):

    def test_extract_from_txt(self):
        mock_content = "Sample text content"
        with patch("builtins.open", mock_open(read_data=mock_content)) as mock_file:
            result = TextExtractor._read_plain_text("dummy.txt")
            mock_file.assert_called_once_with("dummy.txt", "r")
            self.assertEqual(result, mock_content)

    def test_extract_from_docx(self):
        mock_paragraphs = [MagicMock(text="First Paragraph"), MagicMock(text="Second Paragraph")]
        with patch("docx.Document") as mock_docx:
            mock_docx.return_value.paragraphs = mock_paragraphs
            result = TextExtractor._extract_from_docx("dummy.docx")
            mock_docx.assert_called_once_with("dummy.docx")
            self.assertEqual(result, "First Paragraph\nSecond Paragraph")

    # Adjustments to the test_extract_from_html method
    def test_extract_from_html(self):
        mock_html_content = "<html><head><title>Test</title></head><body><p>First paragraph.</p><p>Second paragraph.</p></body></html>"
        with patch("builtins.open", mock_open(read_data=mock_html_content)), \
            patch("bs4.BeautifulSoup.get_text", return_value="First paragraph.\nSecond paragraph."):
            result = TextExtractor._extract_from_html("dummy.html")
            expected_result = "First paragraph.\nSecond paragraph."
            self.assertEqual(result, expected_result)

    @patch('lib.text_extractor.Presentation')
    def test_extract_from_pptx(self, mock_presentation):
        # Mock data
        slide_texts = ["First slide text.", "Second slide text."]
        mock_shapes = [MagicMock(text=text) for text in slide_texts]
        mock_slide = MagicMock()
        mock_slide.shapes = mock_shapes
        mock_presentation.return_value.slides = [mock_slide, mock_slide]  # Two slides with the same shapes

        # Call the method under test
        result = TextExtractor._extract_from_pptx("dummy.pptx")

        # Assert the result is as expected
        expected_text = '\n'.join(slide_texts + slide_texts)  # Each slide text appears twice
        self.assertEqual(result, expected_text)


    @patch('lib.text_extractor.process')
    def test_extract_from_doc(self, mock_process):
        # Mock data
        mock_extracted_text = b"Sample text content from a DOC file"
        mock_process.return_value = mock_extracted_text

        # Call the method under test
        result = TextExtractor._extract_from_doc("dummy.doc")

        # Assert that the mock process was called correctly
        mock_process.assert_called_once_with("dummy.doc")

        # Assert the result is as expected
        expected_text = mock_extracted_text.decode('utf-8')
        self.assertEqual(result, expected_text)


    @patch('lib.text_extractor.shutil.copytree')
    @patch('lib.text_extractor.os.walk')
    @patch('lib.text_extractor.open', new_callable=unittest.mock.mock_open, read_data="Extracted RTF content")
    @patch('lib.text_extractor.os.makedirs')
    def test_extract_from_rtfd(self, mock_makedirs, mock_open, mock_walk, mock_copytree):
        # Setup mocks
        mock_walk.return_value = [('root', [], ['sample.rtf'])]

        # Call the method under test
        result = TextExtractor._extract_from_rtfd("dummy.rtfd")

        # Assert the result is as expected
        expected_text = "Extracted RTF content"
        self.assertEqual(result, expected_text)

        # Assert the temporary directory is created
        mock_makedirs.assert_called_once_with('tmp/rtfd_extraction', exist_ok=True)

        # Assert the RTFD content is copied to the temporary directory
        mock_copytree.assert_called_once_with("dummy.rtfd", "tmp/rtfd_extraction", dirs_exist_ok=True)

        # Assert the RTF file is read
        mock_open.assert_called_once_with(os.path.join('root', 'sample.rtf'), 'r')


    @patch('lib.text_extractor.shutil.rmtree')
    @patch('lib.text_extractor.TextExtractor.extract_text')
    @patch('lib.text_extractor.tarfile.open')
    @patch('lib.text_extractor.os.walk')
    @patch('lib.text_extractor.os.makedirs')
    def test_extract_from_tar(self, mock_makedirs, mock_walk, mock_tar_open, mock_extract_text, mock_rmtree):
        # Mock data setup
        mock_extract_text.side_effect = lambda file_path: f"Extracted text from {os.path.basename(file_path)}"
        mock_walk.return_value = [('root', [], ['file1.txt', 'file2.docx'])]

        # Mock tarfile behavior
        mock_tarfile = MagicMock()
        mock_tarfile.__enter__.return_value = mock_tarfile
        mock_tar_open.return_value = mock_tarfile

        # Call the method under test
        result = TextExtractor._extract_from_tar("dummy.tar")

        # Assert the result is as expected
        expected_text = "Extracted text from file1.txt\nExtracted text from file2.docx"
        self.assertEqual(result, expected_text)

        # Assert the temporary directory is created
        mock_makedirs.assert_called_once_with('tmp/tar_extraction', exist_ok=True)

        # Assert the tar file is opened and extracted
        mock_tar_open.assert_called_once_with("dummy.tar", 'r:*')
        mock_tarfile.extractall.assert_called_once_with('tmp/tar_extraction')

        # Assert the temporary directory is cleaned up
        mock_rmtree.assert_called_once_with('tmp/tar_extraction', ignore_errors=True)


    @patch('lib.text_extractor.shutil.rmtree')
    @patch('lib.text_extractor.TextExtractor.extract_text')
    @patch('lib.text_extractor.zipfile.ZipFile')
    @patch('lib.text_extractor.os.walk')
    @patch('lib.text_extractor.os.makedirs')
    def test_extract_from_zip(self, mock_makedirs, mock_walk, mock_zipfile, mock_extract_text, mock_rmtree):
        # Mock data setup
        mock_extract_text.side_effect = lambda file_path: f"Extracted text from {os.path.basename(file_path)}"
        mock_walk.return_value = [('root', [], ['file1.txt', 'file2.docx'])]

        # Mock zipfile behavior
        mock_zip = MagicMock()
        mock_zip.__enter__.return_value = mock_zip
        mock_zipfile.return_value = mock_zip

        # Call the method under test
        result = TextExtractor._extract_from_zip("dummy.zip")

        # Assert the result is as expected
        expected_text = "Extracted text from file1.txt\nExtracted text from file2.docx"
        self.assertEqual(result, expected_text)

        # Assert the temporary directory is created
        mock_makedirs.assert_called_once_with('tmp/zip_extraction', exist_ok=True)

        # Assert the zip file is opened and extracted
        mock_zipfile.assert_called_once_with("dummy.zip", 'r')
        mock_zip.extractall.assert_called_once_with('tmp/zip_extraction')

        # Assert the temporary directory is cleaned up
        mock_rmtree.assert_called_once_with('tmp/zip_extraction', ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
