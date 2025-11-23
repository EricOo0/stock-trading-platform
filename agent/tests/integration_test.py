import sys
import os
import asyncio
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config
from core.agent import StockAnalysisAgent

async def run_query(agent, query, case_name):
    logger.info(f"\n{'='*20} Running Case: {case_name} {'='*20}")
    logger.info(f"Query: {query}")
    
    try:
        response = await agent.run(query)
        
        if response["success"]:
            logger.info(f"Output: {response['output']}")
            logger.info(f"Intermediate Steps: {len(response['intermediate_steps'])}")
            for step in response['intermediate_steps']:
                logger.info(f"  - {step['agent']}: {step['content'][:100]}...")
            logger.info(f"✅ Case {case_name} completed successfully.")
        else:
            logger.error(f"❌ Case {case_name} failed: {response.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Case {case_name} failed with exception: {e}")

async def main():
    config = get_config()
    agent = StockAnalysisAgent(config)
    
    # Case 1: Stock Analysis (NVDA)
    await run_query(agent, "请全面分析一下英伟达 (NVDA) 的投资价值，包括近期新闻和技术面走势。", "NVDA Analysis")
    
    # Case 2: Macro Analysis (Fed & Gold)
    await run_query(agent, "最近美联储的利率政策对黄金价格有什么影响？", "Fed & Gold")
    
    # Case 3: Web Search (Stock Halt)
    await run_query(agent, "为什么最近这只股票停牌了：000001", "Stock Halt Search")

if __name__ == "__main__":
    asyncio.run(main())
