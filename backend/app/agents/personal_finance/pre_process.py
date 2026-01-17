from __future__ import annotations

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from backend.app.agents.personal_finance.llm import get_llm
from backend.app.agents.personal_finance.market_context import get_market_context
from backend.app.agents.personal_finance.task_schemas import (
    LessonItem,
    PreContext,
    DecisionReviewResult,
)
from backend.app.agents.personal_finance.utils import (
    safe_json_extract,
    extract_response_content,
    summarize_portfolio,
)
from backend.app.agents.personal_finance.prompts import (
    PREPROCESS_SYSTEM_PROMPT,
    PREPROCESS_USER_PROMPT_TEMPLATE,
)
from backend.app.agents.personal_finance.repository import PersonalFinanceRepository
from backend.app.registry import Tools
from backend.app.agents.personal_finance.db_models import DecisionRecord, LessonRecord

logger = logging.getLogger(__name__)


def _render_precontext_markdown(pre: PreContext, portfolio: Optional[Dict[str, Any]] = None) -> str:
    """Render a readable markdown summary for downstream agents."""
    lines: List[str] = []
    lines.append("# Pre Context")

    # 0. Portfolio Summary
    if portfolio:
        lines.append("\n## 投资组合摘要 (Portfolio)")
        
        # Display Total Equity and Market Value if available
        total_equity = portfolio.get("total_equity")
        total_market_value = portfolio.get("total_market_value")
        cash_balance = portfolio.get("cash_balance", 0.0)
        
        if total_equity is not None:
             lines.append(f"- 总资产净值: {total_equity}")
             lines.append(f"- 持仓总市值: {total_market_value}")
        
        lines.append(f"- 现金余额: {cash_balance}")
        
        assets = portfolio.get("assets", [])
        if assets:
            lines.append("- 持仓明细:")
            # Use a compact table or list format
            for a in assets:
                profit_loss = ""
                try:
                    curr = float(a.get('current_price') or 0)
                    cost = float(a.get('cost_basis') or 0)
                    qty = float(a.get('quantity') or 0)
                    if cost > 0 and qty > 0:
                        pct = ((curr - cost) / cost) * 100
                        icon = "🔺" if pct > 0 else "🔻"
                        profit_loss = f" ({icon}{pct:.1f}%)"
                except:
                    pass
                
                lines.append(
                    f"  - **{a.get('symbol')}** ({a.get('name')}): "
                    f"股数={a.get('quantity')}, 当前价格={a.get('current_price')} 成本价={a.get('cost_basis')}{profit_loss}, "
                    f"总市值={a.get('total_value')}"
                )
        else:
            lines.append("- 无持仓资产")

    # 1. Decision Review
    if pre.review_results:
        lines.append("\n## 决策复盘 (Decision Review)")
        for res in pre.review_results:
            icon = "✅" if res.is_correct else "❌"
            lines.append(f"### {icon} {res.symbol} ({res.original_action})")
            lines.append(
                f"- 原始价格: {res.original_price} -> 当前价格: {res.current_price}"
            )
            lines.append(f"- 归因: {res.reason}")
    else:
        lines.append("\n## 决策复盘")
        lines.append("(无活跃历史决策)")

    # 2. Reminders
    lines.append("\n## 重要提醒 (Reminders)")
    if pre.reminders:
        for r in pre.reminders:
            lines.append(f"- {r}")
    else:
        lines.append("(无)")

    # 3. Lessons (Historical Validation)
    if pre.lessons:
        lines.append("\n## 历史经验 (Lessons)")
        for it in pre.lessons:
            lines.append(f"- **{it.title}**: {it.description}")
    return "\n".join(lines)

# 1.2 DB Queries using Repository
def _fetch_db_data(user_id: str, portfolio: Optional[Dict[str, Any]] = None) :
    repo = PersonalFinanceRepository()
    try:
        active_decisions = repo.get_active_decisions(user_id)
        db_lessons = repo.get_lessons(user_id)
        port_data = None
        if not portfolio:
            port_data = repo.get_portfolio(user_id)
        return active_decisions, db_lessons, port_data
    except Exception as e:
        logger.warning(f"Failed to retrieve DB data: {e}")
        return [], [], None
