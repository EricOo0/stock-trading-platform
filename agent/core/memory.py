"""Conversation memory management for the agent."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: str = Field(description="Message role: user, assistant, or system")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMemory:
    """
    Manages conversation history for the agent.
    
    This is a simple in-memory implementation. For production,
    you might want to use:
    - Redis for distributed sessions
    - Database for persistent storage
    - LangChain's built-in memory classes
    """
    
    def __init__(self, max_messages: int = 20):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.max_messages = max_messages
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
        """
        Get conversation messages.
        
        Args:
            last_n: If specified, return only the last N messages
            
        Returns:
            List of messages
        """
        if last_n is None:
            return self.messages
        return self.messages[-last_n:]
    
    def get_chat_history(self) -> str:
        """
        Get formatted chat history for prompts.
        
        Returns:
            Formatted string of chat history
        """
        if not self.messages:
            return "No previous conversation."
        
        history_lines = []
        for msg in self.messages:
            prefix = "Human" if msg.role == "user" else "Assistant"
            history_lines.append(f"{prefix}: {msg.content}")
        
        return "\n".join(history_lines)
    
    def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages = []


class MemoryManager:
    """
    Manages multiple conversation sessions.
    
    Maps session IDs to ConversationMemory instances.
    """
    
    def __init__(self):
        """Initialize memory manager."""
        self.sessions: Dict[str, ConversationMemory] = {}
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """
        Get or create a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationMemory instance
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory()
        return self.sessions[session_id]
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a conversation session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
