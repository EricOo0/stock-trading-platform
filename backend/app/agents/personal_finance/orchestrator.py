from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.personal_finance.llm import get_llm
from backend.app.agents.personal_finance.pre_process import PreProcessAgent
from backend.app.agents.personal_finance.prompts import MASTER_AGENT_SYSTEM_PROMPT
from backend.app.agents.personal_finance.task_schemas import (
    LessonItem,
    Plan,
    PlanTask,
    TaskInputs,
    TaskStatus,
    WorkerType,
)
from backend.app.agents.personal_finance.models import (
    RecommendationCard,
    RecommendationAction,
)
from backend.app.agents.personal_finance.tools import (
    run_macro_analysis,
    run_market_analysis,
    run_news_analysis,
    run_technical_analysis,
)
from backend.app.agents.personal_finance.sub_agents import DailyReviewAnalyst
from backend.infrastructure.adk.core.memory_client import MemoryClient
from backend.infrastructure.config.loader import config

logger = logging.getLogger(__name__)


PLANNER_SYSTEM_PROMPT = """你是 personal_finance 的 Master（任务生成/分配/反思/收敛）。你必须根据上下文做一个明确动作：
1) create_plan：创建任务计划（tasks）
2) add_tasks：在已有计划基础上追加任务（tasks）
3) conclude：输出最终结论（conclusion）

硬约束：
- 任务 worker_type 只能是：macro / market / technical / news / daily_review
- daily_review 可以携带 inputs.portfolio_ops=true，用于输出组合层面的调仓/风控建议。
- 如果当前没有 pending task 且信息足够，请 conclude。
- 规划时参考市场快照（指数/板块温度、资金流、20日新高/新低、连阳/连阴、黄金/白银避险）并显式关注缺口。
- **关键约束**：inputs 中的 "symbols" 必须是**股票代码**（如 000001, 600519, 00700, AAPL），**严禁**使用公司中文名称（如“宗申动力”）。如果不知道代码，请勿生成该 symbols 字段。

输出格式：只输出 JSON，不要输出多余文字。

JSON Schema：
{ 
  "action": "create_plan"|"add_tasks"|"conclude",
  "tasks": [
    {
      "title": string,
      "description": string,
      "worker_type": "macro"|"market"|"technical"|"news"|"daily_review",
      "inputs": {"symbols": string[], "portfolio_ops": boolean, "window": {"pre":5,"post":5} }
    }
  ],
    "questions": [string],
  "conclusion": {
     "final_report": string,
     "replay_summary": string|null,
     "lessons_learned": [{"title": string, "description": string}]
  }
}

注意：
- action=conclude 时 tasks 可以为空数组。
- action=create_plan 时必须产出 3-7 个任务；包含 daily_review 且 portfolio_ops=true。
- 任务覆盖面：宏观周期+指数温度/资金流+板块热/冷+新闻/热点+技术/日内复盘（持仓或 Top symbols）。若缺口（数据为空或错误），在 task 描述中标注“缺口”。
"""


SYNTHESIZER_SYSTEM_PROMPT = """你是一位专业的 AI 理财顾问（Synthesizer）。你的核心职责是根据各路专家的分析结果（Context），为用户提供全面、连贯、数据驱动且个性化的投资建议。

你的工作流程：
1. **综合分析**：
   - 整合宏观、市场、新闻、技术、复盘等多维数据。
   - 寻找矛盾点（如：宏观利空但资金流入）。
   - 进行自省（Reflection），检查是否与用户历史偏好或之前的建议冲突。

2. **制定建议与调仓策略**：
   - 不仅要回答“怎么样”，还要回答“怎么做”。
   - 明确指出调仓机会：例如“建议减持科技股，买入消费防守板块”。
   - 推荐具体的关注标的（板块或个股），并说明理由。
   - 必须生成 1-3个“推荐卡片”，包含明确的行动指令（买入/卖出/持有/观望）。
   - 给出详细，精确的分析结论和理论/数据支撑

重要指引：
- 若市场快照或任何数据存在缺口/时效不足，需在报告中显式标注，而不是忽略。
- 语气：专业、客观、行动导向。给出具体的板块或代码建议时，务必基于数据支持。
"""


def _safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # Try to salvage the first JSON object
        import re

        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


