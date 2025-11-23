import sys
import os
import asyncio
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Literal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config

class Route(BaseModel):
    """Select the next role."""
    next: Literal["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator", "FINISH"] = Field(..., description="The next agent to act or FINISH")

async def debug_tool_choice():
    config = get_config()
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=config.llm.temperature,
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a supervisor. Route the query to the right expert."),
        ("human", "{query}"),
    ])

    # Test 1: Explicit dict format
    print("\n--- Test 1: tool_choice explicit dict ---")
    try:
        chain = prompt | llm.bind_tools([Route], tool_choice={"type": "function", "function": {"name": "Route"}})
        result = await chain.ainvoke({"query": "Analyze Apple stock"})
        print(f"Result: {result.tool_calls}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: String format (which failed before)
    print("\n--- Test 2: tool_choice string 'Route' ---")
    try:
        chain = prompt | llm.bind_tools([Route], tool_choice="Route")
        result = await chain.ainvoke({"query": "Analyze Apple stock"})
        print(f"Result: {result.tool_calls}")
    except Exception as e:
        print(f"Error: {e}")
        
    # Test 3: 'required' (if supported)
    print("\n--- Test 3: tool_choice 'required' ---")
    try:
        chain = prompt | llm.bind_tools([Route], tool_choice="required")
        result = await chain.ainvoke({"query": "Analyze Apple stock"})
        print(f"Result: {result.tool_calls}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tool_choice())
