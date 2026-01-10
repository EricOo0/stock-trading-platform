from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.infrastructure.config.loader import config
from .tools import tools
from .prompts import MARKET_ANALYSIS_SYSTEM_PROMPT, MARKET_ANALYSIS_USER_TEMPLATE
import logging
import os

logger = logging.getLogger(__name__)

async def run_market_agent(user_id: str = "default"):
    """
    Run the Market Analysis Agent.
    Returns the final analysis report chunks.
    """
    # Config LLM
    model_name = config.get("model", "gpt-4o")
    base_url = config.get("api_url")
    
    openai_key = config.get_api_key("openai")
    siliconflow_key = config.get_api_key("siliconflow")
    
    if openai_key and ("xxxx" in openai_key or openai_key.startswith("sk-xxx")):
        openai_key = None
        
    api_key = openai_key or siliconflow_key or os.environ.get("OPENAI_API_KEY")
    
    if base_url and "siliconflow" in base_url and siliconflow_key:
        api_key = siliconflow_key

    llm = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=0.3,
        streaming=True,
    )

    # Create Agent
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=MARKET_ANALYSIS_SYSTEM_PROMPT,
    )

    # Input
    input_msg = MARKET_ANALYSIS_USER_TEMPLATE
    
    messages = [HumanMessage(content=input_msg)]
    
    logger.info(f"Starting Market Analysis Agent")
    
    # Execute
    # We want to stream the output
    final_output = ""
    async for event in agent_graph.astream_events({"messages": messages}, version="v1"):
        kind = event["event"]
        
        # Capture the final LLM output (on_chat_model_stream)
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                final_output += content
                yield content

    logger.info(f"Market Agent finished")
