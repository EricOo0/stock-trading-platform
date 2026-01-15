from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agents.personal_finance.llm import get_llm
from backend.app.agents.personal_finance.tools import get_market_context
from backend.app.agents.personal_finance.task_schemas import (
    LessonItem,
    PreContext,
    QueryBlock,
)

logger = logging.getLogger(__name__)


def _safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from LLM output."""
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


def _render_precontext_markdown(pre: PreContext) -> str:
    """Render a readable markdown summary for downstream agents."""
    lines: List[str] = []
    lines.append("# Pre Context")
    lines.append("\n## 用户问题")
    lines.append(pre.query.raw)

    lines.append("\n## 用户画像/偏好")
    persona = pre.memory_blocks.get("persona")
    lines.append(json.dumps(persona, ensure_ascii=False, indent=2) if persona else "(无)")

    lines.append("\n## 记忆摘要")
    long_term = pre.memory_blocks.get("long_term_principles")
    mid_term = pre.memory_blocks.get("mid_term_history")
    short_term = pre.memory_blocks.get("short_term_dialogue")
    lines.append(f"- 长期: {json.dumps(long_term, ensure_ascii=False) if long_term else '(无)'}")
    lines.append(f"- 中期: {json.dumps(mid_term, ensure_ascii=False) if mid_term else '(无)'}")
    lines.append(f"- 短期: {json.dumps(short_term, ensure_ascii=False) if short_term else '(无)'}")

    lines.append("\n## 关注重点")
    lines.append(f"- 优先级: {pre.focus.priority}")
    lines.append(f"- 必须覆盖: {pre.focus.must_cover}")

    lines.append("\n## 待解决问题")
    lines.append(json.dumps(pre.open_questions, ensure_ascii=False) if pre.open_questions else "(无)")

    lines.append("\n## 经验/启示")
    if pre.lessons.items:
        for it in pre.lessons.items:
            lines.append(f"- {it.title}: {it.description}")
    else:
        lines.append("(无)")

    background = pre.memory_blocks.get("context_summary") if isinstance(pre.memory_blocks, dict) else None
    if background:
        lines.append("\n## 背景摘要")
        market_brief = background.get("market_brief") or []
        memory_brief = background.get("memory_brief") or []
        # Support both 'key_data' (prompt instruction) and 'data' (common hallucination)
        key_data = background.get("key_data") or background.get("data") or []
        key_events = background.get("key_events") or []
        
        if market_brief:
            lines.append("- 市场要点:")
            for item in market_brief:
                lines.append(f"  - {item}")
        if memory_brief:
            lines.append("- 记忆要点:")
            for item in memory_brief:
                lines.append(f"  - {item}")
        if key_data:
            lines.append("- 关键数据:")
            for item in key_data:
                lines.append(f"  - {item}")
        if key_events:
            lines.append("- 关键事件:")
            for item in key_events:
                lines.append(f"  - {item}")

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

        # Market context (best-effort)
        market_snapshot: Dict[str, Any] = {}
        market_md = ""
        try:
            market_snapshot = await get_market_context(as_markdown=True)
            market_md = market_snapshot.get("markdown", "") or ""
        except Exception as e:
            logger.warning(f"[PreProcess] market context fetch failed: {e}")
            market_snapshot = {}
            market_md = ""

        # Build React agent (no tools)
        system_prompt = (
            "你是 PreProcessAgent，负责整理用户记忆、持仓与市场上下文，生成结构化 JSON 供 master 使用。"
            "只输出 JSON，不要额外文字。"
            "字段：{"
            "focus:{priority,must_cover[]}, "
            "open_questions[], "
            "lessons:{items[]}, "
            "refined_memory:{persona?, long_term_principles?}, "
            "context_summary:{market_brief[], memory_brief[], key_data[], key_events[]}"
            "}。"
            "要求："
            "1) market_brief：2-4 条，提炼指数方向/资金流/宏观或新闻；"
            "2) memory_brief：2-4 条，提炼画像、风险偏好、近期对话指令/限制；"
            "3) key_data：列出关键数字或事实（如指数涨跌、板块净流入、重要指标数值），字符串即可；"
            "4) key_events：列出重要事件（含时间/影响简述）；"
            "5) 发现画像或准则与近期记忆冲突时，用 refined_memory 修正；"
            "6) lessons 可为空但字段保留；focus.must_cover 包含风险边界与行动要点。"
            "One-shot 示例："
            '{"focus":{"priority":"risk_first","must_cover":["风险边界","给出执行步骤"]},'
            '"open_questions":["用户是否允许高频调仓?"],'
            '"lessons":{"items":[{"title":"控制仓位","description":"波动加大时单标的不超过10%"}]},'
            '"refined_memory":{"persona":{"risk":"balanced"},"long_term_principles":["止损5%"]},'
            '"context_summary":{"market_brief":["A股分化，权重略强"],'
            '"memory_brief":["用户偏好低波动收益"],'
            '"key_data":["沪深300 +0.8%","主力净流入前5行业：银行/煤炭"],'
            '"key_events":["明日公布CPI，需关注通胀预期"]}}'
            )

        # Prepare input content
        portfolio_json = json.dumps(portfolio or {}, ensure_ascii=False)[:4000]
        memory_json = json.dumps(memory_blocks, ensure_ascii=False)[:6000]

        prompt = f"""
用户问题：{user_query}

记忆上下文：
{memory_json}

持仓/资产：
{portfolio_json}

市场上下文（Markdown）：
{market_md}
"""

        agent = create_agent(model=llm, tools=[], system_prompt=system_prompt)

        focus_priority = "risk_first"
        focus_must_cover: List[str] = []
        open_questions: List[str] = []
        lessons: List[LessonItem] = []

        try:
            resp = await agent.ainvoke(
                {"messages": [HumanMessage(content=prompt)]}
            )
            content = _extract_response_content(resp)
            data = _safe_json_extract(content) or {}

            focus = data.get("focus") or {}
            focus_priority = focus.get("priority") or focus_priority
            focus_must_cover = focus.get("must_cover") or []
            open_questions = data.get("open_questions") or []

            lessons_block = data.get("lessons") or {}
            items = lessons_block.get("items") or []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("title") and it.get("description"):
                        lessons.append(LessonItem(**it))

            refined = data.get("refined_memory")
            if isinstance(refined, dict):
                if refined.get("persona"):
                    memory_blocks["persona"] = refined["persona"]
                if refined.get("long_term_principles"):
                    memory_blocks["long_term_principles"] = refined["long_term_principles"]

            context_summary = data.get("context_summary")
            if isinstance(context_summary, dict):
                memory_blocks["context_summary"] = context_summary
        except Exception as e:
            logger.warning(f"[PreProcess] React agent parsing failed, fallback defaults: {e}")
            focus_must_cover = ["给出明确的风险边界与可执行建议"]

        pre = PreContext(
            query=QueryBlock(raw=user_query),
            memory_blocks=memory_blocks,
        )
        pre.focus.priority = focus_priority
        pre.focus.must_cover = focus_must_cover
        pre.open_questions = open_questions
        pre.lessons.items = lessons
        pre.market_snapshot = market_snapshot
        pre.rendered_market_context_markdown = market_md
        pre.rendered_pre_context_markdown = _render_precontext_markdown(pre)
        pre.rendered_markdown = pre.rendered_pre_context_markdown  # backward compatibility
        logger.info(f"[PreProcess] Generated Pre Context Markdown:\n{pre.rendered_pre_context_markdown}")
        return pre
