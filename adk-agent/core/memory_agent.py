from google.adk.agents import Agent
from google.genai import types
from typing import List, Optional, Any, Callable
from pydantic import PrivateAttr
from .memory_client import MemoryClient

class MemoryAwareAgent(Agent):
    """
    An ADK Agent that automatically integrates with the Memory System.
    Uses before_agent and after_agent callbacks for memory operations.
    """
    agent_id: str
    _memory_client: Any = PrivateAttr()

    def __init__(self, agent_id: str, **kwargs):
        # Set up before/after callbacks for memory
        original_before = kwargs.get('before_agent_callback')
        original_after = kwargs.get('after_agent_callback')
        
        # Wrap callbacks to add memory functionality
        kwargs['before_agent_callback'] = self._create_before_callback(original_before)
        kwargs['after_agent_callback'] = self._create_after_callback(original_after)
        
        # Initialize parent
        super().__init__(agent_id=agent_id, **kwargs)
        
        # Initialize memory client
        self._memory_client = MemoryClient(base_url="http://localhost:10000", agent_id=agent_id)
        print(f"🧠 [MemoryAwareAgent] Initialized for agent: {agent_id}")

    def _create_before_callback(self, original_callback: Optional[Callable]) -> Callable:
        """Create a before_agent callback that injects memory context"""
        async def before_with_memory(callback_context):
            print(f"🧠 [MemoryAwareAgent] before_agent callback triggered")
            
            # Call original callback if exists
            if original_callback:
                result = await original_callback(callback_context=callback_context)
                if result:
                    return result
            
            # Get invocation context
            ctx = callback_context.invocation_context
            
            # Get user query from context
            user_query = self._extract_user_query(ctx)
            if not user_query:
                return None
            
            print(f"🧠 [MemoryAwareAgent] User query: {user_query[:100]}...")
            
            # Retrieve memory context
            try:
                context = self._memory_client.get_context(user_query)
                if context:
                    context_str = self._format_context(context)
                    if context_str:
                        print(f"🧠 [MemoryAwareAgent] Retrieved memory context ({len(context_str)} chars)")
                        # Inject context into the agent's instruction dynamically
                        memory_content = types.Content(
                            role="system",
                            parts=[types.Part(text=f"MEMORY CONTEXT:\n{context_str}")]
                        )
                        # Prepend to session history
                        if hasattr(ctx, 'session') and hasattr(ctx.session, 'history'):
                            ctx.session.history.insert(0, memory_content)
                    else:
                        print(f"🧠 [MemoryAwareAgent] No relevant memory context")
            except Exception as e:
                print(f"❌ [MemoryAwareAgent] Error retrieving context: {e}")
            
            return None
        
        return before_with_memory

    def _create_after_callback(self, original_callback: Optional[Callable]) -> Callable:
        """Create an after_agent callback that saves to memory"""
        async def after_with_memory(callback_context):
            print(f"🧠 [MemoryAwareAgent] after_agent callback triggered")
            
            # Get invocation context
            ctx = callback_context.invocation_context
            
            # Extract user query and agent response
            user_query = self._extract_user_query(ctx)
            agent_response = self._extract_agent_response(ctx)
            
            if user_query and agent_response:
                try:
                    print(f"🧠 [MemoryAwareAgent] Saving interaction to memory...")
                    self._memory_client.add_memory(user_query, role="user")
                    self._memory_client.add_memory(agent_response, role="agent")
                    print(f"✅ [MemoryAwareAgent] Memory saved successfully")
                except Exception as e:
                    print(f"❌ [MemoryAwareAgent] Error saving to memory: {e}")
            
            # Call original callback if exists
            if original_callback:
                return await original_callback(callback_context=callback_context)
            
            return None
        
        return after_with_memory

    def _extract_user_query(self, ctx) -> str:
        """Extract user query from invocation context"""
        try:
            if hasattr(ctx, 'session') and hasattr(ctx.session, 'history'):
                # Find the last user message
                for msg in reversed(ctx.session.history):
                    if msg.role == "user" and msg.parts:
                        return msg.parts[0].text
        except Exception as e:
            print(f"❌ [MemoryAwareAgent] Error extracting user query: {e}")
        return ""

    def _extract_agent_response(self, ctx) -> str:
        """Extract agent response from invocation context"""
        try:
            if hasattr(ctx, 'session') and hasattr(ctx.session, 'history'):
                # Find the last model message
                for msg in reversed(ctx.session.history):
                    if msg.role == "model" and msg.parts:
                        return msg.parts[0].text
        except Exception as e:
            print(f"❌ [MemoryAwareAgent] Error extracting agent response: {e}")
        return ""

    def _format_context(self, context: dict) -> str:
        """Format memory context for injection"""
        memory_block = []
        
        if context.get('core_principles'):
            memory_block.append(f"### Core Principles & Guidelines:\n{context['core_principles']}")
            
        if context.get('episodic_memory'):
            memory_block.append("### Relevant Past Events:")
            for item in context['episodic_memory']:
                content = item.get('content', '')
                if isinstance(content, dict): 
                    content = f"{content.get('summary', '')} ({content.get('key_findings', '')})"
                memory_block.append(f"- {content}")
                
        if context.get('working_memory'):
            memory_block.append("### Recent Conversation Context:")
            for item in context['working_memory']:
                memory_block.append(f"- [{item.get('role', 'unknown')}]: {item.get('content', '')}")
                
        if not memory_block:
            return ""
            
        return "\n\n" + "\n".join(memory_block)
