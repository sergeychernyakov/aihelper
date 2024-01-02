import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from lib.telegram.payment import Payment
from telegram import Update, LabeledPrice
from telegram.ext import CallbackContext

class TestPayment(unittest.TestCase):

    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=CallbackContext)

    @patch('lib.telegram.payment.CurrencyConverter.get_conversion_rate')
    @patch('lib.telegram.payment.SessionLocal')
    async def test_successful_payment_callback(self, mock_session, mock_currency_converter):
        # Setup mocks
        mock_currency_converter.return_value = 1  # Simulate conversion rate
        mock_session.return_value = MagicMock()  # Mock the database session

        # Simulate a successful payment update
        self.update.message.successful_payment.total_amount = 10000
        self.update.message.successful_payment.currency = 'RUB'
        self.update.message.from_user.id = 12345

        # Call the method
        await Payment.successful_payment_callback(self.update, self.context)


if __name__ == '__main__':
    unittest.main()
