import asyncio
import logging
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from backend.app.registry import Tools
from backend.infrastructure.config.loader import config

logger = logging.getLogger(__name__)

# Registry for data fetching
registry = Tools()

# --- Specialized Analyst Definitions ---

class SpecializedAnalyst:
    """Base class for lightweight specialized analysts."""
    def __init__(self, name: str, role_prompt: str):
        self.name = name
        self.role_prompt = role_prompt
        self.llm = self._get_llm()

    def _get_llm(self):
        # Use cheaper/faster model for sub-agents if possible, or same as master
        model_name = config.get("model", "gpt-4o")
        base_url = config.get("api_url")
        
        openai_key = config.get_api_key("openai")
        silicon_key = config.get_api_key("siliconflow")
        
        # Logic to select valid key
        api_key = openai_key
        
        # Check if OpenAI key is placeholder
        if openai_key and openai_key.startswith("sk-") and "xxxx" in openai_key:
            api_key = None # Invalid placeholder
            
        # Prefer SiliconFlow if URL matches or if OpenAI key is invalid
        if "siliconflow" in (base_url or ""):
            api_key = silicon_key or api_key
        elif not api_key:
            # Fallback to SiliconFlow if OpenAI key is missing/invalid
            api_key = silicon_key
            
        if not api_key and silicon_key:
            api_key = silicon_key
        
        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key,
            temperature=0.3
        )

    async def run(self, query: str, context_data: str = "") -> str:
        """Run the analyst logic."""
        logger.info(f"[{self.name}] analyzing: {query}")
        try:
            messages = [
                SystemMessage(content=self.role_prompt),
                HumanMessage(content=f"Task: {query}\n\nData Context:\n{context_data}")
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"[{self.name}] failed: {e}")
            return f"Error in {self.name}: {str(e)}"

# --- 1. Macro Analyst ---

class MacroAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="MacroAnalyst", 
            role_prompt="你是宏观经济分析师。你的任务是根据提供的经济数据（GDP, CPI, PMI等）分析当前经济周期和趋势。请言简意赅。"
        )

    async def analyze(self) -> str:
        # 1. Fetch Data
        try:
            # Parallel fetch of key indicators
            indicators = ["China GDP", "China CPI", "China PMI", "US CPI", "US Fed Funds"]
            # Use asyncio.to_thread for blocking registry calls
            # registry.get_macro_data(q)
            results = {}
            for ind in indicators:
                data = await asyncio.to_thread(registry.get_macro_data, ind)
                results[ind] = data
            
            context = str(results)
        except Exception as e:
            context = f"Error fetching macro data: {e}"

        # 2. Analyze
        return await self.run("分析当前宏观经济环境及其对市场的影响。", context)

# --- 2. Market Analyst ---

class MarketAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="MarketAnalyst",
            role_prompt="你是市场策略分析师。根据板块资金流向和市场情绪，判断当前市场热点和风险。"
        )

    async def analyze(self) -> str:
        # 1. Fetch Data
        try:
            # Hot sectors
            from backend.app.services.market_service import market_service
            hot_sectors = await asyncio.to_thread(market_service.get_hot_sectors, 5, 'industry')
            cold_sectors = await asyncio.to_thread(market_service.get_cold_sectors, 5, 'industry')
            
            context = f"Hot Sectors: {hot_sectors}\nCold Sectors: {cold_sectors}"
        except Exception as e:
            context = f"Error fetching market data: {e}"

        # 2. Analyze
        return await self.run("分析当前市场情绪和资金流向。", context)

# --- 3. News Analyst ---

class NewsAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="NewsAnalyst",
            role_prompt="你是财经新闻分析师。根据搜索到的新闻，提炼对投资组合有重大影响的信息。"
        )

    async def analyze(self, query: str) -> str:
        # 1. Search News
        try:
            # Use registry search
            results = await asyncio.to_thread(
                registry.search_market_news, query=query, limit=5
            )
            context = str(results)
        except Exception as e:
            context = f"Error searching news: {e}"

        # 2. Analyze
        return await self.run(f"总结关于'{query}'的关键新闻及其潜在影响。", context)

# --- 4. Technical Analyst ---

class TechnicalAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="TechnicalAnalyst",
            role_prompt="你是技术分析师。根据K线数据和指标，判断资产的趋势和关键支撑/阻力位。"
        )

    async def analyze(self, symbol: str) -> str:
        # 1. Fetch K-line & Indicators
        try:
            # Get recent history
            history = await asyncio.to_thread(registry.get_historical_data, symbol=symbol, period="30d")
            # Get indicators (if registry supports, otherwise let LLM infer from OHLC)
            # registry.get_technical_indicators is not always available in base registry, 
            # but tools.py in research uses it. Let's try or fallback to history.
            
            # Assuming history is list of dicts
            context = f"Recent History (Last 30 days):\n{str(history)[-2000:]}" # Truncate to fit context
        except Exception as e:
            context = f"Error fetching technical data: {e}"

        # 2. Analyze
        return await self.run(f"分析 {symbol} 的技术走势。", context)

# --- 5. Daily Review Analyst ---

class DailyReviewAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="DailyReviewAnalyst",
            role_prompt="你是日内交易复盘分析师。根据今日分时走势和资金流向，判断主力意图和次日预期。"
        )

    async def analyze(self, symbol: str) -> str:
        # 1. Fetch Data
        try:
            # Intraday Data (30m candles for last 5 days to see trend)
            intraday = await asyncio.to_thread(
                registry.get_historical_data, 
                symbol=symbol, 
                period="5d", 
                interval="30m"
            )
            
            # Fund Flow (Daily flow for last 10 days)
            fund_flow = await asyncio.to_thread(
                registry.get_stock_fund_flow, 
                symbol=symbol
            )
            
            context = f"""
            Intraday Data (Last 5 days, 30m candles):
            {str(intraday)[-2000:]}
            
            Fund Flow Data (Last 10 days):
            {str(fund_flow)}
            """
        except Exception as e:
            context = f"Error fetching daily review data: {e}"

        # 2. Analyze
        return await self.run(f"复盘 {symbol} 今日走势及资金流向。", context)

