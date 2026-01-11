from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.services.market_service import market_service
from backend.app.registry import Tools
from backend.app.agents.personal_finance.llm import get_llm
from backend.app.agents.personal_finance.task_schemas import (
    DataProvenanceCall,
    LessonItem,
    PreContext,
    QueryBlock,
    ReplayBlock,
    ReplayFacts,
    ReplayTarget,
    ReplayWindow,
)

logger = logging.getLogger(__name__)


def _safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
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
        # Try to salvage the first JSON object in text
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


def _parse_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip()
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # Try ISO date part
    try:
        return datetime.strptime(s.split("T")[0], "%Y-%m-%d")
    except Exception:
        return None


def _extract_decision_records(memory_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Best-effort extraction of structured decision records from formatted memory context."""
    if not memory_context:
        return []

    candidate_keys = [
        "decision_records",
        "decisions",
        "trades",
        "history_decisions",
        "mid_term_decisions",
        "episodic_memory",
    ]
    for k in candidate_keys:
        v = memory_context.get(k)
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    # Some memory systems may nest in `mid_term_history`
    mid = memory_context.get("mid_term_history")
    if isinstance(mid, dict):
        for k in candidate_keys:
            v = mid.get(k)
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def _pick_replay_targets(
    user_query: str, decision_records: List[Dict[str, Any]], max_targets: int = 3
) -> List[ReplayTarget]:
    tools = Tools()
    symbols_in_query: List[str] = []
    try:
        symbols_in_query = tools.extract_symbols(user_query)
    except Exception:
        symbols_in_query = []

    targets: List[ReplayTarget] = []
    for r in decision_records:
        symbol = r.get("symbol") or r.get("ticker") or r.get("asset_id")
        if not symbol:
            continue
        # Normalize A-share (strip prefix)
        if isinstance(symbol, str) and (
            symbol.startswith("sh") or symbol.startswith("sz")
        ):
            symbol = symbol[2:]

        decision_time = (
            r.get("decision_time")
            or r.get("time")
            or r.get("date")
            or r.get("timestamp")
        )
        decision_id = r.get("decision_id") or r.get("id")

        # Relevance: if query contains symbols, keep only matching; else take recent ones
        if symbols_in_query and symbol not in symbols_in_query:
            continue

        targets.append(
            ReplayTarget(
                symbol=str(symbol),
                decision_id=str(decision_id) if decision_id else None,
                decision_time=str(decision_time) if decision_time else None,
                window=ReplayWindow(pre=5, post=5),
            )
        )
        if len(targets) >= max_targets:
            break

    if targets:
        return targets

    # No explicit match -> fallback to most recent N records (best-effort sort)
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for r in decision_records:
        t = (
            r.get("decision_time")
            or r.get("time")
            or r.get("date")
            or r.get("timestamp")
        )
        dt = _parse_date(str(t)) if t else None
        score = dt.timestamp() if dt else 0.0
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    for _, r in scored[:max_targets]:
        symbol = r.get("symbol") or r.get("ticker") or r.get("asset_id")
        if not symbol:
            continue
        if isinstance(symbol, str) and (
            symbol.startswith("sh") or symbol.startswith("sz")
        ):
            symbol = symbol[2:]
        decision_time = (
            r.get("decision_time")
            or r.get("time")
            or r.get("date")
            or r.get("timestamp")
        )
        decision_id = r.get("decision_id") or r.get("id")
        targets.append(
            ReplayTarget(
                symbol=str(symbol),
                decision_id=str(decision_id) if decision_id else None,
                decision_time=str(decision_time) if decision_time else None,
                window=ReplayWindow(pre=5, post=5),
            )
        )
    return targets


def _max_drawdown(closes: List[float]) -> float:
    if not closes:
        return 0.0
    peak = closes[0]
    mdd = 0.0
    for c in closes:
        if c > peak:
            peak = c
        dd = (peak - c) / peak if peak else 0.0
        if dd > mdd:
            mdd = dd
    return mdd


def _max_runup(closes: List[float]) -> float:
    if not closes:
        return 0.0
    trough = closes[0]
    mru = 0.0
    for c in closes:
        if c < trough:
            trough = c
        ru = (c - trough) / trough if trough else 0.0
        if ru > mru:
            mru = ru
    return mru


def _compute_replay_facts(
    history: List[Dict[str, Any]],
    decision_dt: datetime,
    window: ReplayWindow,
) -> ReplayFacts:
    # history timestamps are iso strings sorted ascending.
    parsed = []
    for item in history:
        ts = item.get("timestamp")
        if not ts:
            continue
        dt = _parse_date(ts)
        if not dt:
            try:
                dt = datetime.strptime(str(ts).split("T")[0], "%Y-%m-%d")
            except Exception:
                continue
        parsed.append((dt.date(), item))
    parsed.sort(key=lambda x: x[0])
    if not parsed:
        return ReplayFacts()

    # Find closest trading day to decision date
    target_date = decision_dt.date()
    idx = min(range(len(parsed)), key=lambda i: abs((parsed[i][0] - target_date).days))

    start_pre = max(0, idx - window.pre)
    end_pre = idx
    start_post = idx
    end_post = min(len(parsed), idx + window.post + 1)

    pre = parsed[start_pre:end_pre]
    post = parsed[start_post:end_post]
    if len(pre) < window.pre or len(post) < (window.post + 1):
        # Not enough data to compute window
        return ReplayFacts(t_date=str(parsed[idx][0]), t_index=idx)

    close_t = float(post[0][1].get("close", 0) or 0)
    close_pre_0 = float(pre[0][1].get("close", 0) or 0)
    close_post_last = float(post[-1][1].get("close", 0) or 0)

    pre_ret = (close_t / close_pre_0 - 1) if close_pre_0 else None
    post_ret = (close_post_last / close_t - 1) if close_t else None

    post_closes = [float(x[1].get("close", 0) or 0) for x in post]
    mdd = _max_drawdown(post_closes)
    mru = _max_runup(post_closes)

    pre_vols = [float(x[1].get("volume", 0) or 0) for x in pre]
    post_vols = [
        float(x[1].get("volume", 0) or 0) for x in post[1:]
    ]  # exclude T day itself for post avg
    pre_avg = sum(pre_vols) / len(pre_vols) if pre_vols else 0.0
    post_avg = sum(post_vols) / len(post_vols) if post_vols else 0.0
    vol_ratio = (post_avg / pre_avg) if pre_avg else None
    max_spike = (max(post_vols) / pre_avg) if (pre_avg and post_vols) else None

    return ReplayFacts(
        t_date=str(parsed[idx][0]),
        t_index=idx,
        pre_window_return=pre_ret,
        post_window_return=post_ret,
        post_max_drawdown=mdd,
        post_max_runup=mru,
        volume_ratio_post=vol_ratio,
        max_volume_spike=max_spike,
    )


def _render_precontext_markdown(pre: PreContext) -> str:
    def _dump(v: Any) -> str:
        try:
            return json.dumps(v, ensure_ascii=False, indent=2)
        except Exception:
            return str(v)

    lines: List[str] = []
    lines.append("# 本轮起始上下文（PreContext）")
    lines.append("\n## 用户问题")
    lines.append(pre.query.raw)

    lines.append("\n## 长期记忆（准则）")
    lines.append(_dump(pre.memory_blocks.get("long_term_principles")))

    if pre.memory_blocks.get("semantic_memory"):
        lines.append("\n## 长期记忆（综合背景）")
        lines.append(_dump(pre.memory_blocks.get("semantic_memory")))

    lines.append("\n## 中期记忆（相关历史/决策）")
    lines.append(_dump(pre.memory_blocks.get("mid_term_history")))

    lines.append("\n## 短期记忆（近期对话）")
    lines.append(_dump(pre.memory_blocks.get("short_term_dialogue")))

    lines.append("\n## 用户画像")
    lines.append(_dump(pre.memory_blocks.get("persona")))

    lines.append("\n## 复盘事实（T-5~T+5）（如有）")
    if pre.replay.enabled and pre.replay.facts_by_symbol:
        lines.append(
            _dump({k: v.model_dump() for k, v in pre.replay.facts_by_symbol.items()})
        )
    else:
        lines.append("(无)")

    lines.append("\n## 经验总结/建议（如有）")
    if pre.lessons.items:
        for it in pre.lessons.items:
            lines.append(f"- {it.title}: {it.description}")
    else:
        lines.append("(无)")

    lines.append("\n## 本轮关注点（Focus）")
    lines.append(_dump(pre.focus.model_dump()))

    lines.append("\n## 待确认问题（Open Questions）")
    if pre.open_questions:
        for q in pre.open_questions:
            lines.append(f"- {q}")
    else:
        lines.append("(无)")

    lines.append("\n## 取数与证据来源（Provenance）")
    lines.append(_dump(pre.data_provenance.model_dump()))

    return "\n".join(lines)


class PreProcessAgent:
    """Pre-process agent that builds formatted PreContext (JSON + Markdown) for master."""

    async def run(
        self,
        user_query: str,
        memory_context: Dict[str, Any],
        portfolio: Optional[Dict[str, Any]] = None,
    ) -> PreContext:
        llm = get_llm(temperature=0.2)
        provenance_calls: List[DataProvenanceCall] = []

        # Build memory blocks (mapping standard MemorySystem fields)
        memory_blocks = {
            "long_term_principles": memory_context.get("core_principles")
            or memory_context.get("principles")
            or memory_context.get("long_term_principles"),
            "mid_term_history": memory_context.get("episodic_memory")
            or memory_context.get("mid_term_history")
            or memory_context.get("history")
            or memory_context,  # Fallback
            "short_term_dialogue": memory_context.get("working_memory", [])
            or memory_context.get("stm")
            or memory_context.get("short_term_dialogue"),
            "persona": memory_context.get("user_persona")
            or memory_context.get("persona"),
            "semantic_memory": memory_context.get("semantic_memory"),
            "memory_reflection": memory_context.get("reflection"),
        }

        decision_records = _extract_decision_records(memory_context)
        if decision_records:
            logger.info(f"[PreProcess] Found {len(decision_records)} decision records in memory.")

        targets = _pick_replay_targets(user_query, decision_records, max_targets=3)
        if targets:
            logger.info(f"[PreProcess] Selected {len(targets)} replay targets: {[t.symbol for t in targets]}")
        
        replay = ReplayBlock(enabled=bool(targets), targets=targets)

        facts_by_symbol: Dict[str, ReplayFacts] = {}
        if targets:
            # Fetch historical data and compute facts in parallel
            async def _fetch_and_compute(
                t: ReplayTarget,
            ) -> Tuple[str, ReplayFacts, Optional[DataProvenanceCall]]:
                if not t.decision_time:
                    return t.symbol, ReplayFacts(), None
                dt = _parse_date(t.decision_time)
                if not dt:
                    return t.symbol, ReplayFacts(), None
                
                logger.info(f"[PreProcess] Replay fetching for {t.symbol} @ {dt.date()}")

                # Request enough days to include decision date (cap to avoid very heavy requests)
                delta_days = abs((datetime.now().date() - dt.date()).days) + 60
                delta_days = min(max(delta_days, 60), 720)
                period = f"{delta_days}d"

                call = DataProvenanceCall(
                    tool_name="market_service.get_historical_data",
                    params={"symbol": t.symbol, "period": period, "interval": "1d"},
                    time_range=f"{dt.date().isoformat()} (anchor) +/- {t.window.pre}/{t.window.post} trading days",
                )

                try:
                    history = await asyncio.to_thread(
                        market_service.get_historical_data, t.symbol, period, "1d"
                    )
                    facts = _compute_replay_facts(history, dt, t.window)
                    return t.symbol, facts, call
                except Exception as e:
                    call.status = "failed"
                    call.error = str(e)
                    return t.symbol, ReplayFacts(), call

            results = await asyncio.gather(*[_fetch_and_compute(t) for t in targets])
            for sym, facts, call in results:
                facts_by_symbol[sym] = facts
                if call:
                    provenance_calls.append(call)

        replay.facts_by_symbol = facts_by_symbol

        # Let LLM decide focus/open_questions/optional lessons given memory + optional replay facts
        prompt = f"""
你是个人理财智能体链路中的 PreProcessAgent。你的职责是把 MemorySystem 返回的结构化记忆上下文，整理为给 Master 使用的起始上下文（PreContext）。

要求：
1) **冲突记忆过滤与整合**：
   - 请仔细检查 Input 中的 MemoryContext。
   - 如果发现 `user_persona`（画像）或 `long_term_principles`（准则）与近期的 `short_term_dialogue`（短期对话）或 `mid_term_history`（操作历史）存在显著冲突（例如：画像说是保守型，但最近对话要求激进炒作），请**以最新的短期记忆或显式指令为准**。
   - 如果发现冲突并进行了修正，请在 `refined_memory` 字段中输出修正后的版本。

