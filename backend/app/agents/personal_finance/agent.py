import json
import logging
import asyncio
from typing import List, Dict, Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from backend.infrastructure.config.loader import config
from backend.app.agents.personal_finance.state import AgentState
from backend.app.agents.personal_finance.models import RecommendationCard, RecommendationAction
from backend.app.agents.personal_finance.prompts import MASTER_AGENT_SYSTEM_PROMPT
from backend.app.agents.personal_finance.tools import (
    run_macro_analysis,
    run_market_analysis,
    run_technical_analysis,
    run_news_analysis,
    run_daily_review_analysis
)
from backend.infrastructure.adk.core.memory_client import MemoryClient

logger = logging.getLogger(__name__)

# --- Node Implementations ---

def get_llm():
    """Configures and returns the LLM instance."""
    openai_key = config.get_api_key("openai")
    silicon_key = config.get_api_key("siliconflow")
    base_url = config.get("api_url")
    model_name = config.get("model", "gpt-4o")
    
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
        
    # Final fallback if both are somehow valid but we prefer one?
    # Actually, just ensure we have A key.
    if not api_key and silicon_key:
        api_key = silicon_key
        
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.3
    )

async def planner_node(state: AgentState):
    """
    Decides which sub-agents to invoke based on user query and portfolio.
    Also retrieves Memory Context from the Memory System.
    """
    logger.info("Entering Planner Node")
    llm = get_llm()
    
    messages = state["messages"]
    portfolio = state["portfolio"]
    user_id = state.get("user_id", "default_user")
    session_id = state.get("session_id", "default_session")
    
    # --- Memory Retrieval ---
    memory_context = {}
    try:
        # Assuming Memory Service runs on default port or configured in config
        # Use a safe fallback for base_url
        memory_url = config.get("memory_service_url", "http://localhost:10000")
        client = MemoryClient(base_url=memory_url, user_id=user_id, agent_id="personal_finance")
        
        user_query = messages[-1].content
        # Get context asynchronously? MemoryClient is synchronous.
        # Run in thread executor to avoid blocking
        memory_context = await asyncio.to_thread(client.get_context, user_query, session_id)
        logger.info(f"Retrieved memory context keys: {list(memory_context.keys())}")
        
    except Exception as e:
        logger.warning(f"Failed to retrieve memory context: {e}")
        memory_context = {}

    # Format memory for prompt
    persona = memory_context.get("persona", {})
    principles = memory_context.get("principles", [])
    stm = memory_context.get("stm", []) # Short term memory
    
    memory_str = ""
    if persona:
        memory_str += f"\n用户画像: {json.dumps(persona, ensure_ascii=False)}"
    if principles:
        memory_str += f"\n长期原则: {json.dumps(principles, ensure_ascii=False)}"
    if stm:
        # Only take last 2 for brevity if needed, but Planner might need more?
        # Let's just summarize
        memory_str += f"\n近期对话摘要: {len(stm)} 条记录"

    # Simple heuristic + LLM to decide agents
    # For now, we will default to ALL relevant agents for a "comprehensive" check,
    # but let the LLM filter if the request is very specific.
    
    planner_prompt = f"""
    根据用户的查询、投资组合和记忆上下文，确定需要咨询哪些专业智能体。
    
    用户查询: {messages[-1].content}
    投资组合摘要: {len(portfolio.get('assets', []))} 个资产。
    {memory_str}
    
    可用智能体:
    - "macro": 用于广泛的经济背景分析。
    - "market": 用于板块和整体市场情绪分析。
    - "news": 用于特定公司/板块的新闻。
    - "technical": 用于特定股票代码的技术分析。
    - "daily_review": 用于复盘今日走势和资金流向（日内分析）。
    
    返回一个包含单个键 "agents" 的 JSON 对象，其中包含字符串列表。
    示例: {{"agents": ["macro", "news"]}}
    如果需要全面审查，请包含所有智能体。
    """
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a planning assistant."),
            HumanMessage(content=planner_prompt)
        ])
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        
        plan = json.loads(content)
        agents = plan.get("agents", [])
        logger.info(f"Planner decided to call: {agents}")
        
    except Exception as e:
        logger.error(f"Planner failed: {e}, defaulting to all agents.")
        agents = ["macro", "market", "news", "technical", "daily_review"]

    return {"selected_agents": agents, "memory_context": memory_context}

