from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.entrypoints.api.server import app
from backend.app.agents.personal_finance.models import RecommendationCard, RecommendationAction
import json

client = TestClient(app)

# Mock Graph Event Generator
async def mock_graph_stream(input_state):
    yield {"planner": {"selected_agents": ["macro"]}}
    yield {"executor": {"macro_analysis": "Macro is good."}}
    yield {"synthesizer": {
        "final_report": "Report Content", 
        "recommendation_cards": [
            RecommendationCard(
                title="Test Card",
                description="Desc",
                action=RecommendationAction.BUY,
                confidence_score=0.8,
                risk_level="low"
            )
        ]
    }}

@patch("backend.entrypoints.api.routers.agent_personal_finance.create_personal_finance_graph")
def test_analyze_endpoint(mock_create_graph):
    # Mock the graph object and its astream method
    mock_graph = MagicMock()
    mock_graph.astream.side_effect = mock_graph_stream
    mock_create_graph.return_value = mock_graph
    
    payload = {
        "assets": [{"symbol": "AAPL", "type": "Stock", "quantity": 10}],
        "query": "Analysis please"
    }
    
    response = client.post("/api/personal-finance/analyze", json=payload)
    
    assert response.status_code == 200
    # Response is NDJSON
    lines = response.text.strip().split('\n')
    assert len(lines) > 0
    
    # Check for specific event types
    event_types = [json.loads(line)["type"] for line in lines]
    assert "status" in event_types
    assert "report_chunk" in event_types
    assert "card" in event_types
    assert "done" in event_types
