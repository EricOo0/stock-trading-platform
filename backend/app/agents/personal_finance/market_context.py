import json
import logging
import asyncio
import datetime
from typing import Optional, Dict, Any, List

from backend.infrastructure.market.akshare_tool import AkShareTool

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
        
        change = None
        suffix = ""
        
        # Priority 1: Percentage change
        pct_keys = ["change_pct", "change_percent", "percent", "涨跌幅"]
        for k in pct_keys:
            if item.get(k) is not None:
                change = item.get(k)
                suffix = "%"
                break
        
        # Priority 2: Absolute change (if no percentage)
        if change is None:
            amt_keys = ["change_amount", "涨跌额", "涨跌"]
            for k in amt_keys:
                if item.get(k) is not None:
                    change = item.get(k)
                    suffix = ""
                    break

        if price is not None and change is not None:
            lines.append(f"- {name}: {price} ({change}{suffix})")
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

    # A-Share Header Info Calculation
    # 1. Turnover
    turnover_data = context.get("market_turnover") or []
    turnover_str = "N/A"
    turnover_growth_str = ""
    if turnover_data and isinstance(turnover_data, list) and len(turnover_data) > 0:
        latest = turnover_data[0]
        # turnover is in raw unit (float). Display as Trillion/Billion.
        val = float(latest.get("turnover", 0))
        if val > 1000000000000:
            turnover_str = f"{val/1000000000000:.2f}万亿"
        else:
            turnover_str = f"{val/100000000:.2f}亿"
        
        # Growth
        if len(turnover_data) > 1:
            prev = turnover_data[1]
            prev_val = float(prev.get("turnover", 0))
            if prev_val > 0:
                growth = (val - prev_val) / prev_val * 100
                turnover_growth_str = f"较前日增长{growth:+.2f}%"
                prev_display = f"{prev_val/100000000:.2f}亿"
                if prev_val > 1000000000000:
                    prev_display = f"{prev_val/1000000000000:.2f}万亿"
                turnover_growth_str += f"(前日{prev_display})"

    # 2. Fund Flow
    fund_flow = context.get("fund_flow") or {}
    north_flow = fund_flow.get("north", [])
    south_flow = fund_flow.get("south", [])
    
    north_str = "北向资金 N/A"
    # if north_flow and len(north_flow) > 0:
    #     n_val = float(north_flow[0].get("value", 0))
    #     # Value unit check: AkShare usually returns 亿元 or 万元.
    #     # Assuming 亿元 for now based on typical output, need verification.
    #     # If it's raw, it might be large. Let's assume standard float.
    #     # AkShare stock_hsgt_north_net_flow_in_em unit is usually 亿元?
    #     # Actually standard akshare output often varies. Let's just display value with unit if possible.
    #     # Let's assume it is 亿元 (hundred million).
    #     direction = "流入" if n_val > 0 else "流出"
    #     north_str = f"北向资金{direction}{abs(n_val):.2f}亿"

    south_str = "南向资金 N/A"
    if south_flow and len(south_flow) > 0:
        s_val = float(south_flow[0].get("value", 0))
        direction = "流入" if s_val > 0 else "流出"
        south_str = f"南向资金{direction}{abs(s_val):.2f}亿"

    # Construct Header
    header_info = f"总成交额{turnover_str}"
    if turnover_growth_str:
        header_info += f"，{turnover_growth_str}"
    header_info += f"，{north_str}，{south_str}"

    sections.append("## 指数概览")
    
    indices = context.get("indices", {})
    if isinstance(indices, dict):
        # A-Share
        sections.append(f"### A股指数（{header_info}）")
        sections.extend(_format_index_items("", indices.get("A_Share", []))[1:]) # Skip title line from helper
        
        # HK
        sections.append(f"### 港股指数")
        sections.extend(_format_index_items("", indices.get("HK", []))[1:])
        
        # US
        sections.append(f"### 美股指数")
        sections.extend(_format_index_items("", indices.get("US", []))[1:])

    indices_history = context.get("indices_history") or {}
    if indices_history:
        sections.append("## 指数历史")
        for market, indices_data in indices_history.items():
            if indices_data:
                sections.append(f"### {market} 指数历史")
                for index_code, history in indices_data.items():
                    if history:
                        # Compact JSON representation
                        # Filter to only date, close, change_pct
                        compact_hist = []
                        for h in history:
                            compact_hist.append({
                                "date": h.get("date"),
                                "close": h.get("close"),
                                "change": f"{h.get('change_pct', 0):.2f}%"
                            })
                        sections.append(f"- {index_code}: {json.dumps(compact_hist, ensure_ascii=False)}")

    sectors = context.get("sectors") or []
    if sectors:
        sections.append("## 行业资金流向 (Top)")
        for item in sectors:
            name = item.get("名称") or item.get("name") or "Unknown"
            main_flow = (
                item.get("main_net_inflow")
                or item.get("主力净流入")
                or item.get("净流入")
                or item.get("flow_in")
            )
            main_flow_out = (
                    item.get("main_net_outflow")
                    or item.get("主力流出")
                    or item.get("流出")
                    or item.get("flow_out")
            )
            sections.append(f"- {name}: 主力净流入 {main_flow} , 主力流出 {main_flow_out}")

    macro = context.get("macro") or {}
    if macro:
        sections.append("## 宏观摘要")
        for key, value in macro.items():
            # Ensure JSON string format
            sections.append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")

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
            # source = item.get("source") or item.get("来源") or ""
            # pub_time = item.get("time") or item.get("datetime") or item.get("发布时间") or ""
            # Simple format for headlines
            sections.append(f"- {title}")

    errors = context.get("errors") or []
    if errors:
        sections.append("## 错误")
        for err in errors:
            sections.append(f"- {err}")

    return "\n".join(sections) if sections else ""


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
            "market_turnover": {},
            "fund_flow": {
                "north": [],
                "south": []
            },
            "sectors": [],
            "concepts": [],
            "macro": {},
            "errors": []
        }

        # 0. Market Turnover & Fund Flow
        try:
            # Turnover: fetch last 5 days
            turnover_hist = ak_tool.get_market_turnover(market="CN", 
                start_date=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d"))
            if isinstance(turnover_hist, list):
                context["market_turnover"] = turnover_hist
        except Exception as e:
            context["errors"].append(f"Market Turnover error: {str(e)}")

        try:
            # Fund Flow
            north_flow = ak_tool.get_fund_flow(target="", flow_type="north")
            south_flow = ak_tool.get_fund_flow(target="", flow_type="south")
            # Usually returns history list.
            context["fund_flow"]["north"] = north_flow[:5] if isinstance(north_flow, list) else []
            context["fund_flow"]["south"] = south_flow[:5] if isinstance(south_flow, list) else []
        except Exception as e:
            context["errors"].append(f"Fund Flow error: {str(e)}")

        # 1. A-Share Indices
        try:
            # Use unified get_indices_quote for key indices
            # get_indices_quote(market="CN") returns:
            # [{ "symbol": "000001", "name": "上证指数", "price": ..., "change_percent": ... }, ...]
            cn_indices = ak_tool.get_indices_quote(market="CN")
            
            # Filter for specific indices we want to display
            target_cn_indices = ["000001", "399001", "399006", "000300"]
            a_indices = []
            
            for item in cn_indices:
                if item.get("symbol") in target_cn_indices:
                    a_indices.append(item)
            
            # Sort by target list order
            a_indices.sort(key=lambda x: target_cn_indices.index(x.get("symbol")) if x.get("symbol") in target_cn_indices else 999)
            
            context["indices"]["A_Share"] = a_indices
        except Exception as e:
            context["errors"].append(f"A-Share Indices error: {str(e)}")

        # 2. HK Indices
        try:
            hk_indices = ak_tool.get_indices_quote(market="HK")
            target_hk_indices = ["HSI", "HSTECH"] # symbol returned by get_indices_quote for HK is usually the index code
            # Note: get_indices_quote for HK might return symbols like "HSI", "HSCEI", "HSTECH"
            
            hk_data = []
            for item in hk_indices:
                 if item.get("symbol") in target_hk_indices:
                    hk_data.append(item)
                    
            context["indices"]["HK"] = hk_data
        except Exception as e:
             context["errors"].append(f"HK Indices error: {str(e)}")

        # 3. US Indices
        try:
            us_indices = ak_tool.get_indices_quote(market="US")
            target_us_indices = [".IXIC", ".DJI", ".INX"]
            
            us_data = []
            for item in us_indices:
                if item.get("symbol") in target_us_indices:
                    us_data.append(item)
                    
            context["indices"]["US"] = us_data
        except Exception as e:
             context["errors"].append(f"US Indices error: {str(e)}")

        # 4. Indices History (Optional/Default)
        # Using a timeout or separate try block to avoid blocking main context if history is slow
        try:
            # We enable history by default for now as requested, limiting to 7 days
            # indices_history structure: { "CN": { "000001": [...] }, "HK": ..., "US": ... }
            context["indices_history"] = {
                "CN": ak_tool.get_indices_history("CN", days=7),
                "HK": ak_tool.get_indices_history("HK", days=7),
                "US": ak_tool.get_indices_history("US", days=7)
            }
        except Exception as e:
            context["errors"].append(f"Indices History error: {str(e)}")
            context["indices_history"] = {}

        # 5. Sectors (Top 5 Flow)
        try:
            sectors = ak_tool.get_board_info(board_type="industry", info_type="rank")

            context["sectors"] = sectors[:5] if sectors else []
        except Exception as e:
            context["errors"].append(f"Sector Flow error: {str(e)}")

        # 5. Concepts (Top 5 Flow)
        try:
            concepts = ak_tool.get_board_info(board_type="concept", info_type="rank")
            context["concepts"] = concepts[:5] if concepts else []
        except Exception as e:
            context["errors"].append(f"Concept Flow error: {str(e)}")

        # 6. Macro Summary
        macro_indicators = ["GDP", "CPI", "LPR","PPI"]
        for ind in macro_indicators:
            try:
                data = ak_tool.get_macro(ind)
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

if __name__ == "__main__":
    # export PYTHONPATH=$PYTHONPATH:. && python3 backend/app/agents/personal_finance/market_context.py
    import asyncio
    context = asyncio.run(get_market_context(as_markdown=True))
    print(context["markdown"])
