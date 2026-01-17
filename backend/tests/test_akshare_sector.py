import unittest
from backend.infrastructure.market.akshare_tool import AkShareTool

class TestAkShareSector(unittest.TestCase):
    def setUp(self):
        self.tool = AkShareTool()

    def test_get_sector_fund_flow_rank(self):
        print("\nTesting get_sector_fund_flow_rank...")
        rankings = self.tool.get_sector_fund_flow_rank()
        if rankings:
            print(f"Got {len(rankings)} sectors.")
            print("First one:", rankings[0])
            self.assertIn('name', rankings[0])
            self.assertIn('net_flow', rankings[0])
        else:
            print("WARNING: No sector data returned (maybe market closed or API issue)")

    def test_get_sector_components(self):
        print("\nTesting get_sector_components...")
        # Get a valid sector name first
        rankings = self.tool.get_sector_fund_flow_rank()
        if rankings:
            sector_name = rankings[0]['name']
            print(f"Testing components for sector: {sector_name}")
            components = self.tool.get_sector_components(sector_name)
            if components:
                print(f"Got {len(components)} components.")
                print("First component:", components[0])
                self.assertIn('symbol', components[0])
                self.assertIn('amount', components[0])
            else:
                print(f"WARNING: No components found for {sector_name}")
        else:
            print("Skipping component test due to missing rankings")

if __name__ == '__main__':
    unittest.main()
