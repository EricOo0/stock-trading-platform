from loguru import logger
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import CHAIRMAN_SYSTEM_PROMPT
from core.schema import CreatePlan

def create_chairman_chain(chairman_llm: ChatOpenAI):
    """Create the chairman chain with the given LLM."""
    system_prompt = (
        CHAIRMAN_SYSTEM_PROMPT + 
        "\n\n" + 
        "Given the conversation above, who should act next?"
        " Or should we FINISH? Select one of: ['MacroDataInvestigator', 'MarketDataInvestigator', 'SentimentInvestigator', 'WebSearchInvestigator'], FINISH."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | chairman_llm.bind_tools([CreatePlan])

def chairman_node(state: AgentState, chairman_llm: ChatOpenAI):
    """Chairman decides the plan or executes the next step."""
    try:
        plan = state.get("plan", [])
        review_count = state.get("review_count", 0)
        
        # 1. If no plan, generate one
        if not plan:
            logger.info("DEBUG: Chairman generating new plan...")
            
            # Check recursion
            if review_count > 10:
                logger.warning("DEBUG: Recursion limit reached. Forcing FINISH.")
                return {"next": "FINISH", "review_count": review_count}

            chairman_chain = create_chairman_chain(chairman_llm)
            result = chairman_chain.invoke(state)
            
            # Set name for frontend
            result.name = "Chairman"
            
            # Parse tool call
            new_plan = []
            if result.tool_calls:
                tool_call = result.tool_calls[0]
                if tool_call['name'] == 'CreatePlan':
                    args = tool_call['args']
                    if isinstance(args, str):
                        import json
                        args = json.loads(args)
                    
                    steps = args.get('steps', [])
                    # Convert to dicts for state storage
                    new_plan = [step if isinstance(step, dict) else step.dict() for step in steps]
                    
                    logger.info(f"DEBUG: Plan Generated: {len(new_plan)} steps")
                    for i, step in enumerate(new_plan):
                        logger.info(f"  Step {i+1}: {step['agent']} - {step['instruction']}")

            if not new_plan:
                # If Chairman didn't generate a plan, assume we are done or fallback
                logger.info("DEBUG: No plan generated. Finishing.")
                return {"next": "FINISH", "review_count": review_count + 1, "messages": [result]}
            
            # Update local plan variable
            plan = new_plan
            
            # Execute the first step immediately
            current_step = plan[0]
            remaining_plan = plan[1:]
            
            agent_name = current_step['agent']
            instruction = current_step['instruction']
            
            logger.info(f"DEBUG: Executing first step: {agent_name} -> {instruction}")
            
            # Create a HumanMessage to instruct the agent
            instruction_msg = HumanMessage(content=instruction)
            
            # Return the plan, the first instruction, and route to first agent
            return {
                "plan": remaining_plan,  # Store remaining steps
                "messages": [result, instruction_msg],  # Chairman's plan + instruction
                "next": agent_name,  # Route to first agent
                "review_count": review_count + 1
            }

        # 2. Execute next step
        if plan:
            current_step = plan[0]
            remaining_plan = plan[1:]
            
            agent_name = current_step['agent']
            instruction = current_step['instruction']
            
            logger.info(f"DEBUG: Executing Step: {agent_name} -> {instruction}")
            
            # Create a HumanMessage to instruct the agent
            instruction_msg = HumanMessage(content=instruction)
            
            return {
                "next": agent_name,
                "plan": remaining_plan, # Overwrite with remaining steps
                "messages": [instruction_msg],
                "review_count": review_count + 1
            }
        
        return {"next": "FINISH", "review_count": review_count + 1}

    except Exception as e:
        logger.error(f"Chairman error: {e}")
        return {"next": "FINISH", "review_count": state.get("review_count", 0) + 1}