class PreProcessAgent:
    """
    Pre-process agent that builds structured PreContext for Master Agent.
    Capabilities:
    1. Summarize market context.
    2. Review historical decisions (Active Decision Records).
    3. Generate precautions based on portfolio.
    """
    
    def __init__(self):
        self.repo = PersonalFinanceRepository()

    def _create_tools(self) -> List[Any]:
        # Initialize registry Tools
        registry = Tools()

        @tool
        def get_stock_price(symbol: str) -> str:
            """Get real-time price info for a stock/index (e.g. 600036, 00700, AAPL, .DJI). Returns dict as string."""
            try:
                # Use registry to get stock price
                return str(registry.get_stock_price(symbol))
            except Exception as e:
                return f"Error fetching price for {symbol}: {e}"

        @tool
        def search_news(query: str) -> str:
            """Search for recent news about a stock or topic. Returns list of news items as string."""
            try:
                # Use registry to search news
                results = registry.search_market_news(query, limit=5)
                # Simplify output to save tokens
                simple_results = [
                    {
                        "title": r.get("title", ""),
                        "date": r.get("published_date", ""),
                        "content": r.get("body", r.get("content", ""))[:200],
                    }
                    for r in results
                ]
                return str(simple_results)
            except Exception as e:
                return f"Error searching news for {query}: {e}"

        return [get_stock_price, search_news]

    async def run(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        portfolio: Optional[Dict[str, Any]] = None,
    ) -> PreContext:
        llm = get_llm(temperature=0.2)
        tools = self._create_tools()

        # 1. Internal Data Gathering (Market, Memory, Portfolio, Decisions)

        # 1.1 Market Context (Async)
        market_task = asyncio.create_task(get_market_context(as_markdown=True))

        # 1.2 DB Queries using Repository
        db_decisions, db_lessons, db_portfolio = await asyncio.to_thread(_fetch_db_data, user_id, portfolio)
        
        # Use provided portfolio or fallback to DB
        final_portfolio = portfolio or db_portfolio or {}
        
        market_context = await market_task

        # 2. Decision Records Preparation
        decisions_text = "无活跃决策记录。"
        if db_decisions:
            lines = ["待复盘决策列表:"]
            for d in db_decisions:
                lines.append(
                    f"- ID:{d.id}, Symbol:{d.symbol}, Action:{d.action}, "
                    f"Price:{d.price_at_suggestion}, Reason:{d.reasoning}, Time:{d.created_at}"
                )
            decisions_text = "\n".join(lines)
        # 3. Lessons (Historical Validation) Preparation
        lessons_text = "无历史经验。"
        if db_lessons:
            l_lines = ["历史经验列表:"]
            for l in db_lessons:
                l_lines.append(f"- {l.title}: {l.description} (conf:{l.confidence})")
            lessons_text = "\n".join(l_lines)

        # 4. 持仓报告
        portfolio_json = summarize_portfolio(final_portfolio)
        portfolio_str = json.dumps(
            portfolio_json, ensure_ascii=False, default=str
        )
        # 5. Market Context Parsing
        market_md = ""
        if market_context and "markdown" in market_context:
            market_md = market_context["markdown"]
        else:
            market_md = (
                market_context.get("markdown", "")
                if isinstance(market_context, dict)
                else ""
            )

        # 6. Input Prompt
        prompt = PREPROCESS_USER_PROMPT_TEMPLATE.format(
            user_query=user_query,
            decisions_text=decisions_text,
            lessons_text=lessons_text,
            portfolio_str=portfolio_str,
            market_md=market_md
        )
        print(f"Prompt: {prompt}")
        # Create Agent
        agent = create_agent(model=llm, tools=tools, system_prompt=PREPROCESS_SYSTEM_PROMPT)

        # 6. Execution
        try:
            logger.info(f"[PreProcess] Raw LLM req: {prompt[:200]}...") # Truncated log

            resp = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
            
            content = extract_response_content(resp)
            data = safe_json_extract(content) or {}
            if not data:
                logger.warning(f"[PreProcess] JSON extraction failed or returned empty. Raw content: {content}")
        except Exception as e:
            logger.error(f"[PreProcess] Agent execution failed: {e}")
            data = {}

        # 7. Parse Output
        # Review Results
        review_results: List[DecisionReviewResult] = []
        raw_reviews = data.get("review_results") or []
        for r in raw_reviews:
            try:
                review_results.append(DecisionReviewResult(**r))
            except Exception as e:
                logger.warning(f"[PreProcess] Failed to parse review result: {e}")

        # Reminders
        reminders = data.get("reminders") or []

        # Lessons (Historical Validation)
        lessons: List[LessonItem] = []
        # We assume LLM returns the FULL updated list
        lessons_block = data.get("lessons") or {}
        items = lessons_block.get("items") or []
        for it in items:
            if isinstance(it, dict) and it.get("title"):
                lessons.append(LessonItem(**it))

        # 8. Construct Result
        pre = PreContext(
            query=user_query,
            review_results=review_results,
            reminders=reminders,
            lessons=lessons,
        )

        pre.rendered_market_context_markdown = market_md
        pre.rendered_pre_context_markdown = _render_precontext_markdown(pre, portfolio_json)

        logger.info(
            f"[PreProcess] Completed. precontext: {pre.rendered_pre_context_markdown}"
        )
        return pre
