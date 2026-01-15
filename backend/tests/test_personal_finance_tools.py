import pytest
import asyncio
import sys
import os

from sympy import true

# Add project root to sys.path to ensure imports work if run directly
sys.path.append(os.getcwd())

from backend.app.agents.personal_finance.tools import get_market_context

@pytest.mark.asyncio
async def test_get_market_context():
    """Test get_market_context returns valid structure."""
    print("\nStarting test_get_market_context...")
    try:
        context = await get_market_context(as_markdown=True)
        
        # Check basic structure
        assert isinstance(context, dict)
        assert "timestamp" in context
        assert "indices" in context
        assert "sectors" in context
        assert "concepts" in context
        assert "macro" in context
        assert "calendar" in context
        assert "errors" in context
        
        # Check indices structure
        indices = context["indices"]
        assert "A_Share" in indices
        assert "HK" in indices
        assert "US" in indices

        # Check calendar
        calendar = context["calendar"]
        assert isinstance(calendar, list)
        if calendar:
            first_event = calendar[0]
            assert "event" in first_event
            assert "date" in first_event

        # Check news
        if "news" in context:
            news = context["news"]
            assert isinstance(news, list)
            if news:
                first_news = news[0]
                assert "title" in first_news
                assert "publish_time" in first_news
        
        # Print for manual verification
        print("\n=== Market Context ===")
        import json
        # Use default=str to handle datetime objects
        print(json.dumps(context, indent=2, ensure_ascii=False, default=str))
        
        # Verify A-Share indices if available (AkShare reliability varies)
        if indices["A_Share"]:
            first = indices["A_Share"][0]
            assert "名称" in first or "name" in first
            assert "最新价" in first or "close" in first

    except Exception as e:
        pytest.fail(f"get_market_context failed: {e}")

if __name__ == "__main__":
    # Helper for running directly
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_get_market_context())
    finally:
        loop.close()
