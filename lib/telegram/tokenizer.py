import tiktoken

class Tokenizer:
    # Prices within the class
    PRICES = {
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-1106-vision-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0010, "output": 0.0020},
        "gpt-3.5-turbo-1106": {"input": 0.0010, "output": 0.0020},
        "gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-16k": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-16k-0613": {"input": 0.0015, "output": 0.0020},
        "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.0020}
    }

    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

    def num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        return len(self.encoding.encode(string))

    def tokens_to_money(self, tokens: int, token_type: str = "input") -> float:
        """Calculates the cost of tokens based on the model and token type (input or output)."""
        if token_type not in ['input', 'output']:
            raise ValueError("token_type must be either 'input' or 'output'")
        if tokens < 0:
            raise ValueError("Number of tokens cannot be negative")

        price_per_token = self.PRICES.get(self.model, {}).get(token_type, 0) / 1000
        total_cost = tokens * price_per_token

        # Adjust the formatting based on the cost
        if total_cost < 0.01:
            return round(total_cost, 5)  # Less rounding for very small amounts
        else:
            return round(total_cost, 2)  # Standard rounding for larger amounts


# Example Usage
# python3
# from lib.telegram.tokenizer import Tokenizer
# tokenizer = Tokenizer("gpt-4")
# input_tokens = tokenizer.num_tokens_from_string("Hello, world!")
# output_tokens = 500  # Assume 500 tokens for the output

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
