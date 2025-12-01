#!/usr/bin/env python3
"""Test script for A2A streaming functionality."""

import sys
import os
# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


"""Test script for A2A streaming functionality."""

import asyncio
import json
from core.config import get_config
from core.agent import StockAnalysisAgent
import uuid

async def test_a2a_streaming():
    """Test the new A2A streaming functionality."""
    print("🚀 Testing A2A Streaming Implementation")
    print("=" * 50)
    
    try:
        # Initialize agent
        config = get_config()
        agent = StockAnalysisAgent(config)
        
        # Test query
        test_query = "Analyze the stock price of Apple (AAPL) and its recent news sentiment."
        print(f"Test Query: {test_query}")
        print("-" * 50)
        
        # Stream events
        event_count = 0
        async for event in agent.stream_run(test_query):
            event_count += 1
            print(f"\n📡 Event #{event_count}:")
            print(json.dumps(event, indent=2, ensure_ascii=False))
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)
        
        print(f"\n✅ Streaming completed! Total events: {event_count}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_agents():
    """Test individual A2A agents."""
    print("\n🔍 Testing Individual A2A Agents")
    print("=" * 50)
    
    try:
        from core.a2a_client import get_a2a_agent_client
        
        client = get_a2a_agent_client()
        test_message = "What is the current price of AAPL?"
        
        agents_to_test = [
            "receptionist",
            "chairman", 
            "marketdatainvestigator",
            "sentimentinvestigator"
        ]
        
        for agent_name in agents_to_test:
            print(f"\n🤖 Testing {agent_name}...")
            try:
                response = await client.call_agent(agent_name, test_message)
                print(f"   Success: {response.success}")
                if response.success:
                    print(f"   Response: {response.response[:100]}...")
                    print(f"   Steps: {len(response.steps) if response.steps else 0}")
                else:
                    print(f"   Error: {response.error}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Error testing individual agents: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🧪 A2A Streaming Test Suite")
    print("=" * 60)
    
    # Test streaming functionality
    await test_a2a_streaming()
    
    # Test individual agents
    await test_individual_agents()
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())