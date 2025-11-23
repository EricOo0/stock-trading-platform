from loguru import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import CRITIC_SYSTEM_PROMPT

def critic_node(state: AgentState, llm: ChatOpenAI):
    """Reviews evidence and synthesizes final answer."""
    try:
        logger.info("DEBUG: Critic reviewing evidence...")
        
        # Extract only relevant messages (Research Brief + Evidence)
        messages = state["messages"]
        relevant_messages = []
        
        # Find the Research Brief (from Receptionist)
        for msg in messages:
            if hasattr(msg, 'name') and msg.name == "Receptionist":
                relevant_messages.append(msg)
                break
        
        # Collect all evidence from specialists
        specialist_names = ["MarketDataInvestigator", "MacroDataInvestigator", 
                           "SentimentInvestigator", "WebSearchInvestigator"]
        for msg in messages:
            if hasattr(msg, 'name') and msg.name in specialist_names:
                # Only include messages with "EVIDENCE" keyword
                if "EVIDENCE" in msg.content.upper():
                    relevant_messages.append(msg)
        
        logger.info(f"DEBUG: Critic processing {len(relevant_messages)} relevant messages")
        
        # Create chain with filtered messages
        chain = (
            ChatPromptTemplate.from_messages([
                ("system", CRITIC_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ])
            | llm
        )
        
        result = chain.invoke({"messages": relevant_messages})
        logger.info("DEBUG: Critic synthesis complete.")
        
        # Set name for frontend
        result.name = "Critic"
        
        return {"messages": [result]}
    except Exception as e:
        logger.error(f"Critic error: {e}")
        return {"messages": [AIMessage(content="System Error in Critic. Please check logs.", name="Critic")]}
