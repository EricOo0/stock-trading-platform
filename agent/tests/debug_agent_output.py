import sys
import os
import asyncio
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config
from core.agent import StockAnalysisAgent

async def debug_agent_output():
    config = get_config()
    agent = StockAnalysisAgent(config)
    
    query = "请分析000001(Ping An Bank Co., Ltd.)的投资价值和风险"
    logger.info(f"Running query: {query}")
    
    try:
        response = await agent.run(query)
        logger.info("Response received.")
        
        intermediate_steps = response.get("intermediate_steps", [])
        logger.info(f"Intermediate steps count: {len(intermediate_steps)}")
        
        for i, step in enumerate(intermediate_steps):
            logger.info(f"Step {i}: {step}")
            if isinstance(step, dict):
                logger.info(f"  Keys: {list(step.keys())}")
                logger.info(f"  Agent: {step.get('agent')}")
            else:
                logger.info(f"  Type: {type(step)}")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent_output())
