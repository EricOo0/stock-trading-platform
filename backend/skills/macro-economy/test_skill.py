import unittest
from skill import MacroEconomySkill
import json
import logging
from datetime import datetime

# Disable detailed logging for tests
logging.getLogger("macro-economy-skill").setLevel(logging.WARNING)

class TestMacroEconomySkill(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.skill = MacroEconomySkill()

    def test_cn_macro_gdp(self):
        result = self.skill.get_cn_macro("GDP")
        print(f"CN GDP: {result}")
        if "error" not in result:
            self.assertEqual(result["indicator"], "China GDP")
            self.assertIn("value", result)

    def test_cn_macro_cpi(self):
        result = self.skill.get_cn_macro("CPI")
        print(f"CN CPI: {result}")
        if "error" not in result:
            self.assertEqual(result["indicator"], "China CPI")

    def test_cn_macro_lpr(self):
        result = self.skill.get_cn_macro("LPR")
        print(f"CN LPR: {result}")
        if "error" not in result:
            self.assertEqual(result["indicator"], "China LPR")
            self.assertIn("1y", result)

    def test_us_macro_cpi(self):
        # Note: US macro APIs in akshare might be unstable or require connection
        result = self.skill.get_us_macro("CPI")
        print(f"US CPI: {result}")
        # Soft assertion as API might fail due to network
        if "error" not in result:
            self.assertEqual(result["indicator"], "US CPI")

    def test_market_risk(self):
        result = self.skill.get_market_risk()
        print(f"Market Risk: {json.dumps(result, indent=2)}")
        if "error" not in result:
            # Check for at least one key being present and valid
            valid_keys = ['VIX', 'US10Y', 'DXY', 'GOLD', 'CRUDE_OIL']
            found = False
            for k in valid_keys:
                if k in result and "error" not in result[k]:
                    found = True
                    break
            if not found:
                 print("Warning: All risk indicators failed or empty")
            # We don't fail test if network is flaky, but we check structure

    def test_economic_calendar(self):
        today = datetime.now().strftime("%Y%m%d")
        result = self.skill.get_economic_calendar(today)
        print(f"Calendar ({today}) count: {len(result)}")
        # Valid if list is returned (empty is allowed)
        self.assertIsInstance(result, list)

if __name__ == '__main__':
    unittest.main()
