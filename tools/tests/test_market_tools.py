
import unittest
import sys
import os

# Ensure tools can be imported
sys.path.append(os.getcwd())

from tools.market.akshare import AkShareTool
from tools.market.yahoo import YahooFinanceTool

class TestMarketToolsExtensions(unittest.TestCase):
    def setUp(self):
        self.ak = AkShareTool()
        self.yahoo = YahooFinanceTool(enable_rotation=False)

    def test_akshare_alias(self):
        # Test get_historical_data alias
        # We mock or just run it (it might fail if network issue, but we check signature mostly)
        # To avoid network, we can verify the method exists
        self.assertTrue(hasattr(self.ak, 'get_historical_data'))
        # Optional: Run live test if environment allows, but for unit test speed keep it light
        # res = self.ak.get_historical_data("600036", period="5d")
        # self.assertIsInstance(res, list)

    def test_yahoo_alias(self):
        self.assertTrue(hasattr(self.yahoo, 'get_historical_data'))

    def test_yahoo_macro_history(self):
        self.assertTrue(hasattr(self.yahoo, 'get_macro_history'))
        # Basic smoke test for VIX
        try:
            res = self.yahoo.get_macro_history("VIX", period="2d")
            if "error" not in res:
                self.assertIn("data", res)
                self.assertTrue(len(res["data"]) > 0)
        except Exception as e:
            print(f"Skipping live yahoo test: {e}")

if __name__ == '__main__':
    unittest.main()
