from backend.app.services.research.job_manager import JobManager
from backend.infrastructure.config.loader import config
from backend.app.agents.research.tools import tools
from backend.app.agents.research.callbacks import ResearchAgentCallback
from backend.app.agents.research.prompts import RESEARCH_SYSTEM_PROMPT
from langchain.agents import create_agent
from typing import Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)


def _format_memory_context(context: Dict[str, Any]) -> str:
    """Format structured memory context into Markdown text for LLM."""
    if not context:
        return ""

    formatted_parts = []

    # 1. User Persona (Prioritize structured data)
    persona = context.get("user_persona")
    if persona and isinstance(persona, dict) and persona.get("last_updated"):
        p_str = f"User Persona (Last Updated: {persona['last_updated']}):\n"
        p_str += f"- Risk Preference: {persona.get('risk_preference', 'Balanced')}\n"
        p_str += f"- Investment Style: {', '.join(persona.get('investment_style', []))}\n"
        p_str += f"- Analysis Habits: {', '.join(persona.get('analysis_habits', []))}\n"
        p_str += f"- Observed Traits: {', '.join(persona.get('observed_traits', []))}"
        formatted_parts.append(f"### Long-term User Persona:\n{p_str}")
    else:
        # Fallback to semantic_memory string if structured persona is missing
        semantic = context.get("semantic_memory", [])
        if semantic and isinstance(semantic, list) and len(semantic) > 0:
            content = semantic[0].get("content", "")
            if content:
                formatted_parts.append(f"### Long-term User Persona & Principles:\n{content}")

    # 2. Episodic Historical Insights (MTM)
    episodic = context.get("episodic_memory", [])
    if episodic and isinstance(episodic, list):
        lines = []
        for item in episodic:
            content = item.get("content", "")
            meta = item.get("metadata", {})
            # Example format: [2025-12-26] NVDA: Bullish logic...
            ts = meta.get("timestamp", "")[:10] if meta.get("timestamp") else "Unknown Date"
            lines.append(f"- [{ts}] {content}")
        
        if lines:
            formatted_parts.append("### Relevant Historical Insights:\n" + "\n".join(lines))

    # 3. Recent Previous Conversations (STM)
    working = context.get("working_memory", [])
    if working and isinstance(working, list):
        # We only show these as "background" if we are at the start of a job
        lines = []
        for msg in working[-5:]: # Keep last 5 for context
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        
        if lines:
            formatted_parts.append("### Recent Previous Conversations:\n" + "\n".join(lines))

    return "\n\n".join(formatted_parts)