def _extract_response_content(resp: Any) -> str:
    """Helper to extract string content from various agent response formats."""
    # Case 1: AIMessage or object with content attribute
    if hasattr(resp, "content"):
        return str(resp.content)
    
    # Case 2: Dict response (AgentExecutor or Chain)
    if isinstance(resp, dict):
        # Prefer 'output' key (AgentExecutor default)
        if "output" in resp:
            return str(resp["output"])
        
        # Fallback: check for 'messages' key (LangGraph state)
        if "messages" in resp and isinstance(resp["messages"], list) and resp["messages"]:
            last_msg = resp["messages"][-1]
            if hasattr(last_msg, "content"):
                return str(last_msg.content)
    
    # Case 3: Fallback string conversion
    return str(resp)


def _summarize_portfolio(
    portfolio: Dict[str, Any], max_assets: int = 50
) -> Dict[str, Any]:
    assets = portfolio.get("assets") or []
    if not isinstance(assets, list):
        assets = []
    
    # Debug log for portfolio data issues
    cash = portfolio.get("cash_balance", 0.0)
    logger.info(f"[Orchestrator] Portfolio Summary Input - Cash: {cash}, Asset Count: {len(assets)}")
    if assets:
        # Check for potential data quality issues
        total_asset_val = sum([float(a.get("total_value") or 0) for a in assets if isinstance(a, dict)])
        logger.info(f"[Orchestrator] Total Asset Value (Calc): {total_asset_val}")
        if total_asset_val == 0 and len(assets) > 0:
            logger.warning("[Orchestrator] Warning: Assets exist but total value is 0. Check price updates.")
        
        # Log first asset for debugging
        if isinstance(assets[0], dict):
            logger.info(f"[Orchestrator] First Asset Sample: {assets[0]}")
        else:
            logger.error(f"[Orchestrator] Asset type mismatch: expected dict, got {type(assets[0])}")

    # Keep only essential fields to reduce prompt bloat
    trimmed = []
    for a in assets[:max_assets]:
        if not isinstance(a, dict):
            continue
        trimmed.append(
            {
                "symbol": a.get("symbol"),
                "name": a.get("name"),
                "type": a.get("type"),
                "quantity": a.get("quantity"),
                "cost_basis": a.get("cost_basis"),
                "current_price": a.get("current_price"),
                "total_value": a.get("total_value"),
            }
        )
    return {"assets": trimmed, "cash_balance": portfolio.get("cash_balance", 0.0)}


def _extract_top_symbols(portfolio: Dict[str, Any], limit: int = 50) -> List[str]:
    assets = portfolio.get("assets") or []
    symbols: List[str] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        sym = a.get("symbol")
        if sym:
            symbols.append(str(sym).replace("sh", "").replace("sz", ""))
    return symbols[:limit]


def _format_plan_status(plan: Plan) -> str:
    lines = [f"Plan(turn={plan.turn}) goal={plan.goal}"]
    for t in plan.tasks:
        result_preview = ""
        if t.result:
            # Preview first 200 chars of result to help master decide next step
            result_preview = f"\n   Result: {t.result[:200]}..."
        
        lines.append(
            f"- [{t.status}] {t.worker_type.value} {t.title}{result_preview}"
        )
    return "\n".join(lines)


def _lessons_to_markdown(lessons: List[LessonItem]) -> str:
    if not lessons:
        return ""
    lines = ["## 经验总结 / 复盘要点（如有）"]
    for it in lessons:
        lines.append(f"- {it.title}: {it.description}")
    return "\n".join(lines)


@dataclass
class MasterDecision:
    action: str  # create_plan | add_tasks | conclude
    tasks: List[Dict[str, Any]]
    conclusion: Optional[Dict[str, Any]] = None
    questions: Optional[List[str]] = None


