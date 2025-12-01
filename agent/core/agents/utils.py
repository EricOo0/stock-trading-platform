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

async def run_react_agent(agent, tools, messages, max_iterations=5, event_bus=None, session_id=None, agent_name="ReAct Agent"):
    """
    Run an agent in a ReAct loop (Reason-Act-Observe).
    Returns the final response and execution steps.
    """
    from langchain_core.messages import ToolMessage
    
    if hasattr(agent, 'name'):
        agent_name = agent.name
    
    logger.info(f"{agent_name}: Starting execution loop...")
    
    steps = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"{agent_name}: Iteration {iteration}/{max_iterations}")
        
        # Publish thinking event
        if event_bus and session_id:
            from core.bus import Event
            await event_bus.publish(Event(
                type="agent_status_change",
                session_id=session_id,
                agent=agent_name,
                content=f"Thinking (Iteration {iteration})...",
                metadata={"status": "thinking", "iteration": iteration}
            ))
        
        # Invoke agent
        # Note: agent.invoke is sync, but we are in async function. 
        # In a real async app we might want to run this in a thread pool if it blocks.
        # For now we assume it's fast enough or we use ainvoke if available.
        if hasattr(agent, "ainvoke"):
            result = await agent.ainvoke({"messages": messages})
        else:
            result = agent.invoke({"messages": messages})
        
        # Check if agent wants to use tools
        if not result.tool_calls:
            # Agent has reached a conclusion
            logger.info(f"{agent_name}: Final Conclusion Reached: {result.content[:100]}...")
            
            # Publish speaking event
            if event_bus and session_id:
                from core.bus import Event
                await event_bus.publish(Event(
                    type="agent_message",
                    session_id=session_id,
                    agent=agent_name,
                    content=result.content,
                    metadata={"status": "speaking"}
                ))
            
            return {
                "response": result.content,
                "steps": steps
            }
        
        # Execute tool calls
        for tool_call in result.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            logger.info(f"{agent_name}: I need to use tool '{tool_name}' with args: {tool_args}")
            
            # Publish tool call event
            if event_bus and session_id:
                from core.bus import Event
                await event_bus.publish(Event(
                    type="tool_call",
                    session_id=session_id,
                    agent=agent_name,
                    content=f"Calling tool {tool_name}",
                    metadata={
                        "tool": tool_name,
                        "input": tool_args,
                        "iteration": iteration
                    }
                ))
            
            # Find and execute the tool
            tool_result = None
            for tool in tools:
                if tool.name == tool_name:
                    try:
                        # Support async tools
                        if hasattr(tool, "ainvoke"):
                            tool_result = await tool.ainvoke(tool_args)
                        else:
                            tool_result = tool.invoke(tool_args)
                        break
                    except Exception as e:
                        logger.error(f"{agent_name}: Tool '{tool_name}' execution failed: {e}")
                        tool_result = f"Error: {str(e)}"
                        break
            
            if tool_result is None:
                tool_result = f"Tool '{tool_name}' not found"
            
            # Log the step
            steps.append({
                "index": len(steps) + 1,
                "tool": tool_name,
                "args": tool_args,
                "result": str(tool_result)[:200]  # Truncate long results
            })
            
            # Add tool result to messages
            messages = messages + [result] + [ToolMessage(content=str(tool_result), tool_call_id=tool_call['id'])]
    
    # Max iterations reached
    logger.warning(f"{agent_name}: Max iterations reached without final conclusion.")
    return {
        "response": "Max iterations reached. Partial results available.",
        "steps": steps
    }
