"""Tool manager for registering and managing agent tools."""

from typing import List, Dict, Any
from loguru import logger

from langchain.tools import Tool

from tools.base import BaseTool
from tools.skill_adapter import SkillAdapter
from core.config import Config


class ToolManager:
    """
    Manages all tools available to the agent.
    
    This includes:
    - Skill Adapters (market_data_tool, etc.)
    - MCP Clients (future)
    - Custom tools (future)
    """
    
    def __init__(self, config: Config):
        """
        Initialize the tool manager.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all available tools based on configuration."""
        # Register Skills
        if self.config.skills.enabled:
            try:
                skill_adapter = SkillAdapter(skill_path=self.config.skills.path)
                self.tools[skill_adapter.name] = skill_adapter
                logger.info(f"Registered skill tool: {skill_adapter.name}")
            except Exception as e:
                logger.error(f"Failed to register skill adapter: {e}")
        
        # Future: Register MCP tools
        # for mcp_config in self.config.mcp_servers:
        #     if mcp_config.enabled:
        #         try:
        #             mcp_client = MCPClient(mcp_config)
        #             ...
        #         except Exception as e:
        #             logger.error(f"Failed to register MCP tool: {e}")
    
    def get_tools(self) -> List[Tool]:
        """
        Get all registered tools as LangChain Tool instances.
        
        Returns:
            List of LangChain tools
        """
        langchain_tools = []
        for tool_name, tool in self.tools.items():
            try:
                langchain_tool = tool.to_langchain_tool()
                langchain_tools.append(langchain_tool)
            except Exception as e:
                logger.error(f"Failed to convert {tool_name} to LangChain tool: {e}")
        
        return langchain_tools
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self.tools.keys())
    
    def get_tool(self, name: str) -> BaseTool:
        """
        Get a specific tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            BaseTool instance
            
        Raises:
            KeyError: If tool not found
        """
        return self.tools[name]