async def run_agent(job_id: str, query: str):
    """
    Entry point to run the research agent using the modern create_agent factory.
    This creates a graph-based agent (LangGraph under the hood).
    """
    job_manager = JobManager()
    job = job_manager.get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found during run_agent")
        return

    user_id = job.user_id or "default_user"
    callback = ResearchAgentCallback(job_id, user_id=user_id)

    # Load config
    model_name = config.get("model", "gpt-4o")
    base_url = config.get("api_url")

    # Smart API Key Selection to handle placeholders
    openai_key = config.get_api_key("openai")
    siliconflow_key = config.get_api_key("siliconflow")

    # Filter out dummy keys (common in example configs)
    if openai_key and ("xxxx" in openai_key or openai_key.startswith("sk-xxx")):
        openai_key = None

    # Default to OpenAI key (if valid) or SiliconFlow key or Env Var
    api_key = openai_key or siliconflow_key or os.environ.get("OPENAI_API_KEY")

    # Override: If base_url explicitly points to siliconflow, prioritize that key
    if base_url and "siliconflow" in base_url and siliconflow_key:
        api_key = siliconflow_key

    # 1. Create Agent Graph
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from backend.infrastructure.adk.core.memory_client import MemoryClient

    # 0. Initialize Memory Client
    memory_client = MemoryClient(user_id=user_id, agent_id="research_agent")

    llm = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=0,
        streaming=True,
    )

    try:
        logger.info(f"Starting run_agent for job_id={job_id} with query='{query}'")

        graph = create_agent(
            model=llm,  # Passing the initialized LLM object
            tools=tools,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
        )

        # 2. Reconstruct Conversation History
        # We need to fetch previous events to build the chat history
        # History strategy:
        # - System Prompt (Handled by create_agent)
        # - Original Query -> HumanMessage
        # - Previous Turn Output -> AIMessage
        # - Previous User Remark -> HumanMessage

        job = job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found during run_agent")
            return

        events = job_manager.get_events(job_id)
        logger.info(f"Loaded {len(events)} events for history reconstruction")

        messages = []

        # 1.5 Load Memory Context
        memory_context = memory_client.get_context(query)
        if memory_context:
            # 使用格式化工具将结构化数据转为文本
            context_str = _format_memory_context(memory_context)

            if context_str:
                messages.append(
                    SystemMessage(
                        content=f"You have the following historical context about the user and previous research:\n{context_str}\nPlease use this to inform your analysis and reflect on past judgements if relevant."
                    )
                )

        # Add initial query as a SystemMessage to provide context without being the primary instruction
        if job.query:
            messages.append(
                SystemMessage(content=f"Research Background Context: {job.query}")
            )

        # Replay history
        for event in events:
            if event.type == "status" and event.payload.get("status") == "completed":
                output = event.payload.get("output", "")
                if output:
                    messages.append(AIMessage(content=str(output)))
            elif event.type == "user_remark":
                content = event.payload.get("content", "")
                if content:
                    messages.append(HumanMessage(content=content))

        # If the current 'query' arg is essentially the latest remark (passed from add_remark),
        # we check if it's already in the events.
        # add_remark adds the event BEFORE calling run_agent.
        # So 'query' (the remark) is likely the last 'user_remark' event.
        # To avoid duplication, we should check.
        # However, run_agent is also called for the initial run where query=job.query.

        # Simplified Logic:
        # The 'messages' list acts as the history.
        # The agent needs a *current* input.
        # In LangGraph agent, input is usually {"messages": [NewMessage]}.
        # If we pass a list of messages, the last one is treated as the input.

        # Case 1: Initial Run
        # job.query is set. events is empty. messages = [HumanMessage(job.query)].

        # Case 2: Multi-turn (Remark)
        # job.query is set. events has old turns + new remark.
        # messages will contain [Human(original), AI(answer), Human(new_remark)].
        # We just pass this full list.

        # Verify if 'query' param matches the last message.
        # If run_agent was called with a new remark, it should correspond to the last event.
        # If messages is empty (shouldn't happen if job exists), use query.
        if not messages and query:
            messages.append(HumanMessage(content=query))

        # Robustness: Check if the last message is effectively the query.
        # If the events sync missed the latest remark, or if logic above failed,
        # we manually ensure the agent receives the latest instruction.
        last_content = None
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                last_content = last_msg.content

        if query and last_content != query:
            logger.info(
                f"Query/Remark '{query}' not found at end of history. Appending manually."
            )
            messages.append(HumanMessage(content=query))

        # Sync current query/remark to Memory STM
        if query:
            memory_client.add_memory(query, role="user", metadata={"job_id": job_id})

        # Log constructed messages
        for i, m in enumerate(messages):
            logger.info(f"Message {i} [{m.type}]: {str(m.content)[:50]}...")

        inputs = {"messages": messages}

        # 3. Execution
        # The new agent returns a graph that we stream or invoke.
        # We need to bridge the graph stream events to our ResearchAgentCallback.

        # Trying standard invoke with callbacks config first, as LangGraph usually supports it.
        result = await graph.ainvoke(inputs, config={"callbacks": [callback]})
        logger.info(f"Agent finished with result: {result}")

    except Exception as e:
        logger.error(f"Agent failed: {e}")
        # JobManager().append_event(job_id, "status", {
        #     "status": "failed", "error": str(e)})

        # Update Job Status in DB
        job_manager.update_job_status(job_id, "failed", output=str(e))

        from backend.app.services.research.stream_manager import stream_manager
        import json

        await stream_manager.push_event(
            job_id, "status", json.dumps({"status": "failed", "error": str(e)})
        )


if __name__ == "__main__":
    import asyncio
    from backend.infrastructure.adk.core.llm import configure_environment
    from backend.infrastructure.database.engine import create_db_and_tables

    # Setup for standalone run
    configure_environment()
    create_db_and_tables()

    asyncio.run(run_agent("test", "Research NVIDIA"))
