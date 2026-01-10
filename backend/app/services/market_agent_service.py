import logging
import json
from typing import AsyncGenerator
from backend.app.agents.market.agent import run_market_agent

logger = logging.getLogger(__name__)

class MarketAgentService:
    def __init__(self):
        pass

    async def analyze_outlook_stream(self) -> AsyncGenerator[str, None]:
        """
        Delegate analysis to MarketAnalysisAgent (Refactored).
        """
        # Yield initial status
        yield json.dumps({"type": "status", "content": "正在启动市场分析智能体..."}) + "\n"
        
        try:
            async for chunk in run_market_agent(user_id="default"):
                # Wrap content in JSON for frontend compatibility
                msg = {"type": "agent_response", "content": chunk}
                yield json.dumps(msg, ensure_ascii=False) + "\n"
                
        except Exception as e:
            logger.error(f"Error in market agent: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": f"分析失败: {str(e)}"}) + "\n"

market_agent_service = MarketAgentService()
