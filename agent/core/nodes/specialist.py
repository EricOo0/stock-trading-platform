from loguru import logger
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    """Helper function to create an agent node."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
    
    chain = prompt | llm_with_tools
    return chain

def agent_node(state, agent, name):
    """Generic node for specialist agents."""
    # Log inputs for the worker agent
    logger.info(f"DEBUG: --- {name} Input Messages ---")
    for msg in state["messages"]:
        logger.info(f"  [{msg.type}]: {msg.content}")
    
    # Prepare inputs
    messages = state["messages"]
    
    # Fallback: If the last message is an AI message (e.g. from previous turn) and no instruction was added,
    # we might need to prompt it. But with the new Planner, this shouldn't happen often.
    if isinstance(messages[-1], AIMessage):
         # Double check we didn't already add a HumanMessage
         messages = list(messages) + [HumanMessage(content="You have been assigned this task. Use your tools to gather the required evidence based on the Research Brief and previous context.")]
        
    result = agent.invoke({"messages": messages})
    
    # Log output for the worker agent
    logger.info(f"DEBUG: --- {name} Output ---")
    logger.info(f"{result}")

    # Check for empty content
    if not result.content and not result.tool_calls:
        logger.warning(f"DEBUG: {name} returned empty content. Replacing with default.")
        result.content = "I have completed the task."

    # We convert the result to a format that fits into the state
    if isinstance(result, AIMessage):
        result.name = name
    return {"messages": [result]}
