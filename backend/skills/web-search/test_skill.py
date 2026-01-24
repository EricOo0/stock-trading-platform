import os
import unittest
from unittest.mock import patch, MagicMock
from skill import WebSearchSkill

class TestWebSearchSkill(unittest.TestCase):

    @patch('skill.TavilyClient')
    def test_search_success(self, MockTavilyClient):
        # Mock the client and its search method
        mock_client_instance = MockTavilyClient.return_value
        mock_client_instance.search.return_value = {
            'results': [
                {'title': 'Test Result 1', 'url': 'http://test1.com', 'content': 'Content 1', 'score': 0.95},
                {'title': 'Test Result 2', 'url': 'http://test2.com', 'content': 'Content 2', 'score': 0.8},
                {'title': 'Low Score Result', 'url': 'http://low.com', 'content': 'Low Content', 'score': 0.1} 
            ]
        }

        # Initialize skill with a dummy key
        skill = WebSearchSkill(api_key="test_key")
        
        # Call search
        results = skill.search("test query")
        
        # Verify results
        self.assertEqual(len(results), 2) # Should filter out low score
        self.assertEqual(results[0]['title'], 'Test Result 1')
        self.assertEqual(results[0]['href'], 'http://test1.com')
        self.assertEqual(results[1]['title'], 'Test Result 2')
        
        # Verify client call
        mock_client_instance.search.assert_called_with(
            query="test query",
            search_depth="advanced",
            max_results=10,
            include_answer=True
        )

    @patch('skill.TavilyClient')
    def test_search_news_params(self, MockTavilyClient):
        mock_client_instance = MockTavilyClient.return_value
        mock_client_instance.search.return_value = {'results': []}

        skill = WebSearchSkill(api_key="test_key")
        skill.search("news query", topic="news", days=5)

        mock_client_instance.search.assert_called_with(
            query="news query",
            search_depth="advanced",
            max_results=10,
            include_answer=True,
            topic="news",
            days=5
        )

    @patch('skill.TavilyClient')
    def test_search_domains_params(self, MockTavilyClient):
        mock_client_instance = MockTavilyClient.return_value
        mock_client_instance.search.return_value = {'results': []}

        skill = WebSearchSkill(api_key="test_key")
        skill.search("domain query", include_domains=["example.com"])

        mock_client_instance.search.assert_called_with(
            query="domain query",
            search_depth="advanced",
            max_results=10,
            include_answer=True,
            include_domains=["example.com"]
        )

if __name__ == '__main__':
    unittest.main()
