from loguru import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import RECEPTIONIST_SYSTEM_PROMPT

def receptionist_node(state: AgentState, llm: ChatOpenAI):
    """Analyzes user intent and creates a Research Brief."""
    try:
        logger.info("DEBUG: Receptionist analyzing intent...")
        messages = state["messages"]
        
        chain = (
            ChatPromptTemplate.from_messages([
                ("system", RECEPTIONIST_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ])
            | llm
        )
        result = chain.invoke(state)
        brief = result.content
        logger.info(f"DEBUG: Research Brief: {brief}")
        
        # Set name for frontend
        result.name = "Receptionist"
        
        # Initialize evidence log if not present
        evidence_log = state.get("evidence_log", [])
        
        return {
            "messages": [result],
            "research_brief": brief,
            "evidence_log": evidence_log,
            "review_count": 0
        }
    except Exception as e:
        logger.error(f"Receptionist error: {e}")
        # Fallback: Pass original query as brief
        return {
            "messages": [AIMessage(content="System Error in Receptionist. Proceeding with raw query.", name="Receptionist")],
            "research_brief": state["messages"][-1].content if state["messages"] else "Analyze market",
            "evidence_log": [],
            "review_count": 0
        }
