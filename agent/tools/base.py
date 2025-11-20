"""Base classes and interfaces for agent tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base model for tool input parameters."""
    pass


class ToolOutput(BaseModel):
    """Base model for tool output."""
    success: bool = Field(description="Whether the tool execution was successful")
    result: Any = Field(description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    Tools can be either:
    - Skill Adapters: Wrapping Claude Skills from the skills/ directory
    - MCP Clients: Connecting to external MCP servers
    - Custom Tools: Directly implemented functionality
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the LLM."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool with given parameters.
        
        Returns:
            ToolOutput with execution results
        """
        pass
    
    def to_langchain_tool(self):
        """
        Convert this tool to a LangChain Tool instance.
        
        This method will be implemented to create LangChain-compatible tools.
        """
        raise NotImplementedError("Subclasses must implement to_langchain_tool")
