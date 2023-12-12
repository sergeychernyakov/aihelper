import tiktoken
from decimal import Decimal
from lib.telegram.assistant import Assistant

class Tokenizer:
    MAX_OUTPUT_TOKENS = 4096
    PROFIT_MARGIN = Decimal('0.16') # 16% profit margin
    MINIMUM_COST = Decimal('0.001')

    # Prices within the class
    PRICES = {
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-1106-vision-preview": {"input": 0.01, "output": 0.03, "image": 0.00085},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0010, "output": 0.0020},
        "gpt-3.5-turbo-1106": {"input": 0.0010, "output": 0.0020},
        "gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-16k": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-16k-0613": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.0020},
        "tts": 0.0015,
        "whisper": 0.006,
        "retrieval": 0.2,
        "dall-e-3": 0.040
    }

    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initializes the tokenizer with a specific model.

        :param model: The model to be used for tokenization.
        """
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

    def num_tokens_from_string(self, string: str) -> int:
        """
        Returns the number of tokens in a given text string.

        :param string: The text string to tokenize.
        :return: The number of tokens in the string.
        """
        return len(self.encoding.encode(string))

    def tokens_to_money(self, tokens: int, token_type: str = "input") -> Decimal:
        """
        Calculates the cost of a given number of tokens, including a profit margin.

        :param tokens: The number of tokens to calculate the cost for.
        :param token_type: The type of tokens ('input' or 'output').
        :return: The cost in Decimal, including the profit margin.
        """
        if token_type not in ['input', 'output']:
            raise ValueError("token_type must be either 'input' or 'output'")
        if tokens < 0:
            raise ValueError("Number of tokens cannot be negative")

        price_per_token = Decimal(str(self.PRICES.get(self.model, {}).get(token_type, 0))) / Decimal('1000')
        total_cost = Decimal(str(tokens)) * price_per_token

        # Add the profit to the total cost
        profit = total_cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = total_cost + profit

        # Adjust the formatting based on the cost
        if total_cost_with_profit < Decimal('0.01'):
            return total_cost_with_profit.quantize(Decimal('0.000001'))  # Less rounding for very small amounts
        else:
            return total_cost_with_profit.quantize(Decimal('0.01'))  # Standard rounding for larger amounts

    def tokens_to_money_from_string(self, string: str, token_type: str = "input") -> Decimal:
        """
        Calculates the cost of tokens required for a given string, based on the model and token type.

        :param string: The text string to process.
        :param token_type: The type of tokens ('input' or 'output').
        :return: The cost in Decimal for processing the given string.
        """
        # Get the number of tokens in the string
        tokens = self.num_tokens_from_string(string)

        # Use the existing method to calculate the cost
        return self.tokens_to_money(tokens, token_type)

    def tokens_to_money_to_voice(self, string: str) -> Decimal:
        """
        Calculates the cost of converting a given string to voice using TTS.

        :param string: The text string to be converted to voice.
        :return: The cost in Decimal for converting the text to voice.
        """
        tts_cost_per_1k_chars = Decimal(str(self.PRICES.get("tts", 0)))  # TTS cost per 1,000 characters
        num_chars = len(string)
        cost = (Decimal(num_chars) / Decimal('1000')) * tts_cost_per_1k_chars

        # Add the profit to the total cost
        profit = cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = cost + profit
        return total_cost_with_profit.quantize(Decimal('0.000001'))

    def tokens_to_money_from_voice(self, seconds: int) -> Decimal:
        """
        Calculates the cost of transcribing voice based on duration in seconds.

        :param seconds: The duration of the voice recording in seconds.
        :return: The cost in Decimal for transcribing the voice.
        """
        whisper_cost_per_minute = Decimal(str(self.PRICES.get("whisper", 0)))  # Whisper cost per minute
        minutes = Decimal(seconds) / Decimal('60')
        cost = minutes * whisper_cost_per_minute

        # Add the profit to the total cost
        profit = cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = cost + profit

        # Ensure the total cost is not less than the minimum cost
        if total_cost_with_profit < Tokenizer.MINIMUM_COST:
            total_cost_with_profit = Tokenizer.MINIMUM_COST

        return total_cost_with_profit.quantize(Decimal('0.000001'))

    def tokens_to_money_from_image(self) -> Decimal:
        """
        Calculates the cost of processing an image using the specified model.

        :return: The cost in Decimal for processing the image.
        """
        image_cost = Decimal(str(self.PRICES.get("gpt-4-1106-vision-preview", {}).get("image", 0)))

        # Add the profit to the total cost
        profit = image_cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = image_cost + profit
        return total_cost_with_profit.quantize(Decimal('0.000001'))

    def tokens_to_money_to_image(self) -> Decimal:
        """
        Calculates the cost of generating an image using DALL-E 3.

        :return: The cost in Decimal for generating the image.
        """
        dall_e_image_cost = Decimal(str(self.PRICES.get("dall-e-3", 0)))

        # Add the profit to the total cost
        profit = dall_e_image_cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = dall_e_image_cost + profit

        # Ensure the total cost is not less than the minimum cost
        if total_cost_with_profit < Tokenizer.MINIMUM_COST:
            total_cost_with_profit = Tokenizer.MINIMUM_COST

        return total_cost_with_profit.quantize(Decimal('0.000001'))

    def tokens_to_money_from_document(self, file_size: int) -> Decimal:
        """
        Calculates the cost of processing a document based on its file size.

        :param file_size: The file size in bytes.
        :return: The cost in Decimal for processing the document.
        """
        retrieval_cost_per_gb = Decimal('0.20')  # Cost per GB
        bytes_per_gb = Decimal('1e9')  # Number of bytes in a GB

        # Convert file size to GB and calculate cost
        cost = (Decimal(file_size) / bytes_per_gb) * retrieval_cost_per_gb

        # Add the profit to the total cost
        profit = cost * Tokenizer.PROFIT_MARGIN
        total_cost_with_profit = cost + profit

        # Ensure the total cost is not less than the minimum cost
        if total_cost_with_profit < Tokenizer.MINIMUM_COST:
            total_cost_with_profit = Tokenizer.MINIMUM_COST

        return total_cost_with_profit.quantize(Decimal('0.000001'))

    def has_sufficient_balance_for_message(self, message: str, balance: Decimal, token_type: str = "input") -> bool:
        """
        Checks if the user's balance is sufficient to cover the cost of the tokens for a given message,
        considering the potential cost of output tokens if the token type is 'input'.

        :param message: The message to be processed.
        :param balance: The current balance of the user.
        :param token_type: The type of token to consider ('input' or 'output').
        :return: True if the balance is sufficient, False otherwise.
        """
        tokens_required = self.num_tokens_from_string(message)
        cost = self.tokens_to_money(tokens_required, token_type)

        if token_type == 'input':
            output_cost = self.tokens_to_money(Tokenizer.MAX_OUTPUT_TOKENS, 'output')
            total_cost = cost + output_cost
        else:
            total_cost = cost

        return balance >= total_cost

    def has_sufficient_balance_for_amount(self, amount: Decimal, balance: Decimal) -> bool:
        """
        Checks if the user's balance is sufficient to cover a specified amount.

        :param amount: The amount to be covered.
        :param balance: The current balance of the user.
        :return: True if the balance is sufficient, False otherwise.
        """
        return balance >= amount

    def calculate_thread_tokens(self, messages):
        """
        Calculates the total number of tokens in a list of messages from thread.

        :param messages: A list of messages from a conversation.
        :return: The total number of tokens in the messages.
        """
        total_tokens = 0
        for message in messages:
            if message.content and message.content[0].type == 'text':
                text = message.content[0].text.value
                total_tokens += self.num_tokens_from_string(text)

        return total_tokens

    def calculate_assistant_prompt_tokens(self):
        assistant = Assistant()
        prompt_text = assistant.prompt()
        if prompt_text:
            return self.num_tokens_from_string(prompt_text)
        else:
            return 0

    def calculate_thread_total_amount(self, messages):
        messages_tokens = self.calculate_thread_tokens(messages)
        prompt_tokens = self.calculate_assistant_prompt_tokens()        
        if prompt_tokens is not None:
            return self.tokens_to_money(messages_tokens + prompt_tokens, 'input')
        else:
            # Handle the case where prompt_tokens is None
            # Perhaps return a default value or raise an error
            return self.tokens_to_money(messages_tokens, 'input')

# Example Usage
# python3
# from lib.telegram.tokenizer import Tokenizer
# tokenizer = Tokenizer("gpt-4")
# input_tokens = tokenizer.num_tokens_from_string("Hello, world!")
# output_tokens = 500  # Assume 500 tokens for the output


# tokenizer.tokens_to_money_from_string('hi')


# try:
#     input_cost = tokenizer.tokens_to_money(input_tokens)  # Defaults to 'input'
#     output_cost = tokenizer.tokens_to_money(output_tokens, "output")
#     print(f"Cost for {input_tokens} input tokens: ${input_cost}")
#     print(f"Cost for {output_tokens} output tokens: ${output_cost}")
# except ValueError as e:
#     print(e)


# Retrieval	$0.20 / GB / assistant / day (free until 12/13/2023)
# DALL·E 3	Standard	1024×1024	$0.040 / image
# Whisper	$0.006 / minute (rounded to the nearest second)
# TTS	$0.015 / 1K characters