async def executor_node(state: AgentState):
    """
    Executes selected agents in parallel.
    """
    logger.info("Entering Executor Node")
    agents = state["selected_agents"]
    portfolio = state["portfolio"]
    session_id = state.get("session_id", "default")
    messages = state["messages"]
    user_query = messages[-1].content
    
    # Prepare tasks
    tasks = []
    task_names = []
    
    # Extract top symbols for analysis (naive approach: top 3 by market value or just first 3)
    # Ideally, planner should specify THIS, but for now we take top holdings.
    assets = portfolio.get("assets", [])
    # Sort by market value if possible, else take first few
    # Assuming assets have 'market_value' or 'quantity' * 'price'
    # For MVP, take first 3 valid symbols
    symbols = [a['symbol'] for a in assets if a.get('symbol')]
    top_symbols = symbols[:3]
    top_symbols_str = ", ".join(top_symbols)

    if "macro" in agents:
        tasks.append(run_macro_analysis(session_id))
        task_names.append("macro")
        
    if "market" in agents:
        tasks.append(run_market_analysis())
        task_names.append("market")
        
    if "technical" in agents and top_symbols:
        # Technical usually analyzes one by one. For MVP, analyze the most important one or all top 3
        # Let's parallelize technical analysis for top 3
        tech_tasks = [run_technical_analysis(sym, session_id) for sym in top_symbols]
        # We need to gather these sub-technical tasks
        tasks.append(asyncio.gather(*tech_tasks))
        task_names.append("technical")
    elif "technical" in agents:
        # If no symbols, skip technical
        task_names.append("technical_skipped")
        tasks.append(asyncio.sleep(0)) # No op

    if "daily_review" in agents and top_symbols:
        # Similar to technical, analyze top symbols
        review_tasks = [run_daily_review_analysis(sym, session_id) for sym in top_symbols]
        tasks.append(asyncio.gather(*review_tasks))
        task_names.append("daily_review")
    elif "daily_review" in agents:
        task_names.append("daily_review_skipped")
        tasks.append(asyncio.sleep(0))

    if "news" in agents and top_symbols:
        # News for top symbols
        query = f"Latest news and sentiment for {top_symbols_str}"
        tasks.append(run_news_analysis(query, session_id))
        task_names.append("news")
    elif "news" in agents:
        # General market news if no symbols
        tasks.append(run_news_analysis("Latest market news", session_id))
        task_names.append("news")

    # Execute
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Map results back to state
    update = {}
    for name, res in zip(task_names, results):
        if name == "technical":
            # result is a list of strings
            if isinstance(res, list):
                update["technical_analysis"] = "\n\n".join([str(r) for r in res])
            else:
                 update["technical_analysis"] = str(res)
        elif name == "technical_skipped":
            update["technical_analysis"] = "No specific assets identified for technical analysis."
        elif name == "daily_review":
            if isinstance(res, list):
                update["daily_review_analysis"] = "\n\n".join([str(r) for r in res])
            else:
                update["daily_review_analysis"] = str(res)
        elif name == "daily_review_skipped":
            update["daily_review_analysis"] = "No specific assets identified for daily review."
        elif name == "macro":
            update["macro_analysis"] = str(res)
        elif name == "market":
            update["market_analysis"] = str(res)
        elif name == "news":
            update["news_analysis"] = str(res)
            
    return update

