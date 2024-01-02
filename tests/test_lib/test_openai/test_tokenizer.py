import unittest
from unittest.mock import patch, MagicMock
from lib.openai.tokenizer import Tokenizer
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

    def test_tokens_to_money_from_voice(self):
        test_cases = [
            (0, Decimal('0.003')),  # Cost for 1 minute
            (60, Decimal('0.007860')),  # Cost for 1 minute
            (30, Decimal('0.003930')),  # Cost for 30 seconds, assuming minimum cost applies
            (120, Decimal('0.015720')), # Cost for 2 minutes
        ]
        for seconds, expected_cost in test_cases:
            with self.subTest(seconds=seconds):
                actual_cost = self.tokenizer.tokens_to_money_from_voice(seconds)
                self.assertEqual(actual_cost, expected_cost)

    def test_tokens_to_money_from_image(self):
        expected_cost = Decimal('0.003000')
        actual_cost = self.tokenizer.tokens_to_money_from_image()
        self.assertEqual(actual_cost, expected_cost)

    def test_tokens_to_money_from_video(self):
        test_cases = [
            # Test case format: (seconds, frame_interval, expected_cost)
            (0, 60, Decimal('0.003')),  # 1 frame in 60 seconds
            (120, 60, Decimal('0.003000')), # 2 frames in 120 seconds
            (4800, 10, Decimal('0.534480')),  # 2 frames in 60 seconds
            # Add more test cases as needed
        ]
        for seconds, frame_interval, expected_cost in test_cases:
            with self.subTest(seconds=seconds, frame_interval=frame_interval):
                actual_cost = self.tokenizer.tokens_to_money_from_video(seconds, frame_interval)
                self.assertEqual(actual_cost, expected_cost)

    def test_has_sufficient_balance_for_message(self):
        test_cases = [
            # Test case format: (message, balance, token_type, expected_result)
            ("Short message", Decimal('1.00'), 'input', True),  # Assuming the cost is less than the balance
            ("Long message that requires more tokens" * 300, Decimal('0.01'), 'input', False),  # Cost exceeds balance
            ("Long message that requires more tokens" * 300, Decimal('1.00'), 'input', True),  # Cost exceeds balance
            ("Short message", Decimal('0.001'), 'output', False),  # Insufficient balance for output tokens
            ("", Decimal('0.04'), 'input', True),  # Empty message with minimum balance
            # Add more test cases as needed
        ]
        for message, balance, token_type, expected_result in test_cases:
            with self.subTest(message=message, balance=balance, token_type=token_type):
                result = self.tokenizer.has_sufficient_balance_for_message(message, balance, token_type)
                self.assertEqual(result, expected_result)

    def test_has_sufficient_balance_for_amount(self):
        test_cases = [
            # Test case format: (amount, balance, expected_result)
            (Decimal('0.50'), Decimal('1.00'), True),  # Balance is greater than amount
            (Decimal('1.00'), Decimal('0.50'), False), # Balance is less than amount
            (Decimal('0.75'), Decimal('0.75'), True),  # Balance equals amount
            (Decimal('0.00'), Decimal('0.00'), True),  # Zero amount with zero balance
            # Add more test cases as needed
        ]
        for amount, balance, expected_result in test_cases:
            with self.subTest(amount=amount, balance=balance):
                result = self.tokenizer.has_sufficient_balance_for_amount(amount, balance)
                self.assertEqual(result, expected_result)

    def test_calculate_thread_tokens(self):
        test_cases = [
            # Test case format: (messages, expected_total_tokens)
            ([{'content': [{'type': 'text', 'text': {'value': 'Hello'}}]}, 
              {'content': [{'type': 'text', 'text': {'value': 'World'}}]}], 10),  # Two messages with 5 tokens each
            ([], 0),  # Empty thread
            ([{'content': [{'type': 'text', 'text': {'value': 'A longer sentence here'}}]}], 22),  # One longer message
            # Add more test cases as needed
        ]
        for messages, expected_total_tokens in test_cases:
            with self.subTest(messages=messages):
                # Create mock messages with the proper structure
                adjusted_messages = []
                for message in messages:
                    mock_message = MagicMock()
                    mock_message.content = []
                    for item in message['content']:
                        mock_content_item = MagicMock()
                        mock_content_item.type = item['type']
                        mock_content_item.text = MagicMock(value=item['text']['value'])
                        mock_message.content.append(mock_content_item)
                    adjusted_messages.append(mock_message)

                total_tokens = self.tokenizer.calculate_thread_tokens(adjusted_messages)
                self.assertEqual(total_tokens, expected_total_tokens)

    @patch('lib.openai.tokenizer.Assistant')
    def test_calculate_assistant_prompt_tokens(self, mock_assistant):
        test_cases = [
            ("Short prompt", 12),  # Assuming "Short prompt" is 12 tokens
            ("", 0),  # Empty prompt
            ("A longer prompt sentence for testing.", 37),  # Longer prompt
        ]
        for prompt_text, expected_token_count in test_cases:
            with self.subTest(prompt_text=prompt_text):
                mock_assistant.return_value.prompt.return_value = prompt_text
                actual_token_count = self.tokenizer.calculate_assistant_prompt_tokens()
                self.assertEqual(actual_token_count, expected_token_count)

    @patch('lib.openai.tokenizer.Tokenizer.calculate_thread_tokens')
    @patch('lib.openai.tokenizer.Tokenizer.calculate_assistant_prompt_tokens')
    def test_calculate_thread_total_amount(self, mock_calculate_prompt_tokens, mock_calculate_thread_tokens):
        test_cases = [
            # Test case format: (thread_tokens, prompt_tokens, expected_total_cost)
            (12344, 50, Decimal('0.02')),  # Assuming specific costs based on token counts
            (0, 0, Decimal('0.003')),    # Empty thread and prompt with minimum cost
            (1500, 1200, Decimal('0.003537')), # More tokens
            # Add more test cases as needed
        ]
        for thread_tokens, prompt_tokens, expected_total_cost in test_cases:
            with self.subTest(thread_tokens=thread_tokens, prompt_tokens=prompt_tokens):
                mock_calculate_thread_tokens.return_value = thread_tokens
                mock_calculate_prompt_tokens.return_value = prompt_tokens
                actual_total_cost = self.tokenizer.calculate_thread_total_amount([])
                self.assertEqual(actual_total_cost, expected_total_cost)

if __name__ == '__main__':
    unittest.main()