class PersonalFinanceMaster:
    """LangChain-based master that creates/updates plan and synthesizes conclusion."""

    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.planner_agent = create_agent(
            model=self.llm,
            tools=[],
            system_prompt=PLANNER_SYSTEM_PROMPT
        )
        self.synthesizer_agent = create_agent(
            model=self.llm,
            tools=[],
            system_prompt=SYNTHESIZER_SYSTEM_PROMPT
        )

    async def decide_next(
        self, *, pre_context_markdown: str, user_query: str, plan: Optional[Plan], market_snapshot_md: str = ""
    ) -> MasterDecision:
        plan_status = (
            "No plan yet. You must create a plan."
            if not plan
            else _format_plan_status(plan)
        )
        prompt = f"""
=== PreContext ===
{pre_context_markdown}

=== Market Snapshot ===
{market_snapshot_md}

=== User Query ===
{user_query}

=== Plan Status ===
{plan_status}
"""
        print(f"[Master] Planner prompt: {prompt}")
        resp = await self.planner_agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]}
        )
        content = _extract_response_content(resp)
        data = _safe_json_extract(content) or {}

        action = data.get("action") or ("create_plan" if not plan else "conclude")
        tasks = data.get("tasks") or []
        questions = data.get("questions") or []
        conclusion = data.get("conclusion")

        logger.info(f"[Master] DecideNext: action={action}, tasks_len={len(tasks)}")
        if action == "conclude":
            logger.info(f"[Master] Conclusion preview: {str(conclusion)[:100]}...")

        return MasterDecision(
            action=action, tasks=tasks, conclusion=conclusion, questions=questions
        )

    async def synthesize_cards(self, *, context: str) -> List[RecommendationCard]:
        card_prompt = f"""
根据上下文，为用户生成 1-3 张高价值的“推荐卡片”。返回 JSON：{{"cards": [ ... ]}}。

卡片 schema：
{{
  "title": string,
  "description": string,
  "asset_id": string|null,
  "action": "buy"|"sell"|"hold"|"monitor",
  "confidence_score": number, // 范围 0.0 - 1.0 (例如 0.85 代表 85%)
  "risk_level": "low"|"medium"|"high"
}}

上下文：
{context}
"""
        cards: List[RecommendationCard] = []
        try:
            resp = await self.synthesizer_agent.ainvoke({"messages": [HumanMessage(content=card_prompt)]})
            content = _extract_response_content(resp)
            data = _safe_json_extract(content) or {}
            for item in data.get("cards", []) or []:
                if isinstance(item, dict):
                    # Normalize confidence score if needed
                    score = item.get("confidence_score", 0.5)
                    if score > 1.0:
                        item["confidence_score"] = score / 100.0
                    
                    cards.append(RecommendationCard(**item))
        except Exception as e:
            logger.error(f"Failed to generate cards: {e}")
            cards.append(
                RecommendationCard(
                    title="Portfolio Review Complete",
                    description="请查看详细报告并结合风险偏好做决策。",
                    action=RecommendationAction.HOLD,
                    confidence_score=0.5,
                    risk_level="medium",
                )
            )
        logger.info(f"[Master] Generated {len(cards)} recommendation cards.")
        return cards

    async def synthesize_report(self, *, context: str) -> str:
        report_prompt = f"""
将上下文综合成一份连贯、易读、行动导向的 Markdown 报告。

硬约束：
1) 必须包含章节：
   - ## 结论与建议
   - ## 风险与边界条件
   - ## 证据链摘要
   - ## 经验总结 / 复盘要点（如有）
2) 如果上下文中出现“经验总结/复盘要点”，不得省略。

上下文：
{context}
"""
        logger.info(f"[Master] Synthesize report with prompt: {report_prompt[:100]}...")
        resp = await self.synthesizer_agent.ainvoke({"messages": [HumanMessage(content=report_prompt)]})
        return _extract_response_content(resp)


