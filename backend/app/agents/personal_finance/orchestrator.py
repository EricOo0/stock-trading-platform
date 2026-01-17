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
import datetime
from backend.app.agents.personal_finance.task_schemas import (
    LessonItem,
    Plan,
    PlanTask,
    TaskInputs,
    TaskStatus,
    WorkerType,
    DecisionReviewResult,
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
from backend.app.agents.personal_finance.repository import PersonalFinanceRepository
from backend.app.agents.personal_finance.utils import (
    safe_json_extract,
    extract_response_content,
    summarize_portfolio,
    extract_top_symbols,
)
from backend.app.agents.personal_finance.prompts import (
    MASTER_PLANNER_SYSTEM_PROMPT,
    MASTER_SYNTHESIZER_SYSTEM_PROMPT,
    MASTER_PLANNER_USER_PROMPT_TEMPLATE,
    MASTER_CARD_GENERATION_PROMPT_TEMPLATE,
    MASTER_REPORT_GENERATION_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def _format_plan_status(plan: Plan) -> str:
    lines = [f"Plan(turn={plan.turn}) goal={plan.goal}"]
    for t in plan.tasks:
        result_preview = ""
        if t.result:
            # Preview first 200 chars of result to help master decide next step
            result_preview = f"\n   Result: {t.result}"
        
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
            system_prompt=MASTER_PLANNER_SYSTEM_PROMPT
        )
        self.synthesizer_agent = create_agent(
            model=self.llm,
            tools=[],
            system_prompt=MASTER_SYNTHESIZER_SYSTEM_PROMPT
        )

    async def decide_next(
        self, *, pre_context_markdown: str, user_query: str, plan: Optional[Plan], market_snapshot_md: str = ""
    ) -> MasterDecision:
        plan_status = (
            "No plan yet. You must create a plan."
            if not plan
            else _format_plan_status(plan)
        )
        prompt = MASTER_PLANNER_USER_PROMPT_TEMPLATE.format(
            pre_context_markdown=pre_context_markdown,
            market_snapshot_md=market_snapshot_md,
            user_query=user_query,
            plan_status=plan_status
        )
        
        print(f"[Master] Planner prompt: {prompt}")
        resp = await self.planner_agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]}
        )
        content = extract_response_content(resp)
        data = safe_json_extract(content) or {}

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
        card_prompt = MASTER_CARD_GENERATION_PROMPT_TEMPLATE.format(context=context)
        
        cards: List[RecommendationCard] = []
        try:
            resp = await self.synthesizer_agent.ainvoke({"messages": [HumanMessage(content=card_prompt)]})
            content = extract_response_content(resp)
            data = safe_json_extract(content) or {}
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
        report_prompt = MASTER_REPORT_GENERATION_PROMPT_TEMPLATE.format(context=context)
        
        logger.info(f"[Master] Synthesize report with prompt: {report_prompt[:100]}...")
        resp = await self.synthesizer_agent.ainvoke({"messages": [HumanMessage(content=report_prompt)]})
        return extract_response_content(resp)


