import json
import logging
import asyncio
import datetime
from typing import Optional, Dict, Any, List

from backend.infrastructure.market._akshare import AkShareTool
from backend.app.agents.personal_finance.sub_agents import (
    MacroAnalyst,
    MarketAnalyst,
    NewsAnalyst,
    TechnicalAnalyst,
    DailyReviewAnalyst,
)

logger = logging.getLogger(__name__)

def _stringify_value(value: Any) -> str:
    """
    Convert value to string while handling dict/list gracefully.
    """
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def _format_index_items(title: str, items: List[Dict[str, Any]]) -> List[str]:
    """
    Format index entries into markdown bullet lines.
    """
    if not items:
        return []
    lines = [f"### {title}"]
    for item in items:
        name = (
            item.get("name")
            or item.get("名称")
            or item.get("index")
            or item.get("symbol")
            or "Unknown"
        )
        price = (
            item.get("最新价")
            or item.get("close")
            or item.get("最新")
            or item.get("price")
            or item.get("当前价")
        )
        change = (
            item.get("涨跌幅")
            or item.get("change_percent")
            or item.get("percent")
            or item.get("涨跌额")
            or item.get("涨跌")
        )
        if price is not None and change is not None:
            lines.append(f"- {name}: {price} ({change})")
        elif price is not None:
            lines.append(f"- {name}: {price}")
        else:
            lines.append(f"- {name}: {_stringify_value(item)}")
    return lines


# Function: render_market_context_markdown
def render_market_context_markdown(context: Dict[str, Any]) -> str:
    """
    Render market context dictionary to a readable markdown string.
    """
    sections: List[str] = []

    timestamp = context.get("timestamp")
    if timestamp:
        sections.append("## 时间戳")
        sections.append(f"- {timestamp}")

    indices = context.get("indices", {})
    if isinstance(indices, dict):
        index_lines: List[str] = []
        index_lines.extend(_format_index_items("A股指数", indices.get("A_Share", [])))
        index_lines.extend(_format_index_items("港股指数", indices.get("HK", [])))
        index_lines.extend(_format_index_items("美股指数", indices.get("US", [])))
        if index_lines:
            sections.append("## 指数概览")
            sections.extend(index_lines)

    sectors = context.get("sectors") or []
    if sectors:
        sections.append("## 行业资金流向 (Top)")
        for item in sectors:
            name = item.get("名称") or item.get("name") or "Unknown"
            main_flow = (
                item.get("main_net_inflow")
                or item.get("主力净流入")
                or item.get("净流入")
            )
            if main_flow is not None:
                sections.append(f"- {name}: 主力净流入 {main_flow}")
            else:
                sections.append(f"- {name}: {_stringify_value(item)}")

    concepts = context.get("concepts") or []
    if concepts:
        sections.append("## 概念资金流向 (Top)")
        for item in concepts:
            name = item.get("名称") or item.get("name") or "Unknown"
            main_flow = (
                item.get("main_net_inflow")
                or item.get("主力净流入")
                or item.get("净流入")
            )
            if main_flow is not None:
                sections.append(f"- {name}: 主力净流入 {main_flow}")
            else:
                sections.append(f"- {name}: {_stringify_value(item)}")

    macro = context.get("macro") or {}
    if macro:
        sections.append("## 宏观摘要")
        for key, value in macro.items():
            sections.append(f"- {key}: {_stringify_value(value)}")

    calendar = context.get("calendar") or []
    if calendar:
        sections.append("## 经济日历")
        for event in calendar:
            title = (
                event.get("event")
                or event.get("title")
                or event.get("indicator")
                or "事件"
            )
            time_str = event.get("time") or event.get("datetime") or ""
            importance = event.get("importance")
            importance_text = f"(重要度 {importance})" if importance is not None else ""
            sections.append(f"- {title} {importance_text} {time_str}".strip())

    news = context.get("news") or []
    if news:
        sections.append("## 头条新闻")
        for item in news:
            title = item.get("title") or item.get("名称") or "新闻"
            source = item.get("source") or item.get("来源") or ""
            pub_time = item.get("time") or item.get("datetime") or item.get("发布时间") or ""
            meta = " - ".join(filter(None, [source, pub_time]))
            if meta:
                sections.append(f"- {title} ({meta})")
            else:
                sections.append(f"- {title}")

    errors = context.get("errors") or []
    if errors:
        sections.append("## 错误")
        for err in errors:
            sections.append(f"- {err}")

    return "\n".join(sections) if sections else ""


async def run_macro_analysis(session_id: str = "default", market_snapshot: Optional[str] = None) -> str:
    """
    Runs the Macro Analyst (independent sub-agent) and returns the analysis.
    """
    logger.info("Starting Macro Analysis Sub-task...")
    try:
        analyst = MacroAnalyst()
        result = await analyst.analyze(market_snapshot=market_snapshot)
        return result
    except Exception as e:
        logger.error(f"Failed to run macro analysis: {e}")
        return f"Error running macro analysis: {str(e)}"


async def run_market_analysis(market_snapshot: Optional[str] = None) -> str:
    """
    Runs the Market Analyst (independent sub-agent) and returns the analysis.
    """
    logger.info("Starting Market Analysis Sub-task...")
    try:
        analyst = MarketAnalyst()
        result = await analyst.analyze(market_snapshot=market_snapshot)
        return result
    except Exception as e:
        logger.error(f"Failed to run market analysis: {e}")
        return f"Error running market analysis: {str(e)}"