if __name__ == "__main__":
    # 测试用主函数
    # export PYTHONPATH=$PYTHONPATH:. && python3 backend/app/agents/personal_finance/pre_process.py
    async def main():
        # 1.1 Market Context (Async)
        # 启动市场数据任务（它会立即在后台 Event Loop 中开始运行）
        # market_task = asyncio.create_task(get_market_context(as_markdown=True))
        #
        # # 1.2 DB Queries using Repository
        # # 并发运行 DB 查询（使用 await 等待线程结果，此时 market_task 也在后台跑）
        # # 注意：这里加了 await，才能拿到 _fetch_db_data 返回的三个值
        # db_decisions, db_lessons, db_portfolio = await asyncio.to_thread(_fetch_db_data, "default_user")
        #
        # # 3. 等待市场数据任务完成并获取结果
        # market_context = await market_task
        #
        # # 2. Market Context Parsing
        # market_md = ""
        # if market_context and "markdown" in market_context:
        #     market_md = market_context["markdown"]
        # else:
        #     market_md = (
        #         market_context.get("markdown", "")
        #         if isinstance(market_context, dict)
        #         else ""
        #     )
        #
        # # 3. Decision Records Preparation
        # decisions_text = "无活跃决策记录。"
        # if db_decisions:
        #     lines = ["待复盘决策列表:"]
        #     for d in db_decisions:
        #         lines.append(
        #             f"- ID:{d.id}, Symbol:{d.symbol}, Action:{d.action}, "
        #             f"Price:{d.price_at_suggestion}, Reason:{d.reasoning}, Time:{d.created_at}"
        #         )
        #     decisions_text = "\n".join(lines)
        # lessons_text = "无历史经验。"
        # if db_lessons:
        #     l_lines = ["历史经验列表:"]
        #     for l in db_lessons:
        #         l_lines.append(f"- {l.title}: {l.description} (conf:{l.confidence})")
        #     lessons_text = "\n".join(l_lines)
        #
        # # 4. 持仓报告
        # portfolio_json = summarize_portfolio(db_portfolio)
        # portfolio_str = json.dumps(
        #     portfolio_json, ensure_ascii=False, default=str
        # )
        #
        # # 5. Market Context Parsing
        # market_md = ""
        # if market_context and "markdown" in market_context:
        #     market_md = market_context["markdown"]
        # else:
        #     market_md = (
        #         market_context.get("markdown", "")
        #         if isinstance(market_context, dict)
        #         else ""
        #     )
        #
        # # 6. Input Prompt
        # prompt = PREPROCESS_USER_PROMPT_TEMPLATE.format(
        #     user_query="user_query",
        #     decisions_text=decisions_text,
        #     lessons_text=lessons_text,
        #     portfolio_str=portfolio_str,
        #     market_md=market_md
        # )
        # print(f"Decisions: {decisions_text}")
        # print(f"Market MD length: {len(market_md)}")
        # print(f"Prompt length: {prompt}")

        res =await PreProcessAgent().run("default_user","",user_query="分析")
        print(res.rendered_pre_context_markdown)
        print(res.rendered_market_context_markdown)

    asyncio.run(main())
