from google.adk.agents import Agent
from google.genai import types
from typing import List, Optional, Any
from pydantic import PrivateAttr
from .memory_client import MemoryClient

class MemoryAwareAgent(Agent):
    """
    An ADK Agent that automatically integrates with the Memory System.
    It fetches context before generating and saves history after generating.
    """
    agent_id: str
    _memory_client: Any = PrivateAttr()

    def __init__(self, agent_id: str, **kwargs):
        # kwargs contains fields for Agent (model, name, instruction, tools, description)
        super().__init__(agent_id=agent_id, **kwargs)
        # Initialize the client. PrivateAttr allows setting it on the instance.
        self._memory_client = MemoryClient(base_url="http://localhost:10000", agent_id=agent_id)

    def _inject_context(self, query: str) -> str:
        """Fetch memory context and build an enhanced system instruction segment."""
        context = self._memory_client.get_context(query)
        if not context:
            return ""
            
        # Format the context for the LLM
        # We rely on the core_principles and episodic memory to guide the agent
        memory_block = []
        
        if context.get('core_principles'):
            memory_block.append(f"### Core Principles & Guidelines:\n{context['core_principles']}")
            
        if context.get('episodic_memory'):
            memory_block.append("### Relevant Past Events:")
            for item in context['episodic_memory']:
                content = item.get('content', '')
                if isinstance(content, dict): 
                    # Handle structured event content
                     content = f"{content.get('summary', '')} ({content.get('key_findings', '')})"
                memory_block.append(f"- {content}")
                
        if context.get('working_memory'):
            memory_block.append("### Recent Conversation Context:")
            for item in context['working_memory']:
                memory_block.append(f"- [{item.get('role', 'unknown')}]: {item.get('content', '')}")
                
        if not memory_block:
            return ""
            
        return "\n\n" + "\n".join(memory_block)

    def generate(self, model_client: Any, messages: List[types.Content], **kwargs) -> types.GenerateContentResponse:
        """
        Override the generate method to inject memory.
        """
        # 1. Identify User Query
        user_query = ""
        for msg in messages:
            if msg.role == "user":
                parts = msg.parts
                if parts:
                    user_query = parts[0].text
        
        # 2. Inject Context if we have a query
        if user_query:
            context_str = self._inject_context(user_query)
            if context_str:
                # Add to system instruction dynamically
                # Prepending a system message with context
                memory_msg = types.Content(
                    role="system",
                    parts=[types.Part(text=f"MEMORY CONTEXT:\n{context_str}")]
                )
                # Insert before the last user message
                messages.insert(-1, memory_msg)

        # 3. Call original generate
        response = super().generate(model_client, messages, **kwargs)
        
        # 4. Save Interaction to Memory (Async-like)
        if user_query and response.text:
             # Save User Message
            self._memory_client.add_memory(user_query, role="user")
            # Save Agent Response
            self._memory_client.add_memory(response.text, role="agent")
            
        return response