2) 你必须输出 JSON（不要输出多余文本），字段包含：
   - focus: {{ priority: string, must_cover: string[] }}
   - open_questions: string[]
   - lessons: {{ items: [{{ title, description, applicable_conditions?, confidence? }}] }}
   - replay: {{ analysis?: string }}
   - refined_memory: {{ 
       persona?: object,          // 仅当发现冲突且需要修正画像时输出，否则为 null
       long_term_principles?: string[] // 仅当发现冲突且需要修正准则时输出，否则为 null
     }}

输入：
用户问题：{user_query}

MemoryContext（格式化）：
{json.dumps(memory_context, ensure_ascii=False)[:12000]}

ReplayFacts（可能为空）：
{json.dumps({k: v.model_dump() for k, v in facts_by_symbol.items()}, ensure_ascii=False)}
"""

        focus_priority = "risk_first"
        focus_must_cover: List[str] = []
        open_questions: List[str] = []
        lessons: List[LessonItem] = []
        replay_analysis: Optional[str] = None

        try:
            resp = await llm.ainvoke(
                [
                    SystemMessage(content="You are a helpful assistant."),
                    HumanMessage(content=prompt),
                ]
            )
            data = _safe_json_extract(resp.content) or {}

            focus = data.get("focus") or {}
            focus_priority = focus.get("priority") or focus_priority
            focus_must_cover = focus.get("must_cover") or []
            open_questions = data.get("open_questions") or []
            replay_analysis = (
                (data.get("replay") or {}).get("analysis")
                if isinstance(data.get("replay"), dict)
                else None
            )

            logger.info(f"[PreProcess] Focus priority: {focus_priority}")
            if replay_analysis:
                logger.info(f"[PreProcess] Replay analysis: {replay_analysis[:50]}...")
            
            lessons_block = data.get("lessons") or {}
            items = lessons_block.get("items") or []
            if isinstance(items, list):
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    if it.get("title") and it.get("description"):
                        lessons.append(LessonItem(**it))
            
            # Apply refined memory if conflicts were resolved
            refined = data.get("refined_memory")
            if isinstance(refined, dict):
                if refined.get("persona"):
                    logger.info("[PreProcess] Applying refined persona (conflict resolution)")
                    memory_blocks["persona"] = refined["persona"]
                if refined.get("long_term_principles"):
                    logger.info("[PreProcess] Applying refined principles (conflict resolution)")
                    memory_blocks["long_term_principles"] = refined["long_term_principles"]

        except Exception as e:
            logger.warning(
                f"PreProcessAgent LLM parse failed, fallback to minimal focus: {e}"
            )
            focus_must_cover = ["给出明确的风险边界与可执行建议"]

        pre = PreContext(
            query=QueryBlock(raw=user_query),
            memory_blocks=memory_blocks,
            replay=replay,
        )
        pre.focus.priority = focus_priority
        pre.focus.must_cover = focus_must_cover
        pre.open_questions = open_questions
        pre.lessons.items = lessons
        pre.replay.analysis = replay_analysis
        pre.data_provenance.tool_calls = provenance_calls
        pre.rendered_markdown = _render_precontext_markdown(pre)
        logger.info(f"[PreProcess] Generated Context Markdown:\n{pre.rendered_markdown}")
        return pre
