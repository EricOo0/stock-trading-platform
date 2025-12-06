
import unittest
import json
import sys
import os
from unittest.mock import MagicMock, patch
from io import BytesIO

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api_server import MarketDataAPIHandler

class TestMarketDataAPIHandler(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_client_address = ('127.0.0.1', 8080)
        self.mock_server = MagicMock()
        
    def _create_handler(self, path='/', method='GET', body=None):
        self.mock_request.makefile.return_value = BytesIO(body if body else b'')
        
        # Mocking wfile to capture response
        self.wfile = BytesIO()
        
        # We need to patch BaseHTTPRequestHandler.setup because it tries to read from request socket
        with patch('http.server.BaseHTTPRequestHandler.setup'), \
             patch('http.server.BaseHTTPRequestHandler.handle_one_request'):
            handler = MarketDataAPIHandler(self.mock_request, self.mock_client_address, self.mock_server)
            handler.rfile = BytesIO(body if body else b'')
            handler.wfile = self.wfile
            handler.path = path
            handler.command = method
            handler.headers = {'Content-Length': str(len(body)) if body else '0'}
            return handler

    @patch('backend.api_server.main_handle')
    def test_handle_market_data_hot(self, mock_main_handle):
        # Mock skill response
        mock_main_handle.return_value = {
            'status': 'success', 
            'data': {'name': 'PingAn', 'price': 10.5}
        }
        
        handler = self._create_handler(path='/api/market-data/hot', method='GET')
        handler.handle_hot_stocks()
        
        response = self.wfile.getvalue().decode('utf-8')
        # Extract JSON body (after headers)
        body_start = response.find('{')
        if body_start != -1:
            body = json.loads(response[body_start:])
            self.assertEqual(body['status'], 'success')
            self.assertIn('data', body)
            self.assertIsInstance(body['data'], list)

    @patch('backend.api_server.MarketDataSkill')
    def test_handle_historical_data(self, MockSkill):
        # Mock skill instance
        mock_skill = MockSkill.return_value
        mock_skill.get_historical_data.return_value = {
            'status': 'success',
            'data': [{'date': '2023-01-01', 'close': 100}]
        }
        
        handler = self._create_handler(path='/api/market/historical/AAPL?period=10d', method='GET')
        # We need to manually parse query params as handler does in do_GET
        # But here we call specific method. 
        # Wait, handler.handle_historical_data takes (path, query_params)
        
        handler.handle_historical_data('/api/market/historical/AAPL', {'period': ['10d']})
        
        response = self.wfile.getvalue().decode('utf-8')
        body_start = response.find('{')
        if body_start != -1:
            body = json.loads(response[body_start:])
            self.assertEqual(body['status'], 'success')
            self.assertIn('data', body)
            self.assertEqual(body['symbol'], 'AAPL')

    @patch('backend.api_server.WebSearchSkill')
    def test_handle_web_search(self, MockSkill):
        mock_skill = MockSkill.return_value
        mock_skill._run.return_value = {
            'status': 'success',
            'raw_results': [{'title': 'News', 'url': 'http://example.com'}]
        }
        
        handler = self._create_handler(path='/api/web-search?q=Apple', method='GET')
        handler.handle_web_search({'q': ['Apple']})
        
        response = self.wfile.getvalue().decode('utf-8')
        body_start = response.find('{')
        if body_start != -1:
            body = json.loads(response[body_start:])
            self.assertEqual(body['status'], 'success')
            self.assertIn('results', body)

if __name__ == '__main__':
    unittest.main()
