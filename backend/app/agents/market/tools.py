from langchain_core.tools import tool
from typing import List, Dict, Any
import logging
from backend.app.registry import Tools
from backend.app.services.market_service import market_service

logger = logging.getLogger(__name__)
tools_registry = Tools()

@tool
def get_market_news(query: str = "A股 市场热点 政策利好 行业动态") -> str:
    """
    Search for the latest market news, hot topics, and policy updates.
    Useful for analyzing market catalysts and news-driven events.
    """
    try:
        results = tools_registry.search_market_news(query=query, topic="news")
        if not results:
            return "暂无最新市场新闻。"
        
        formatted_news = []
        for item in results[:5]:
            title = item.get('title', 'No Title')
            snippet = item.get('content', '')[:150] + "..."
            formatted_news.append(f"- **{title}**: {snippet}")
        return "\n".join(formatted_news)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return f"获取新闻失败: {str(e)}"

@tool
def get_macro_data(indicators: List[str] = ["china pmi", "us10y", "dxy"]) -> str:
    """
    Get key macroeconomic indicators. 
    Default indicators: China PMI, US 10Y Treasury Yield, Dollar Index (DXY).
    Useful for analyzing the macro environment (liquidity, economic cycle).
    """
    try:
        results = []
        for ind in indicators:
            res = tools_registry.get_macro_data(ind)
            if res and "data" in res and res["data"]:
                latest = res["data"][-1]
                val = latest.get("value", "N/A")
                date = latest.get("date", "N/A")
                results.append(f"- {ind.upper()}: {val} ({date})")
            else:
                results.append(f"- {ind.upper()}: N/A")
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Error fetching macro data: {e}")
        return f"获取宏观数据失败: {str(e)}"

@tool
def get_market_fund_flow() -> str:
    """
    Get the capital flow of hot and cold sectors (Industries and Concepts).
    Also returns top leading stocks for the top 3 hot industries.
    Useful for analyzing market fund direction, sector rotation, and finding top picks.
    """
    try:
        hot_ind = market_service.get_hot_sectors(limit=5, sector_type="industry")
        cold_ind = market_service.get_cold_sectors(limit=5, sector_type="industry")
        hot_con = market_service.get_hot_sectors(limit=5, sector_type="concept")
        
        # Get details for top 3 hot industries
        hot_ind_details = []
        for sector in hot_ind[:3]:
            name = sector['name']
            details = market_service.get_sector_details(name, limit=3)
            stocks_str = ""
            if details and "stocks" in details:
                stocks = details["stocks"]
                stocks_str = ", ".join([f"{s['name']}({s['symbol']})" for s in stocks])
            hot_ind_details.append(f"{name} [Top Stocks: {stocks_str}]")

        # Fallback for others
        remaining_hot_ind = [s['name'] for s in hot_ind[3:]]
        
        cold_ind_str = ", ".join([f"{s['name']}" for s in cold_ind])
        hot_con_str = ", ".join([f"{s['name']}" for s in hot_con])
        
        hot_ind_str = "\n".join([f"- {s}" for s in hot_ind_details])
        if remaining_hot_ind:
            hot_ind_str += f"\n- 其他热门: {', '.join(remaining_hot_ind)}"

        return f"""
        **资金流向 (Capital Flow)**:
        
        **热门行业及龙头股 (Hot Industries & Top Stocks)**:
        {hot_ind_str}
        
        **冷门行业 (Cold Industries)**: {cold_ind_str}
        
        **热门概念 (Hot Concepts)**: {hot_con_str}
        """
    except Exception as e:
        logger.error(f"Error fetching fund flow: {e}")
        return f"获取资金流向数据失败: {str(e)}"

tools = [get_market_news, get_macro_data, get_market_fund_flow]
