import sys
import os
import asyncio
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config
from core.agent import StockAnalysisAgent

async def test_agent_initialization():
    """Test that the agent and graph can be initialized."""
    try:
        logger.info("Testing Agent Initialization...")
        config = get_config()
        agent = StockAnalysisAgent(config)
        logger.info("✅ Agent initialized successfully")
        
        if agent.graph:
            logger.info("✅ Graph compiled successfully")
            # Print graph structure representation if possible
            logger.info(f"Graph nodes: {agent.graph.nodes.keys() if hasattr(agent.graph, 'nodes') else 'N/A'}")
        else:
            logger.error("❌ Graph is None")
            
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        raise

async def main():
    await test_agent_initialization()

if __name__ == "__main__":
    asyncio.run(main())
