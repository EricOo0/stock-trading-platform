import functools
from loguru import logger
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from core.config import Config
from core.state import AgentState
from core.prompts import (
    MACRO_AGENT_SYSTEM_PROMPT,
    MARKET_AGENT_SYSTEM_PROMPT,
    SENTIMENT_AGENT_SYSTEM_PROMPT,
    WEB_SEARCH_AGENT_SYSTEM_PROMPT,
)

# Import Skills
from skills.market_data_tool.skill import MarketDataSkill
from skills.macro_data_tool.skill import MacroDataSkill
from skills.sentiment_analysis_tool.skill import SentimentAnalysisSkill
from skills.web_search_tool.skill import WebSearchSkill

# Import Nodes
from core.nodes.receptionist import receptionist_node
from core.nodes.chairman import chairman_node
from core.nodes.critic import critic_node
from core.nodes.specialist import agent_node, create_agent

# --- Graph Construction ---

def create_graph(config: Config):
    # 1. Initialize LLM (Workers)
    # Use low temperature for factual analysis to prevent hallucinations
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=0.1, 
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )
    
    # Chairman LLM (temperature 0 for deterministic planning)
    chairman_llm = ChatOpenAI(
        model=config.llm.model,
        temperature=0.0,
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )
    
    # Critic LLM (temperature 0 for objective, deterministic synthesis)
    critic_llm = ChatOpenAI(
        model=config.llm.model,
        temperature=0.0,
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )

    # 2. Initialize Tools
    macro_tool = MacroDataSkill()
    market_tool = MarketDataSkill(llm=llm)  # Pass LLM for intelligent symbol extraction
    sentiment_tool = SentimentAnalysisSkill()
    search_tool = WebSearchSkill()

    # 3. Create Agents
    # Macro Agent
    macro_agent = create_agent(llm, [macro_tool], MACRO_AGENT_SYSTEM_PROMPT)
    macro_node = functools.partial(agent_node, agent=macro_agent, name="MacroDataInvestigator")

    # Market Agent
    market_agent = create_agent(llm, [market_tool], MARKET_AGENT_SYSTEM_PROMPT)
    market_node = functools.partial(agent_node, agent=market_agent, name="MarketDataInvestigator")

    # Sentiment Agent
    sentiment_agent = create_agent(llm, [sentiment_tool], SENTIMENT_AGENT_SYSTEM_PROMPT)
    sentiment_node = functools.partial(agent_node, agent=sentiment_agent, name="SentimentInvestigator")

    # Web Search Agent
    search_agent = create_agent(llm, [search_tool], WEB_SEARCH_AGENT_SYSTEM_PROMPT)
    search_node = functools.partial(agent_node, agent=search_agent, name="WebSearchInvestigator")
    
    # Create wrapper functions for nodes that need LLM
    def receptionist_wrapper(state):
        return receptionist_node(state, llm)
    
    def chairman_wrapper(state):
        return chairman_node(state, chairman_llm)
    
    def critic_wrapper(state):
        return critic_node(state, critic_llm)  # Use dedicated critic_llm with temp 0.0

    # 4. Build StateGraph
    workflow = StateGraph(AgentState)

    workflow.add_node("Receptionist", receptionist_wrapper)
    workflow.add_node("Chairman", chairman_wrapper)
    workflow.add_node("Critic", critic_wrapper)
    
    workflow.add_node("MacroDataInvestigator", macro_node)
    workflow.add_node("MarketDataInvestigator", market_node)
    workflow.add_node("SentimentInvestigator", sentiment_node)
    workflow.add_node("WebSearchInvestigator", search_node)

    # Create ToolNodes for each agent
    macro_tools_node = ToolNode([macro_tool])
    market_tools_node = ToolNode([market_tool])
    sentiment_tools_node = ToolNode([sentiment_tool])
    search_tools_node = ToolNode([search_tool])

    workflow.add_node("MacroDataTools", macro_tools_node)
    workflow.add_node("MarketDataTools", market_tools_node)
    workflow.add_node("SentimentTools", sentiment_tools_node)
    workflow.add_node("WebSearchTools", search_tools_node)

    # Helper for conditional edges
    def should_continue(state):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return "chairman"

    # Edges
    workflow.add_edge("Receptionist", "Chairman")
    workflow.add_edge("Critic", END)

    # Edges for Macro Agent
    workflow.add_conditional_edges(
        "MacroDataInvestigator",
        should_continue,
        {
            "tools": "MacroDataTools",
            "chairman": "Chairman"
        }
    )
    workflow.add_edge("MacroDataTools", "MacroDataInvestigator")

    # Edges for Market Agent
    workflow.add_conditional_edges(
        "MarketDataInvestigator",
        should_continue,
        {
            "tools": "MarketDataTools",
            "chairman": "Chairman"
        }
    )
    workflow.add_edge("MarketDataTools", "MarketDataInvestigator")

    # Edges for Sentiment Agent
    workflow.add_conditional_edges(
        "SentimentInvestigator",
        should_continue,
        {
            "tools": "SentimentTools",
            "chairman": "Chairman"
        }
    )
    workflow.add_edge("SentimentTools", "SentimentInvestigator")

    # Edges for Web Search Agent
    workflow.add_conditional_edges(
        "WebSearchInvestigator",
        should_continue,
        {
            "tools": "WebSearchTools",
            "chairman": "Chairman"
        }
    )
    workflow.add_edge("WebSearchTools", "WebSearchInvestigator")

    # Conditional Edges from Chairman
    members = ["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator"]
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = "Critic" # Route FINISH to Critic
    conditional_map["Critic"] = "Critic" # Explicit route
    
    workflow.add_conditional_edges(
        "Chairman",
        lambda x: x["next"],
        conditional_map
    )

    workflow.set_entry_point("Receptionist")

    # Compile
    return workflow.compile()
