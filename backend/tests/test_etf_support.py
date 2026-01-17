
import unittest
from backend.app.registry import Tools
from backend.infrastructure.market.sina import SinaFinanceTool

class TestETFSupport(unittest.TestCase):
    def setUp(self):
        self.tools = Tools()
        self.sina = SinaFinanceTool()

    def test_registry_detect_market(self):
        """Test if registry detects A-share ETFs correctly"""
        # SH ETF (51xxxx)
        self.assertEqual(self.tools._detect_market("510050"), "A-share") # SSE 50 ETF
        self.assertEqual(self.tools._detect_market("513050"), "A-share") # ChinaAMC Kweb
        self.assertEqual(self.tools._detect_market("588000"), "A-share") # STAR 50 ETF
        
        # SZ ETF (15xxxx)
        self.assertEqual(self.tools._detect_market("159915"), "A-share") # ChiNext ETF
        self.assertEqual(self.tools._detect_market("159901"), "A-share") # Deep 100 ETF
        
        # LOF (16xxxx)
        self.assertEqual(self.tools._detect_market("162411"), "A-share") # HuaBao Oil Gas

    def test_sina_format_conversion(self):
        """Test if Sina tool converts ETF symbols to correct sh/sz prefix"""
        # SH (60, 68, 51, 58) -> sh
        self.assertEqual(self.sina._convert_to_sina_format("510050", "A-share"), "sh510050")
        self.assertEqual(self.sina._convert_to_sina_format("588000", "A-share"), "sh588000")
        
        # SZ (00, 30, 15, 16) -> sz
        self.assertEqual(self.sina._convert_to_sina_format("159915", "A-share"), "sz159915")
        self.assertEqual(self.sina._convert_to_sina_format("162411", "A-share"), "sz162411")

if __name__ == "__main__":
    unittest.main()
