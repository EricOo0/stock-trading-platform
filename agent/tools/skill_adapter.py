"""Skill adapter to integrate Claude Skills into LangChain."""

import sys
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger

from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField

from tools.base import BaseTool, ToolOutput
from utils.exceptions import SkillLoadError


class SkillInput(LangChainBaseModel):
    """Input for skill tools."""
    query: str = LangChainField(description="Natural language query or input for the skill")


class SkillAdapter(BaseTool):
    """
    Adapter to wrap Claude Skills as LangChain tools.
    
    This adapter loads a Claude Skill and exposes it as a tool
    that the ReAct agent can use.
    """
    
    def __init__(self, skill_path: str = "../skills/market_data_tool", name: str = "market_data", description: str = None):
        """
        Initialize the skill adapter.
        
        Args:
            skill_path: Path to the skill directory
            name: Tool name
            description: Tool description
        """
        self.skill_path = Path(skill_path)
        self._name = name
        self._description = description
        self._skill_module = None
        self._main_handle = None
        self._load_skill()
    
    def _load_skill(self) -> None:
        """Load the skill module."""
        try:
            # Add the skills parent directory to sys.path
            # This allows importing skills as packages (e.g., import market_data_tool)
            skill_parent = self.skill_path.parent.absolute()
            if str(skill_parent) not in sys.path:
                sys.path.insert(0, str(skill_parent))
                logger.debug(f"Added {skill_parent} to sys.path")
            
            # Get the skill module name (e.g., 'market_data_tool', 'sentiment_analysis_tool')
            skill_module_name = self.skill_path.name
            
            # Dynamically import the skill module
            # This will execute __init__.py if it exists, and allow relative imports to work
            try:
                # Try to import the skill module
                skill_module = importlib.import_module(skill_module_name)
                logger.debug(f"Successfully imported package: {skill_module_name}")
                
                # Now import the skill submodule
                skill_main_module = importlib.import_module(f"{skill_module_name}.skill")
                
                # Get the main_handle function
                if not hasattr(skill_main_module, "main_handle"):
                    raise SkillLoadError(f"Skill module {skill_module_name}.skill does not have main_handle function")
                
                self._skill_module = skill_main_module
                self._main_handle = skill_main_module.main_handle
                logger.info(f"Successfully loaded skill: {skill_module_name}")
                
            except ModuleNotFoundError as e:
                logger.error(f"Failed to import skill module {skill_module_name}: {e}")
                raise SkillLoadError(f"Failed to import skill module {skill_module_name}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to load skill from {self.skill_path}: {e}", exc_info=True)
            raise SkillLoadError(f"Failed to load skill: {e}")
    
    @property
    def name(self) -> str:
        """Tool name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Tool description."""
        if self._description:
            return self._description
            
        return (
            "Get real-time stock market data for A-shares, US stocks, and HK stocks. "
            "Input should be a stock symbol (e.g., '000001', 'AAPL', '00700') or company name. "
            "Returns current price, change percentage, volume, and other market data."
        )
    
    async def execute(self, query: str) -> ToolOutput:
        """
        Execute the skill.
        
        Args:
            query: Stock symbol or company name
            
        Returns:
            ToolOutput with market data or error
        """
        try:
            result = self._main_handle(query)
            
            # Check if result indicates success
            if result.get("status") == "success":
                return ToolOutput(
                    success=True,
                    result=result
                )
            else:
                return ToolOutput(
                    success=False,
                    result=result,
                    error=result.get("message", "Unknown error occurred")
                )
        
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return ToolOutput(
                success=False,
                result=None,
                error=str(e)
            )
    
    def _run_sync(self, query: str) -> str:
        """
        Synchronous wrapper for LangChain.
        
        Args:
            query: Stock symbol or company name
            
        Returns:
            JSON string containing market data or error
        """
        import asyncio
        import json
        
        # Run async execute in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            output = loop.run_until_complete(self.execute(query))
            # Use default=str to handle datetime and other non-serializable objects
            return json.dumps(output.model_dump(), ensure_ascii=False, indent=2, default=str)
        finally:
            loop.close()
    
    def to_langchain_tool(self) -> Tool:
        """
        Convert to LangChain Tool.
        
        Returns:
            LangChain Tool instance
        """
        return Tool(
            name=self.name,
            description=self.description,
            func=self._run_sync,
            args_schema=SkillInput
        )
