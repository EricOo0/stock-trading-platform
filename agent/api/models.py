"""Pydantic models for API requests and responses."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(description="User message")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")


class ToolCall(BaseModel):
    """Represents a single tool call made by the agent."""
    tool_name: str = Field(description="Name of the tool called")
    tool_input: Any = Field(description="Input parameters to the tool (can be string or dict)")
    tool_output: Any = Field(description="Output from the tool")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(description="Agent's response")
    session_id: str = Field(description="Session ID")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools called during this interaction")
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(default=None, description="Error message if any")


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    api_base: Optional[str] = Field(default=None, description="API base URL")
    model: Optional[str] = Field(default=None, description="Model name")
    temperature: Optional[float] = Field(default=None, ge=0, le=2, description="Temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Max tokens")


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration update."""
    success: bool = Field(description="Whether the update was successful")
    message: str = Field(description="Success or error message")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Updated configuration")


class ToolInfo(BaseModel):
    """Information about a single tool."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")


class ToolsResponse(BaseModel):
    """Response model for tools list endpoint."""
    tools: List[ToolInfo] = Field(description="List of available tools")
    count: int = Field(description="Number of tools")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(description="Service status")
    version: str = Field(description="Service version")
    tools_loaded: int = Field(description="Number of tools loaded")
