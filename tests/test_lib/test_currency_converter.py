import unittest
import requests
from unittest.mock import patch, MagicMock
from lib.currency_converter import CurrencyConverter
from decimal import Decimal
from datetime import datetime, timedelta

class TestCurrencyConverter(unittest.TestCase):

    def setUp(self):
        CurrencyConverter._cache = {}  # Reset cache before each test

    @patch('lib.currency_converter.requests.get')
    def test_get_conversion_rate_same_currency(self, mock_get):
        rate = CurrencyConverter.get_conversion_rate('USD', 'USD')
        self.assertEqual(rate, Decimal(1))
        mock_get.assert_not_called()

    @patch('lib.currency_converter.requests.get')
    def test_get_conversion_rate_different_currency(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'rates': {'EUR': Decimal('0.85')}}
        mock_get.return_value = mock_response

        rate = CurrencyConverter.get_conversion_rate('USD', 'EUR')
        self.assertEqual(rate, Decimal('0.85').quantize(Decimal('0.01')))  # Rounding for comparison

    @patch('lib.currency_converter.requests.get')
    def test_get_conversion_rate_with_caching(self, mock_get):
        # Set a rate in the cache
        CurrencyConverter._cache['USD-EUR'] = {'rate': Decimal('0.85'), 'expiry': datetime.now() + timedelta(days=1)}

        rate = CurrencyConverter.get_conversion_rate('USD', 'EUR')
        self.assertEqual(rate, Decimal('0.85'))
        mock_get.assert_not_called()  # Ensure API was not called due to caching

    @patch('lib.currency_converter.requests.get')
    def test_get_conversion_rate_cache_expired(self, mock_get):
        # Set an expired rate in the cache
        CurrencyConverter._cache['USD-EUR'] = {'rate': Decimal('0.85'), 'expiry': datetime.now() - timedelta(days=1)}

        mock_response = MagicMock()
        mock_response.json.return_value = {'rates': {'EUR': Decimal('0.86')}}
        mock_get.return_value = mock_response

        rate = CurrencyConverter.get_conversion_rate('USD', 'EUR')
        self.assertEqual(rate, Decimal('0.86').quantize(Decimal('0.01')))  # Rounding for comparison

    @patch('lib.currency_converter.requests.get')
    def test_get_conversion_rate_api_error(self, mock_get):
        mock_get.side_effect = requests.RequestException('API Error')

        rate = CurrencyConverter.get_conversion_rate('USD', 'EUR')
        self.assertIsNone(rate)  # Check if the method returns None on API error
        mock_get.assert_called_once()

    def test_set_cache_duration(self):
        CurrencyConverter.set_cache_duration(3600)  # 1 hour
        self.assertEqual(CurrencyConverter._cache_duration, timedelta(seconds=3600))

if __name__ == '__main__':
    unittest.main()
