import sys
import os
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config

class Route(BaseModel):
    """Select the next role."""
    next: Literal["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator", "FINISH"] = Field(..., description="The next agent to act or FINISH")

async def test_config(name, llm, tool_choice, prompt_msgs):
    print(f"\n--- Testing: {name} ---")
    try:
        if tool_choice == "DEFAULT":
            chain = llm.bind_tools([Route])
        else:
            chain = llm.bind_tools([Route], tool_choice=tool_choice)
            
        result = await chain.ainvoke(prompt_msgs)
        print(f"Success!")
        print(f"Tool Calls: {result.tool_calls}")
        print(f"Content: {result.content}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

async def debug_deepseek_tools():
    config = get_config()
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=config.llm.temperature,
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )

    # Strict prompt similar to what we added
    system_prompt = """You are a supervisor. Route the query to the right expert.
    You MUST call the `Route` tool to select the next agent.
    Do NOT output any conversational text, thoughts, or explanations.
    ONLY output the function call."""
    
    msgs = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Analyze Apple stock")
    ]

    # Test 1: Default (Auto)
    await test_config("Default (Auto)", llm, "DEFAULT", msgs)

    # Test 2: 'required'
    await test_config("'required'", llm, "required", msgs)

    # Test 3: Explicit Dict
    await test_config("Explicit Dict", llm, {"type": "function", "function": {"name": "Route"}}, msgs)
    
    # Test 4: String Name
    await test_config("String Name", llm, "Route", msgs)

    # Test 5: 'none' (Should fail to call tool, but check if it errors)
    await test_config("'none'", llm, "none", msgs)

if __name__ == "__main__":
    asyncio.run(debug_deepseek_tools())
