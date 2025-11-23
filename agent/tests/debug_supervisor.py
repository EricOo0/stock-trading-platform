import sys
import os
import asyncio
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config
from core.prompts import MANAGER_SYSTEM_PROMPT

async def debug_supervisor():
    config = get_config()
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=config.llm.temperature,
        openai_api_key=config.llm.api_key,
        openai_api_base=config.llm.api_base,
    )

    members = ["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator"]
    options = members + ["FINISH"]
    
    system_prompt = (
        MANAGER_SYSTEM_PROMPT + 
        "\n\n" + 
        "Given the conversation above, who should act next?"
        " Or should we FINISH? Select one of: {options}, FINISH."
    ).format(options=str(members))

    # Define tool using Pydantic for bind_tools
    from pydantic import BaseModel, Field
    from typing import Literal

    class Route(BaseModel):
        """Select the next role."""
        next: Literal["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator", "FINISH"] = Field(..., description="The next agent to act or FINISH")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Use bind_tools
    raw_chain = (
        prompt
        | llm.bind_tools([Route])
    )

    messages = [HumanMessage(content="Analyze Apple's stock")]
    
    print("--- Invoking Raw Chain (bind_tools) ---")
    try:
        result = await raw_chain.ainvoke({"messages": messages})
        print(f"Raw Result Type: {type(result)}")
        print(f"Raw Result Content: {result.content}")
        print(f"Raw Result Tool Calls: {result.tool_calls}")
    except Exception as e:
        print(f"Raw Chain Error: {e}")

    # Use JsonOutputToolsParser
    from langchain_core.output_parsers.openai_tools import JsonOutputToolsParser
    print("\n--- Invoking Chain with JsonOutputToolsParser ---")
    parser_chain = raw_chain | JsonOutputToolsParser()
    try:
        parsed_result = await parser_chain.ainvoke({"messages": messages})
        print(f"Parsed Result: {parsed_result}")
    except Exception as e:
        print(f"Parser Chain Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_supervisor())
