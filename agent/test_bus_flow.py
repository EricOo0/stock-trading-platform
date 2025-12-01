import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.core.agent import StockAnalysisAgent
from agent.core.config import Config

async def test_streaming_flow():
    print("Initializing Agent...")
    from agent.core.config import Config, LLMConfig, SkillsConfig, AgentConfig, ServerConfig
    
    config = Config(
        llm=LLMConfig(api_key="dummy", api_base="http://dummy", model="gpt-4"),
        mcp_servers=[],
        skills=SkillsConfig(),
        agent=AgentConfig(),
        server=ServerConfig()
    )
    agent = StockAnalysisAgent(config)
    
    query = "Analyze NVDA stock"
    print(f"Starting stream run with query: {query}")
    
    try:
        async for event in agent.stream_run(query):
            print(f"Received Event: [{event.get('type')}] {event.get('agent')}: {event.get('content') or event.get('message')}")
            
            if event.get('type') == 'system_end':
                print("System end received.")
                break
            if event.get('type') == 'error':
                print(f"Error received: {event}")
                break
                
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_flow())
