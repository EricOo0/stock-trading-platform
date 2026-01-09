from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.infrastructure.config.loader import config
from .tools import tools
from .prompts import REVIEW_SYSTEM_PROMPT, REVIEW_USER_PROMPT
import logging
import os

logger = logging.getLogger(__name__)

async def run_review_agent(symbol: str, user_id: str = "default"):
    """
    Run the Review Agent for a specific symbol.
    Returns the final review report.
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
        temperature=0.3, # Slightly creative for analysis
        streaming=True,
    )

    # Create Agent
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=REVIEW_SYSTEM_PROMPT,
    )

    # Input
    input_msg = REVIEW_USER_PROMPT.format(symbol=symbol, context="[Data will be fetched by tools]")
    
    messages = [HumanMessage(content=input_msg)]
    
    logger.info(f"Starting Review Agent for {symbol}")
    
    # Execute
    # We want to stream the output
    final_output = ""
    async for event in agent_graph.astream_events({"messages": messages}, version="v1"):
        kind = event["event"]
        
        # Capture the final LLM output (on_chat_model_stream)
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # In a real app, we would yield this to the frontend via SSE
                # For now, we accumulate it to return or print
                final_output += content
                yield content

    logger.info(f"Review Agent finished for {symbol}")