async def run_technical_analysis(symbol: str, session_id: str = "default", market_snapshot: Optional[str] = None) -> str:
    """
    Runs the Technical Analyst (independent sub-agent) for a specific symbol.
    IMPORTANT: 'symbol' MUST be a valid stock code (e.g., 'sh600519', 'sz000001', '00700', 'AAPL'), NOT a company name.
    """
    logger.info(f"Starting Technical Analysis Sub-task for {symbol}...")
    try:
        analyst = TechnicalAnalyst()
        result = await analyst.analyze(symbol, market_snapshot=market_snapshot)
        return result
    except Exception as e:
        logger.error(f"Failed to run technical analysis for {symbol}: {e}")
        return f"Error running technical analysis for {symbol}: {str(e)}"


async def run_news_analysis(query: str, session_id: str = "default", market_snapshot: Optional[str] = None) -> str:
    """
    Runs the News Analyst (independent sub-agent) for a specific query.
    """
    logger.info(f"Starting News Analysis Sub-task for query: {query}...")
    try:
        analyst = NewsAnalyst()
        result = await analyst.analyze(query, market_snapshot=market_snapshot)
        return result
    except Exception as e:
        logger.error(f"Failed to run news analysis: {e}")
        return f"Error running news analysis: {str(e)}"


async def run_daily_review_analysis(symbol: str, session_id: str = "default", market_snapshot: Optional[str] = None) -> str:
    """
    Runs the Daily Review Analyst (independent sub-agent) for a specific symbol.
    IMPORTANT: 'symbol' MUST be a valid stock code (e.g., 'sh600519', 'sz000001', '00700', 'AAPL'), NOT a company name.
    """
    logger.info(f"Starting Daily Review Analysis Sub-task for {symbol}...")
    try:
        analyst = DailyReviewAnalyst()
        result = await analyst.analyze(symbol, market_snapshot=market_snapshot)
        return result
    except Exception as e:
        logger.error(f"Failed to run daily review analysis for {symbol}: {e}")
        return f"Error running daily review analysis for {symbol}: {str(e)}"


# Function: get_market_context
# Complexity: O(N) - Multiple API calls to gather market context
async def get_market_context(include_history: bool = False, as_markdown: bool = False) -> Dict[str, Any]:
    """
    Get market context information including:
    - Current timestamp
    - Major indices (A-share, HK, US)
    - Sector/Concept fund flow (Top 5)
    - Macro summary (GDP, CPI, PMI)
    """
    logger.info("Gathering Market Context...")

    loop = asyncio.get_running_loop()

    def _fetch_data():
        ak_tool = AkShareTool()
        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "indices": {
                "A_Share": [],
                "HK": [],
                "US": []
            },
            "sectors": [],
            "concepts": [],
            "macro": {},
            "errors": []
        }

        # 1. A-Share Indices
        try:
            context["indices"]["A_Share"] = ak_tool.get_a_share_indices_spot()
        except Exception as e:
            context["errors"].append(f"A-Share Indices error: {str(e)}")

        # 2. HK Indices
        hk_data = []
        for symbol, name in [("HSI", "恒生指数"), ("HSTECH", "恒生科技")]:
            last = ak_tool.get_hk_index_latest(symbol=symbol, name=name)
            if last and "error" not in last:
                hk_data.append(last)
        context["indices"]["HK"] = hk_data

        # 3. US Indices
        us_data = []
        for symbol, name in [(".IXIC", "纳斯达克"), (".DJI", "道琼斯"), (".INX", "标普500")]:
            last = ak_tool.get_us_index_latest(symbol=symbol, name=name)
            if last and "error" not in last:
                us_data.append(last)
        context["indices"]["US"] = us_data

        # 4. Sectors (Top 5 Flow)
        try:
            # Use AkShareTool method
            sectors = ak_tool.get_sector_fund_flow_rank()
            context["sectors"] = sectors[:5] if sectors else []
        except Exception as e:
            context["errors"].append(f"Sector Flow error: {str(e)}")

        # 5. Concepts (Top 5 Flow)
        try:
            concepts = ak_tool.get_concept_fund_flow_rank()
            context["concepts"] = concepts[:5] if concepts else []
        except Exception as e:
            context["errors"].append(f"Concept Flow error: {str(e)}")

        # 6. Macro Summary
        # Fetching latest of each
        macro_indicators = ["GDP", "CPI", "PMI"]
        for ind in macro_indicators:
            try:
                data = ak_tool.get_macro_data(ind)
                if "error" not in data:
                    context["macro"][ind] = data
            except Exception as e:
                pass

        # 7. Economic Calendar (Today + Tomorrow)
        try:
            today = datetime.datetime.now()
            tomorrow = today + datetime.timedelta(days=1)
            
            events_today = ak_tool.get_economic_calendar(today.strftime("%Y%m%d"))
            events_tomorrow = ak_tool.get_economic_calendar(tomorrow.strftime("%Y%m%d"))
            
            context["calendar"] = []
            sorted_events_today = sorted(events_today, key=lambda x: x.get("importance", 0), reverse=True)
            sorted_events_tomorrow = sorted(events_tomorrow, key=lambda x: x.get("importance", 0), reverse=True)

            for i,event in enumerate(sorted_events_today):
                if i>5:
                    break
                context["calendar"].append(event)
            for i,event in enumerate(sorted_events_tomorrow):
                if i>5:
                    break
                context["calendar"].append(event)
        except Exception as e:
            context["errors"].append(f"Calendar error: {str(e)}")

        # 8. Headline News (Top 5)
        try:
            news_list = ak_tool.get_headline_news(limit=5)
            context["news"] = news_list
        except Exception as e:
            context["errors"].append(f"News error: {str(e)}")

        return context

    context = await loop.run_in_executor(None, _fetch_data)

    if as_markdown:
        context["markdown"] = render_market_context_markdown(context)

    return context
