
import unittest
from tools.utils.nlu import extract_symbols

class TestNLU(unittest.TestCase):
    def test_extract_a_share(self):
        # Test 6-digit A-share codes
        text = "Check price of 000001 and 600519"
        symbols = extract_symbols(text)
        self.assertIn("000001", symbols)
        self.assertIn("600519", symbols)

    def test_extract_us_stock(self):
        # Test US stock symbols
        text = "How is AAPL doing? What about TSLA?"
        symbols = extract_symbols(text)
        self.assertIn("AAPL", symbols)
        self.assertIn("TSLA", symbols)

    def test_extract_hk_stock(self):
        # Test HK stock symbols
        text = "Price of 00700 and 09988"
        symbols = extract_symbols(text)
        self.assertIn("00700", symbols)
        self.assertIn("09988", symbols)

    def test_chinese_company_names(self):
        # Test mapping from Chinese names
        text = "平安银行股价多少？"
        symbols = extract_symbols(text)
        self.assertIn("000001", symbols)

        text = "腾讯的股价"
        symbols = extract_symbols(text)
        self.assertIn("00700", symbols)

    def test_mixed_input(self):
        # Test mixed input
        text = "Comparison between 茅台 and AAPL"
        symbols = extract_symbols(text)
        self.assertIn("600519", symbols)
        self.assertIn("AAPL", symbols)

if __name__ == '__main__':
    unittest.main()
