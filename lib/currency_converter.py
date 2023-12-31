# lib/currency_converter.py

import requests
from datetime import datetime, timedelta
from decimal import Decimal

class CurrencyConverter:
    API_URL = 'https://api.exchangerate-api.com/v4/latest/'
    _cache = {}
    _cache_duration = timedelta(days=1)  # Default cache duration of 1 day

    @classmethod
    def set_cache_duration(cls, duration_in_seconds: int):
        cls._cache_duration = timedelta(seconds=duration_in_seconds)

    @classmethod
    def _is_cache_expired(cls, key: str) -> bool:
        if key not in cls._cache:
            return True
        return datetime.now() > cls._cache[key]['expiry']

    @classmethod
    def get_conversion_rate(cls, from_currency: str, to_currency: str) -> Decimal:
        cache_key = f"{from_currency}-{to_currency}"

        if not cls._is_cache_expired(cache_key):
            return cls._cache[cache_key]['rate']

        try:
            response = requests.get(f"{cls.API_URL}{from_currency}")
            response.raise_for_status()
            data = response.json()
            rate = Decimal(data['rates'].get(to_currency, 0))
            
            cls._cache[cache_key] = {
                'rate': rate,
                'expiry': datetime.now() + cls._cache_duration
            }
            return rate
        except requests.RequestException as e:
            print(f"Error fetching conversion rate: {e}")
            return None  # or a default value


# Example usage
# from lib.currency_converter import CurrencyConverter
# converter = CurrencyConverter()
# converter.set_cache_duration(86400)  # Set cache duration to 1 day (86400 seconds)
# conversion_rate = converter.get_conversion_rate('RUB', 'USD')
# if conversion_rate:
#     print(f"Current RUB to USD conversion rate: {conversion_rate:.3f}")
# else:
#     print("Conversion rate not found or error in fetching.")