class PersonalFinanceOrchestrator:
    """Drop-in replacement for the old LangGraph graph object (exposes astream)."""

    def __init__(self):
        self.pre = PreProcessAgent()
        self.master = PersonalFinanceMaster()
        # Cache latest snapshot markdown for sub-agent calls
        self.latest_snapshot_md: str = ""

    async def astream(
        self, initial_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        messages: List[BaseMessage] = initial_state.get("messages") or []
        portfolio: Dict[str, Any] = initial_state.get("portfolio") or {}
        user_id: str = initial_state.get("user_id", "default_user")
        session_id: str = initial_state.get("session_id", "default_session")
        print("debug-wzf",portfolio)
        user_query = portfolio.get("query") or (
            messages[-1].content if messages else "请分析我的投资组合并给出建议"
        )

        # 1) Retrieve memory context (formatted by MemorySystem)
        memory_context: Dict[str, Any] = {}
        try:
            memory_url = config.get("memory_service_url", "http://localhost:10000")
            client = MemoryClient(
                base_url=memory_url, user_id=user_id, agent_id="personal_finance"
            )
            memory_context = await asyncio.to_thread(
                client.get_context, 
                query=user_query, 
                session_id=session_id,
                limit=20,
                max_tokens=5000
            )
        except Exception as e:
            logger.warning(f"Failed to retrieve memory context: {e}")
            memory_context = {}

        # 2) PreProcessAgent
        pre_context = await self.pre.run(
            user_query=user_query, memory_context=memory_context, portfolio=portfolio
        )
        if hasattr(pre_context, "rendered_market_context_markdown"):
            self.latest_snapshot_md = pre_context.rendered_market_context_markdown
        yield {
            "pre_process": {
                "pre_context": pre_context.model_dump(),
                "pre_context_markdown": pre_context.rendered_pre_context_markdown,
                "market_context_markdown": pre_context.rendered_market_context_markdown,
                "replay_enabled": pre_context.replay.enabled,
                "lessons_count": len(pre_context.lessons.items),
            }
        }

        # 3) Multi-turn planning/execution loop
        plan: Optional[Plan] = None
        max_turns = 10
        semaphore = asyncio.Semaphore(3)

        for turn in range(max_turns):
            if plan:
                plan.turn = turn

            decision = await self.master.decide_next(
                pre_context_markdown=pre_context.rendered_pre_context_markdown,
                user_query=user_query,
                plan=plan,
                market_snapshot_md=getattr(pre_context, "rendered_market_context_markdown", "") or "",
            )

            if decision.action == "create_plan":
                plan = self._build_plan_from_tasks(
                    user_query, decision.tasks, portfolio
                )
                yield {
                    "planner": {
                        "plan": plan.model_dump(),
                        "selected_agents": [t.worker_type.value for t in plan.tasks],
                    }
                }
            elif decision.action == "add_tasks" and plan:
                added = self._build_tasks_from_dicts(decision.tasks, portfolio)
                plan.tasks.extend(added)
                yield {
                    "planner": {
                        "plan": plan.model_dump(),
                        "added_tasks": [t.model_dump() for t in added],
                    }
                }
            elif decision.action == "conclude":
                conclusion_dict = decision.conclusion or {}
                # Final synthesis context
                context = self._build_synthesis_context(
                    user_query, portfolio, pre_context, plan
                )
                final_report = conclusion_dict.get("final_report")
                if not final_report:
                    final_report = await self.master.synthesize_report(context=context)

                lessons = []
                for it in conclusion_dict.get("lessons_learned") or []:
                    if (
                        isinstance(it, dict)
                        and it.get("title")
                        and it.get("description")
                    ):
                        lessons.append(
                            LessonItem(title=it["title"], description=it["description"])
                        )

                # Ensure lessons from pre_context are preserved (if any)
                if pre_context.lessons.items:
                    for it in pre_context.lessons.items:
                        lessons.append(it)

                # Ensure report contains lessons section
                lessons_md = _lessons_to_markdown(lessons)
                if lessons_md and "经验总结" not in final_report:
                    final_report = lessons_md + "\n\n" + final_report

                cards = await self.master.synthesize_cards(context=context)
                yield {
                    "synthesizer": {
                        "final_report": final_report,
                        "recommendation_cards": [c.model_dump() for c in cards],
                        "plan": plan.model_dump() if plan else None,
                    }
                }
                print(f"[Master] Final report: {final_report}")
                await self._save_memory(
                    user_id=user_id,
                    pre_context=pre_context,
                    user_query=user_query,
                    final_report=final_report,
                    lessons=lessons,
                )
                return

            # Execute pending tasks if plan exists
            if not plan:
                continue

            pending = [t for t in plan.tasks if t.status == TaskStatus.PENDING]
            if not pending:
                # No pending tasks -> ask master to conclude next round
                continue

            yield {
                "executor": {"status": f"开始执行 {len(pending)} 个任务（turn={turn}）"}
            }

            async def _execute_with_semaphore(task: PlanTask):
                async with semaphore:
                    return await self._execute_task(task, portfolio)

            # We can't stream tokens here; emit task status updates after each batch
            results = await asyncio.gather(
                *[_execute_with_semaphore(task) for task in pending],
                return_exceptions=True,
            )
            for task, res in zip(pending, results):
                task.status = (
                    TaskStatus.COMPLETED
                    if not isinstance(res, Exception)
                    else TaskStatus.FAILED
                )
                task.result = (
                    str(res)
                    if not isinstance(res, Exception)
                    else f"Execution Error: {res}"
                )
                yield {
                    "executor": {
                        "task_update": {
                            "id": task.id,
                            "status": task.status,
                            "title": task.title,
                            "result": task.result,
                        }
                    }
                }

        # Max turns reached -> force conclude
        context = self._build_synthesis_context(
            user_query, portfolio, pre_context, plan
        )
        final_report = await self.master.synthesize_report(context=context)
        lessons = list(pre_context.lessons.items)
        lessons_md = _lessons_to_markdown(lessons)
        if lessons_md and "经验总结" not in final_report:
            final_report = lessons_md + "\n\n" + final_report
        cards = await self.master.synthesize_cards(context=context)
        yield {
            "synthesizer": {
                "final_report": final_report,
                "recommendation_cards": cards,
                "plan": plan.model_dump() if plan else None,
            }
        }
        await self._save_memory(
            user_id=user_id,
            pre_context=pre_context,
            user_query=user_query,
            final_report=final_report,
            lessons=lessons,
        )

    def _build_tasks_from_dicts(
        self, tasks: List[Dict[str, Any]], portfolio: Dict[str, Any]
    ) -> List[PlanTask]:
        built: List[PlanTask] = []
        top_symbols = _extract_top_symbols(portfolio, limit=50)
        for i, t in enumerate(tasks or []):
            if not isinstance(t, dict):
                continue
            worker_type = t.get("worker_type")
            try:
                wt = WorkerType(worker_type)
            except Exception:
                continue
            inputs_dict = t.get("inputs") or {}
            symbols = inputs_dict.get("symbols") or []
            if not symbols and wt in (
                WorkerType.TECHNICAL,
                WorkerType.DAILY_REVIEW,
                WorkerType.NEWS,
            ):
                symbols = top_symbols
            
            # --- 增加 Symbol 格式校验 ---
            valid_symbols = []
            for s in symbols:
                s_str = str(s).strip()
                # 简单规则：必须包含数字，或者是美股纯字母但长度通常较短且非中文
                # 如果包含非ascii（例如中文），则认为非法
                if not all(ord(c) < 128 for c in s_str):
                    logger.warning(f"[Orchestrator] Invalid symbol format (non-ascii): {s_str}. Dropping.")
                    continue
                valid_symbols.append(s_str.replace("sh", "").replace("sz", ""))
            
            if not valid_symbols and symbols:
                logger.warning(f"[Orchestrator] All symbols for task {t.get('title')} were invalid. Using top symbols fallback.")
                valid_symbols = [str(s).replace("sh", "").replace("sz", "") for s in top_symbols]

            inputs = TaskInputs(
                symbols=valid_symbols,
                portfolio_ops=bool(inputs_dict.get("portfolio_ops", False)),
            )
            # ---------------------------

            task_id = f"pf_task_{int(time.time())}_{i}_{wt.value}"
            built.append(
                PlanTask(
                    id=task_id,
                    title=t.get("title") or f"{wt.value} 分析",
                    description=t.get("description") or "",
                    worker_type=wt,
                    inputs=inputs,
                )
            )
        return built

    def _build_plan_from_tasks(
        self, user_query: str, tasks: List[Dict[str, Any]], portfolio: Dict[str, Any]
    ) -> Plan:
        plan_id = f"pf_plan_{int(time.time())}"
        built = self._build_tasks_from_dicts(tasks, portfolio)
        if not built:
            # fallback minimal plan
            built = self._build_tasks_from_dicts(
                [
                    {
                        "title": "宏观环境",
                        "description": "分析宏观环境与资产配置影响",
                        "worker_type": "macro",
                        "inputs": {},
                    },
                    {
                        "title": "市场情绪",
                        "description": "分析市场热点与风险",
                        "worker_type": "market",
                        "inputs": {},
                    },
                    {
                        "title": "组合复盘",
                        "description": "对持仓做复盘与调仓建议",
                        "worker_type": "daily_review",
                        "inputs": {"portfolio_ops": True},
                    },
                ],
                portfolio,
            )
        return Plan(plan_id=plan_id, goal=user_query, tasks=built)

    async def _execute_task(self, task: PlanTask, portfolio: Dict[str, Any]) -> str:
        logger.info(f"[Executor] Starting task: {task.title} (type={task.worker_type.value})")
        wt = task.worker_type
        if wt == WorkerType.MACRO:
            snapshot_md = getattr(self, "latest_snapshot_md", "")
            return await run_macro_analysis(market_snapshot=snapshot_md)
        if wt == WorkerType.MARKET:
            snapshot_md = getattr(self, "latest_snapshot_md", "")
            return await run_market_analysis(market_snapshot=snapshot_md)
        if wt == WorkerType.TECHNICAL:
            symbols = task.inputs.symbols or _extract_top_symbols(portfolio, limit=50)
            if not symbols:
                return "No symbols for technical analysis."
            res = await asyncio.gather(
                *[
                    run_technical_analysis(
                        sym,
                        market_snapshot=getattr(self, "latest_snapshot_md", ""),
                    )
                    for sym in symbols
                ]
            )
            return "\n\n".join([str(r) for r in res])
        if wt == WorkerType.NEWS:
            symbols = task.inputs.symbols or _extract_top_symbols(portfolio, limit=50)
            q = (
                f"Latest news and sentiment for {', '.join(symbols)}"
                if symbols
                else "Latest market news"
            )
            return await run_news_analysis(q, market_snapshot=getattr(self, "latest_snapshot_md", ""))
        if wt == WorkerType.DAILY_REVIEW:
            symbols = task.inputs.symbols or _extract_top_symbols(portfolio, limit=50)
            analyst = DailyReviewAnalyst()
            if task.inputs.portfolio_ops:
                return await analyst.analyze_portfolio_ops(
                    symbols=symbols,
                    portfolio=portfolio,
                    market_snapshot=getattr(self, "latest_snapshot_md", ""),
                )
            if not symbols:
                return "No symbols for daily review."
            res = await asyncio.gather(
                *[
                    analyst.analyze(
                        sym, market_snapshot=getattr(self, "latest_snapshot_md", "")
                    )
                    for sym in symbols
                ]
            )
            return "\n\n".join([str(r) for r in res])
        return "Unsupported worker type"

    def _build_synthesis_context(
        self,
        user_query: str,
        portfolio: Dict[str, Any],
        pre_context,
        plan: Optional[Plan],
    ) -> str:
        port_summary = _summarize_portfolio(portfolio)
        tasks_summary = ""
        if plan:
            for t in plan.tasks:
                tasks_summary += f"\n\n### [{t.status}] {t.title} ({t.worker_type.value})\n{t.result or ''}"

        snapshot_md = getattr(pre_context, "rendered_market_context_markdown", "") or ""

        return f"""
【Market Context】\n{snapshot_md}

【PreContext】\n{pre_context.rendered_pre_context_markdown}

【投资组合摘要】\n{json.dumps(port_summary, ensure_ascii=False, indent=2)}

【用户查询】\n{user_query}

【任务结果汇总】\n{tasks_summary}
""".strip()

    async def _save_memory(
        self,
        *,
        user_id: str,
        pre_context,
        user_query: str,
        final_report: str,
        lessons: List[LessonItem],
    ):
        try:
            memory_url = config.get("memory_service_url", "http://localhost:10000")
            client = MemoryClient(
                base_url=memory_url, user_id=user_id, agent_id="personal_finance"
            )

            def _add():
                client.add_memory(user_query, role="user")
                
                # Attach lessons to report metadata instead of creating separate entry
                meta = {"type": "report"}
                if lessons:
                    meta["lessons"] = [l.model_dump() for l in lessons]
                    
                client.add_memory(
                    final_report, role="assistant", metadata=meta
                )
                
                # pre_context removed to save storage
                # lessons separate entry logic removed to avoid duplicate assistant messages
                
                client.finalize()

            await asyncio.to_thread(_add)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
