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
    """Base class for lightweight specialized analysts with optional market snapshot context."""

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
            api_key = None  # Invalid placeholder

        # Prefer SiliconFlow if URL matches or if OpenAI key is invalid
        if "siliconflow" in (base_url or ""):
            api_key = silicon_key or api_key
        elif not api_key:
            # Fallback to SiliconFlow if OpenAI key is missing/invalid
            api_key = silicon_key

        if not api_key and silicon_key:
            api_key = silicon_key

        return ChatOpenAI(
            model=model_name, base_url=base_url, api_key=api_key, temperature=0.3
        )

    async def run(self, query: str, context_data: str = "", market_snapshot: Optional[str] = None) -> str:
        """Run the analyst logic."""
        logger.info(f"[{self.name}] analyzing: {query}")
        snapshot_block = f"\n\nMarket Snapshot:\n{market_snapshot}" if market_snapshot else ""
        try:
            messages = [
                SystemMessage(content=self.role_prompt),
                HumanMessage(content=f"Task: {query}\n\nData Context:\n{context_data}{snapshot_block}"),
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
            role_prompt="你是宏观经济分析师。你的任务是根据提供的经济数据（GDP, CPI, PMI等）分析当前经济周期和趋势。请言简意赅。",
        )

    async def analyze(self, market_snapshot: Optional[str] = None) -> str:
        # 1. Fetch Data
        try:
            # Parallel fetch of key indicators
            indicators = [
                "China GDP",
                "China CPI",
                "China PMI",
                "US CPI",
                "US Fed Funds",
            ]
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
        query = "分析当前宏观经济环境及其对市场的影响，结合指数温度/资金流/避险资产（若提供）。"
        return await self.run(query, context, market_snapshot=market_snapshot)


# --- 2. Market Analyst ---


class MarketAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="MarketAnalyst",
            role_prompt="你是市场策略分析师。根据板块资金流向和市场情绪，判断当前市场热点和风险。",
        )

    async def analyze(self, market_snapshot: Optional[str] = None) -> str:
        # 1. Fetch Data
        try:
            # Hot sectors
            from backend.app.services.market_service import market_service

            hot_sectors = await asyncio.to_thread(
                market_service.get_hot_sectors, 5, "industry"
            )
            cold_sectors = await asyncio.to_thread(
                market_service.get_cold_sectors, 5, "industry"
            )

            context = f"Hot Sectors: {hot_sectors}\nCold Sectors: {cold_sectors}"
        except Exception as e:
            context = f"Error fetching market data: {e}"

        # 2. Analyze
        query = "分析当前市场情绪和资金流向，输出行业/概念热冷榜与资金方向，结合指数温度与缺口（若有）。"
        return await self.run(query, context, market_snapshot=market_snapshot)


# --- 3. News Analyst ---


class NewsAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="NewsAnalyst",
            role_prompt="你是财经新闻分析师。根据搜索到的新闻，提炼对投资组合有重大影响的信息。",
        )

    async def analyze(self, query: str, market_snapshot: Optional[str] = None) -> str:
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
        task = f"总结关于'{query}'的关键新闻及其潜在影响，标注利好/利空、主体（个股/板块/指数），若数据缺口需说明。"
        return await self.run(task, context, market_snapshot=market_snapshot)


# --- 4. Technical Analyst ---


class TechnicalAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="TechnicalAnalyst",
            role_prompt="你是技术分析师。根据K线数据和指标，判断资产的趋势和关键支撑/阻力位。",
        )

    async def analyze(self, symbol: str, market_snapshot: Optional[str] = None) -> str:
        # 1. Fetch K-line & Indicators
        try:
            # Get recent history
            history = await asyncio.to_thread(
                registry.get_historical_data, symbol=symbol, period="30d"
            )
            # Get indicators (if registry supports, otherwise let LLM infer from OHLC)
            # registry.get_technical_indicators is not always available in base registry,
            # but tools.py in research uses it. Let's try or fallback to history.

            # Assuming history is list of dicts
            context = f"Recent History (Last 30 days):\n{str(history)[-2000:]}"  # Truncate to fit context
        except Exception as e:
            context = f"Error fetching technical data: {e}"

        # 2. Analyze
        return await self.run(
            f"分析 {symbol} 的技术走势，并结合所属板块/大盘温度提示趋势风险或背离。",
            context,
            market_snapshot=market_snapshot,
        )


# --- 5. Daily Review Analyst ---


class DailyReviewAnalyst(SpecializedAnalyst):
    def __init__(self):
        super().__init__(
            name="DailyReviewAnalyst",
            role_prompt="你是日内交易复盘分析师。根据今日分时走势和资金流向，判断主力意图和次日预期。",
        )

    async def analyze(self, symbol: str, market_snapshot: Optional[str] = None) -> str:
        # 1. Fetch Data
        try:
            # Intraday Data (30m candles for last 5 days to see trend)
            intraday = await asyncio.to_thread(
                registry.get_historical_data, symbol=symbol, period="5d", interval="30m"
            )

            # Fund Flow (Daily flow for last 10 days)
            fund_flow = await asyncio.to_thread(
                registry.get_stock_fund_flow, symbol=symbol
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
        return await self.run(
            f"复盘 {symbol} 今日走势及资金流向，标注板块/指数温度及缺口。",
            context,
            market_snapshot=market_snapshot,
        )

    async def analyze_portfolio_ops(self, symbols: List[str], portfolio: dict, market_snapshot: Optional[str] = None) -> str:
        """Generate portfolio-level actions based on intraday review + holdings context."""

        # 1. Fetch data for a few key symbols
        symbols = [s for s in (symbols or []) if s]
        symbols = symbols[:5]

        async def _fetch_one(sym: str):
            intraday = await asyncio.to_thread(
                registry.get_historical_data,
                symbol=sym,
                period="5d",
                interval="30m",
            )
            fund_flow = await asyncio.to_thread(
                registry.get_stock_fund_flow, symbol=sym
            )
            quote = await asyncio.to_thread(registry.get_stock_price, sym)
            return {
                "symbol": sym,
                "quote": quote,
                "intraday": intraday[-60:] if isinstance(intraday, list) else intraday,
                "fund_flow": fund_flow,
            }

        try:
            data = await asyncio.gather(*[_fetch_one(s) for s in symbols])
            holdings = (
                portfolio.get("assets", []) if isinstance(portfolio, dict) else []
            )
            holdings_trim = []
            for h in holdings:
                if not isinstance(h, dict):
                    continue
                holdings_trim.append(
                    {
                        "symbol": h.get("symbol"),
                        "name": h.get("name"),
                        "type": h.get("type"),
                        "quantity": h.get("quantity"),
                        "cost_basis": h.get("cost_basis"),
                        "current_price": h.get("current_price"),
                        "total_value": h.get("total_value"),
                    }
                )
            context = (
                "【组合持仓摘要】\n"
                + str(
                    {
                        "assets": holdings_trim[:12],
                        "cash_balance": portfolio.get("cash_balance", 0.0),
                    }
                )
                + "\n\n【关键标的日内/资金数据】\n"
                + str(data)
            )
        except Exception as e:
            context = f"Error fetching portfolio ops data: {e}"

        # 2. Analyze
        query = "基于组合持仓与关键标的的日内走势/资金流向，输出可执行的调仓与风控建议（包含仓位、触发条件、替代方案）。"
        return await self.run(query, context, market_snapshot=market_snapshot)