async def synthesizer_node(state: AgentState):
    """
    Synthesizes all reports into a final advice and structured cards.
    Also saves interaction to Memory System.
    """
    logger.info("Entering Synthesizer Node")
    llm = get_llm()
    
    portfolio = state["portfolio"]
    messages = state["messages"]
    memory_context = state.get("memory_context", {})
    user_id = state.get("user_id", "default_user")
    
    # Format memory for synthesis context (Reflection is important here)
    reflection = memory_context.get("reflection", "")
    persona = memory_context.get("persona", {})
    
    memory_insight = ""
    if reflection:
        memory_insight += f"\n[记忆自省/冲突检测]: {reflection}"
    if persona:
        risk_pref = persona.get("risk_preference", "unknown")
        style = persona.get("investment_style", "unknown")
        memory_insight += f"\n[用户偏好]: 风险偏好: {risk_pref}, 风格: {style}"

    # Construct Context
    context = f"""
    用户投资组合摘要: {json.dumps(portfolio, default=str)}
    用户查询: {messages[-1].content}
    {memory_insight}
    
    --- 智能体报告 ---
    宏观分析 (Macro Analysis):
    {state.get('macro_analysis', 'N/A')}
    
    市场分析 (Market Analysis):
    {state.get('market_analysis', 'N/A')}
    
    今日复盘 (Daily Review):
    {state.get('daily_review_analysis', 'N/A')}
    
    技术分析 (Technical Analysis):
    {state.get('technical_analysis', 'N/A')}
    
    新闻分析 (News Analysis):
    {state.get('news_analysis', 'N/A')}
    """
    
    # 1. Generate Structured Recommendations (Cards)
    # We ask for JSON output for cards
    card_prompt = f"""
    {MASTER_AGENT_SYSTEM_PROMPT}
    
    根据以上分析，为用户生成 1-3 张高价值的“推荐卡片”。
    
    **卡片生成策略**：
    1. **调仓建议**：如果有明确的风险或机会，建议买入/卖出特定标的。
    2. **机会发现**：基于市场分析，推荐关注的热门板块或潜力个股。
    3. **风险预警**：对持仓中的高风险资产发出预警。
    
    分析数据:
    {context}
    
    返回一个包含键 "cards" 的 JSON 对象，其中包含符合此模式的对象列表：
    {{
        "title": "简短有力的标题 (e.g. '建议买入：半导体ETF')",
        "description": "详细的理由和操作建议 (e.g. '资金持续流入，技术面突破阻力位，建议关注 sh512480')",
        "asset_id": "相关的股票/基金代码 (e.g. 'sh512480'，如果没有具体代码则留空)",
        "action": "buy" | "sell" | "hold" | "monitor",
        "confidence_score": 0.0 到 1.0 (置信度),
        "risk_level": "low" | "medium" | "high"
    }}
    
    注意：不要生成空泛的卡片。如果没有具体建议，可以生成“继续持有”并解释宏观理由。
    """
    
    cards = []
    try:
        card_response = await llm.ainvoke([HumanMessage(content=card_prompt)])
        content = card_response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        data = json.loads(content)
        for item in data.get("cards", []):
            cards.append(RecommendationCard(**item))
    except Exception as e:
        logger.error(f"Failed to generate cards: {e}")
        # Fallback card
        cards.append(RecommendationCard(
            title="Portfolio Review Complete",
            description="Please review the detailed report below.",
            action=RecommendationAction.HOLD,
            confidence_score=0.5,
            risk_level="medium"
        ))

    # 2. Generate Final Report (Markdown)
    report_prompt = f"""
    {MASTER_AGENT_SYSTEM_PROMPT}
    
    将智能体报告综合成一份连贯、易读的 Markdown 报告给用户。
    直接回答他们的查询。使用章节和要点。
    强调子智能体识别出的关键风险和机会。
    
    上下文:
    {context}
    """
    
    report_response = await llm.ainvoke([HumanMessage(content=report_prompt)])
    final_report = report_response.content
    
    # --- Memory Saving ---
    try:
        memory_url = config.get("memory_service_url", "http://localhost:10000")
        client = MemoryClient(base_url=memory_url, user_id=user_id, agent_id="personal_finance")
        
        user_query = messages[-1].content
        
        # We perform these operations in background/async to not block response
        async def save_memory():
            # 1. Add User Query
            client.add_memory(user_query, role="user")
            # 2. Add Agent Response (Report)
            client.add_memory(final_report, role="assistant", metadata={"type": "report"})
            # 3. Finalize (Trigger archival/evolution)
            # In a real chat loop, finalize might be called at end of session. 
            # Here we call it after each turn for simplicity, or rely on frontend to call it.
            # But the requirement said "finish task save query and output".
            client.finalize()
            logger.info("Memory saved and finalized.")

        asyncio.create_task(save_memory())
        
    except Exception as e:
        logger.error(f"Failed to save memory: {e}")

    return {
        "final_report": final_report,
        "recommendation_cards": cards
    }

# --- Graph Definition ---

def create_personal_finance_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.set_entry_point("planner")
    
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()