class PersonalFinanceOrchestrator:
    """Drop-in replacement for the old LangGraph graph object (exposes astream)."""

    def __init__(self):
        self.pre = PreProcessAgent()
        self.master = PersonalFinanceMaster()
        self.repo = PersonalFinanceRepository()
        # Cache latest snapshot markdown for sub-agent calls
        self.latest_snapshot_md: str = ""

    async def _save_decisions_to_db(self, *, user_id: str, cards: List[RecommendationCard]) -> List[Dict[str, Any]]:
        """Save recommendation cards as active decisions and return shadow trade requests."""
        if not cards:
            return []
        
        try:
            return await asyncio.to_thread(self.repo.save_decisions, user_id, cards)
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to save decision records: {e}")
            return []

    async def _save_lessons_to_db(self, *, user_id: str, lessons: List[LessonItem]):
        """Replace user lessons with refined list."""
        if not lessons:
            return

        try:
            await asyncio.to_thread(self.repo.save_lessons, user_id, lessons)
            logger.info(f"[Orchestrator] Saved {len(lessons)} refined lessons via Repo.")
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to save lessons: {e}")

    async def _update_reviewed_decisions(self, *, user_id: str, reviews: List[DecisionReviewResult]):
        """Update active decisions with latest review results."""
        if not reviews:
            return

        try:
            await asyncio.to_thread(self.repo.update_decision_reviews, user_id, reviews)
            logger.info(f"[Orchestrator] Updated {len(reviews)} decision records with review results via Repo.")
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to update decision reviews: {e}")

    async def _finalize_and_save(self, *, user_id: str, context: str, plan: Optional[Plan], pre_context, conclusion_dict: Optional[Dict[str, Any]] = None):
        """Finalize the session: synthesize report, generate cards, and save everything."""
        logger.info(f"[Orchestrator] Finalize and save session for user {user_id} with context: {context[:100]}...")
        final_report = conclusion_dict.get("final_report") if conclusion_dict else None

        if not final_report:
            final_report = await self.master.synthesize_report(context=context)

        cards = await self.master.synthesize_cards(context=context)
        
        # Save decisions and get shadow trade requests
        shadow_requests = await self._save_decisions_to_db(user_id=user_id, cards=cards)
        
        # --- Shadow Trade Execution ---
        if shadow_requests:
            for req in shadow_requests:
                try:
                    await asyncio.to_thread(
                        self.repo.execute_shadow_trade,
                        user_id=user_id,
                        symbol=req["symbol"],
                        action=req["action"],
                        quantity=req["quantity"],
                        price=req["price"]
                    )
                    logger.info(f"[Orchestrator] Executed shadow trade: {req['action']} {req['symbol']} qty={req['quantity']}")
                except Exception as e:
                    logger.error(f"[Orchestrator] Failed to execute shadow trade for {req.get('symbol')}: {e}")
        # ------------------------------
        
        # Save Lessons (Directly from PreContext, trusting PreProcessAgent's management)
        await self._save_lessons_to_db(user_id=user_id, lessons=pre_context.lessons)
        
        print(f"[Master] Final report: {final_report}")
        
        return {
            "synthesizer": {
                "final_report": final_report,
                "recommendation_cards": [c.model_dump() for c in cards],
                "plan": plan.model_dump() if plan else None,
            }
        }

    async def astream(
        self, initial_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        messages: List[BaseMessage] = initial_state.get("messages") or []
        portfolio: Dict[str, Any] = initial_state.get("portfolio") or {}
        user_id: str = initial_state.get("user_id", "default_user")
        session_id: str = initial_state.get("session_id", "default_session")
        user_query = portfolio.get("query") or (
            messages[-1].content if messages else "请分析我的投资组合并给出建议"
        )

        # 2) PreProcessAgent
        pre_context = await self.pre.run(
            user_id=user_id,
            session_id=session_id,
            user_query=user_query,
            portfolio=portfolio,
        )

        # 2.1) Update Decisions with Review Results (Close the loop)
        if pre_context.review_results:
            await self._update_reviewed_decisions(user_id=user_id, reviews=pre_context.review_results)

        yield {
            "pre_process": {
                "pre_context": pre_context.model_dump(),
                "pre_context_markdown": pre_context.rendered_pre_context_markdown,
                "market_context_markdown": pre_context.rendered_market_context_markdown,
                "lessons_count": len(pre_context.lessons),
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
                market_snapshot_md=pre_context.rendered_market_context_markdown,
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
                    user_query=user_query,
                    pre_context=pre_context,
                    plan=plan
                )
                
                result = await self._finalize_and_save(
                    user_id=user_id,
                    context=context,
                    plan=plan,
                    pre_context=pre_context,
                    conclusion_dict=conclusion_dict
                )
                yield result
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
            user_query=user_query,
            portfolio=portfolio,
            pre_context=pre_context,
            plan=plan
        )
        
        result = await self._finalize_and_save(
            user_id=user_id,
            context=context,
            plan=plan,
            pre_context=pre_context
        )
        yield result

    def _build_tasks_from_dicts(
        self, tasks: List[Dict[str, Any]], portfolio: Dict[str, Any]
    ) -> List[PlanTask]:
        built: List[PlanTask] = []
        top_symbols = extract_top_symbols(portfolio, limit=50)
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
            symbols = task.inputs.symbols or extract_top_symbols(portfolio, limit=50)
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
            symbols = task.inputs.symbols or extract_top_symbols(portfolio, limit=50)
            q = (
                f"Latest news and sentiment for {', '.join(symbols)}"
                if symbols
                else "Latest market news"
            )
            return await run_news_analysis(q, market_snapshot=getattr(self, "latest_snapshot_md", ""))
        if wt == WorkerType.DAILY_REVIEW:
            symbols = task.inputs.symbols or extract_top_symbols(portfolio, limit=50)
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
        pre_context,
        plan: Optional[Plan],
    ) -> str:
        tasks_summary = ""
        if plan:
            for t in plan.tasks:
                tasks_summary += f"\n\n### [{t.status}] {t.title} ({t.worker_type.value})\n{t.result or ''}"

        return f"""
【Market Context】
{pre_context.rendered_market_context_markdown}

【PreContext】
{pre_context.rendered_pre_context_markdown}

【用户查询】
{user_query}

【任务结果汇总】
{tasks_summary}
""".strip()


if __name__ == "__main__":
    # export PYTHONPATH=$PYTHONPATH:. && python3 backend/app/agents/personal_finance/orchestrator.py
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        orchestrator = PersonalFinanceOrchestrator()
        
        # Mock initial state
        initial_state = {
            "user_id": "test_user_001",
            "session_id": "test_session_001",
            "portfolio": {
                "cash_balance": 50000.0,
                "assets": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "type": "us_stock",
                        "quantity": 100,
                        "cost_basis": 150.0,
                        "current_price": 220.0,
                        "total_value": 22000.0
                    },
                    {
                        "symbol": "600519",
                        "name": "贵州茅台",
                        "type": "cn_stock",
                        "quantity": 100,
                        "cost_basis": 1800.0,
                        "current_price": 1600.0,
                        "total_value": 160000.0
                    }
                ]
            },
            "messages": [
                HumanMessage(content="帮我分析一下现在的持仓风险，并给出调仓建议")
            ]
        }
        
        print("\n>>> Starting Orchestrator Test...")
        try:
            async for event in orchestrator.astream(initial_state):
                print("\n--- Event Received ---")
                for k, v in event.items():
                    print(f"Key: {k}")
                    if k == "pre_process":
                        print(f"PreContext Markdown Preview:\n{v.get('pre_context_markdown', '')[:300]}...")
                    elif k == "synthesizer":
                        print(f"Final Report Preview:\n{v.get('final_report', '')[:300]}...")
                        if v.get("recommendation_cards"):
                             print(f"Cards Count: {len(v['recommendation_cards'])}")
                    elif k == "planner":
                         plan = v.get("plan", {})
                         tasks = plan.get("tasks", [])
                         print(f"Plan Created/Updated. Tasks: {[t.get('title') for t in tasks]}")
                    elif k == "executor":
                        print(f"Executor Update: {v}")
        except Exception as e:
            logger.exception("Orchestrator test failed")

    asyncio.run(main())