"""API routes for the stock analysis agent."""

import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from api.models import (
    ChatRequest, ChatResponse, ToolCall,
    ConfigUpdateRequest, ConfigUpdateResponse,
    ToolsResponse, ToolInfo, HealthResponse
)
from core.config import Config, get_config, set_config, LLMConfig
from core.agent import StockAnalysisAgent
from core.memory import MemoryManager

# Initialize router
router = APIRouter(prefix="/api", tags=["agent"])

# Global instances
_agent: StockAnalysisAgent = None
_memory_manager = MemoryManager()


def get_agent() -> StockAnalysisAgent:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        config = get_config()
        _agent = StockAnalysisAgent(config)
    return _agent


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the stock analysis agent.
    
    The agent will use available tools to answer stock-related questions.
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        memory = _memory_manager.get_or_create_session(session_id)
        
        # Get agent
        agent = get_agent()
        
        # Run agent
        result = await agent.run(
            query=request.message,
            memory=memory
        )
        
        # Parse tool calls from intermediate steps
        tool_calls = []
        for step in result.get("intermediate_steps", []):
            if isinstance(step, dict):
                # Handle LangGraph format
                agent_name = step.get("agent")
                if agent_name: # Only include steps where agent is defined
                    tool_calls.append(ToolCall(
                        tool_name=agent_name,
                        tool_input={}, # Input is not explicitly available in this simplified format
                        tool_output=step.get("content", "")
                    ))
            elif isinstance(step, (list, tuple)) and len(step) >= 2:
                # Handle legacy ReAct format
                action, observation = step[0], step[1]
                tool_calls.append(ToolCall(
                    tool_name=action.tool if hasattr(action, 'tool') else "unknown",
                    tool_input=action.tool_input if hasattr(action, 'tool_input') else {},
                    tool_output=observation
                ))
        
        return ChatResponse(
            response=result.get("output", ""),
            session_id=session_id,
            tool_calls=tool_calls,
            success=result.get("success", True),
            error=result.get("error")
        )
        
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat with the stock analysis agent.
    Returns NDJSON events.
    """
    try:
        agent = get_agent()
        
        async def event_generator():
            import json
            async for event in agent.stream_run(request.message):
                yield json.dumps(event) + "\n"
                
        from fastapi.responses import StreamingResponse
        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
        
    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/config", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    Update agent configuration (API key, model, etc.).
    
    This will reload the agent with new configuration.
    """
    try:
        global _agent
        
        # Get current config
        config = get_config()
        
        # Update LLM config
        llm_data = config.llm.model_dump()
        if request.api_key is not None:
            llm_data["api_key"] = request.api_key
        if request.api_base is not None:
            llm_data["api_base"] = request.api_base
        if request.model is not None:
            llm_data["model"] = request.model
        if request.temperature is not None:
            llm_data["temperature"] = request.temperature
        if request.max_tokens is not None:
            llm_data["max_tokens"] = request.max_tokens
        
        config.llm = LLMConfig(**llm_data)
        
        # Update global config
        set_config(config)
        
        # Reload agent
        _agent = StockAnalysisAgent(config)
        
        logger.info("Configuration updated successfully")
        
        return ConfigUpdateResponse(
            success=True,
            message="Configuration updated successfully",
            config={
                "model": config.llm.model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens
            }
        )
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        return ConfigUpdateResponse(
            success=False,
            message=f"Failed to update configuration: {str(e)}"
        )


@router.get("/tools", response_model=ToolsResponse)
async def list_tools():
    """
    List all available tools the agent can use.
    """
    try:
        agent = get_agent()
        tool_names = agent.get_available_tools()
        
        # Get tool details
        tools_info = []
        for tool in agent.tools:
            tools_info.append(ToolInfo(
                name=tool.name,
                description=tool.description
            ))
        
        return ToolsResponse(
            tools=tools_info,
            count=len(tools_info)
        )
        
    except Exception as e:
        logger.error(f"Tools list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        agent = get_agent()
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            tools_loaded=len(agent.tools)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session."""
    try:
        _memory_manager.delete_session(session_id)
        return {"success": True, "message": f"Session {session_id} deleted"}
    except Exception as e:
        logger.error(f"Session deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
