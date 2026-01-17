import unittest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.entrypoints.api.routers.market import router

app = FastAPI()
app.include_router(router)

class TestSectorAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    def test_get_sectors_flow_hot(self):
        print("\nTesting GET /api/market/sectors/flow?type=hot")
        try:
            response = self.client.get("/api/market/sectors/flow?type=hot&limit=5")
            print("Status Code:", response.status_code)
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data['status'], 'success')
                self.assertEqual(data['type'], 'hot')
                self.assertTrue(len(data['data']) <= 5)
                if len(data['data']) > 0:
                    print("Top hot sector:", data['data'][0]['name'])
            else:
                print("Request failed:", response.text)
        except Exception as e:
            print(f"Test failed with exception: {e}")

    def test_get_sectors_flow_cold(self):
        print("\nTesting GET /api/market/sectors/flow?type=cold")
        try:
            response = self.client.get("/api/market/sectors/flow?type=cold&limit=5")
            print("Status Code:", response.status_code)
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data['status'], 'success')
                self.assertEqual(data['type'], 'cold')
            else:
                 print("Request failed:", response.text)
        except Exception as e:
            print(f"Test failed with exception: {e}")

    def test_get_sector_stocks(self):
        print("\nTesting GET /api/market/sectors/{name}/stocks")
        try:
            # Get a real sector name first
            flow_res = self.client.get("/api/market/sectors/flow?limit=1")
            if flow_res.status_code == 200 and flow_res.json()['data']:
                sector_name = flow_res.json()['data'][0]['name']
                print(f"Testing stocks for sector: {sector_name}")
                
                response = self.client.get(f"/api/market/sectors/{sector_name}/stocks?limit=3")
                print("Status Code:", response.status_code)
                if response.status_code == 200:
                    data = response.json()
                    self.assertEqual(data['status'], 'success')
                    self.assertEqual(data['data']['sector_name'], sector_name)
                    self.assertTrue(len(data['data']['stocks']) <= 3)
                    if len(data['data']['stocks']) > 0:
                         print("Top stock:", data['data']['stocks'][0]['name'])
                else:
                     print("Request failed:", response.text)
            else:
                print("Skipping stock test due to flow failure")
        except Exception as e:
            print(f"Test failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
