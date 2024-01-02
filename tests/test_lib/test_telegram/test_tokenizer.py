import unittest
from unittest.mock import patch, MagicMock
from lib.telegram.tokenizer import Tokenizer
from decimal import Decimal

class TestTokenizer(unittest.TestCase):

    @patch('tiktoken.encoding_for_model')
    def setUp(self, mock_encoding):
        # Setup a default Tokenizer for use in all tests
        mock_encoding.return_value = MagicMock(encode=MagicMock(side_effect=lambda x: list(range(len(x)))))
        self.tokenizer = Tokenizer()

    @patch('tiktoken.encoding_for_model')
    def test_default_model_initialization(self, mock_encoding):
        mock_encoding.return_value = 'mocked_encoding'
        tokenizer = Tokenizer()
        self.assertEqual(tokenizer.model, "gpt-3.5-turbo")
        self.assertEqual(tokenizer.encoding, 'mocked_encoding')

    @patch('tiktoken.encoding_for_model')
    def test_model_assignment(self, mock_encoding):
        test_model = "gpt-4"
        mock_encoding.return_value = 'mocked_encoding_gpt4'
        tokenizer = Tokenizer(model=test_model)
        self.assertEqual(tokenizer.model, test_model)
        self.assertEqual(tokenizer.encoding, 'mocked_encoding_gpt4')

    def test_num_tokens_from_empty_string(self):
        self.assertEqual(self.tokenizer.num_tokens_from_string(""), 0)

    def test_num_tokens_from_non_empty_string(self):
        test_cases = [
            ("Hello", 5),
            ("Test string", 11),
            ("Another test", 12)
        ]
        for text, expected_count in test_cases:
            with self.subTest(text=text):
                self.assertEqual(self.tokenizer.num_tokens_from_string(text), expected_count)

    def test_num_tokens_with_non_string_input(self):
        with self.assertRaises(TypeError):
            self.tokenizer.num_tokens_from_string(None)
            self.tokenizer.num_tokens_from_string(123)

    def test_tokens_to_money_with_valid_input(self):
        test_cases = [
            (12345, 'input', Decimal('0.02')),  # Assuming a specific cost for tokens
            (3412, 'output', Decimal('0.008939'))  # And so on...
        ]
        for token_count, token_type, expected_cost in test_cases:
            with self.subTest(token_count=token_count, token_type=token_type):
                actual_cost = self.tokenizer.tokens_to_money(token_count, token_type)
                self.assertEqual(actual_cost, expected_cost)

    def test_tokens_to_money_with_invalid_token_type(self):
        with self.assertRaises(ValueError):
            self.tokenizer.tokens_to_money(1000, 'invalid_type')

    def test_tokens_to_money_with_negative_tokens(self):
        with self.assertRaises(ValueError):
            self.tokenizer.tokens_to_money(-1, 'input')

    def test_tokens_to_money_zero_tokens(self):
        self.assertEqual(self.tokenizer.tokens_to_money(0, 'input'), Decimal('0.003'))

    def test_tokens_to_money_from_string_with_valid_input(self):
        test_cases = [
            ("Hello", 'input', Decimal('0.003')),  # Assuming specific costs based on token count
            ("Another test" * 2345, 'output', Decimal('0.07')),
            ("Another test" * 3234, 'output', Decimal('0.10'))
        ]
        for text, token_type, expected_cost in test_cases:
            with self.subTest(text=text, token_type=token_type):
                actual_cost = self.tokenizer.tokens_to_money_from_string(text, token_type)
                self.assertEqual(actual_cost, expected_cost)

    def test_tokens_to_money_from_string_with_empty_string(self):
        self.assertEqual(self.tokenizer.tokens_to_money_from_string("", 'input'), Decimal('0.003'))

    def test_tokens_to_money_to_voice(self):
        test_cases = [
            ("Hello world"*1234, Decimal('0.026673')),  # Cost for 11 characters
            ("", Decimal('0.003')),  # Minimum cost for an empty string
            # Add more test cases as needed
        ]
        for text, expected_cost in test_cases:
            with self.subTest(text=text):
                actual_cost = self.tokenizer.tokens_to_money_to_voice(text)
                self.assertEqual(actual_cost, expected_cost)

if __name__ == '__main__':
    unittest.main()
