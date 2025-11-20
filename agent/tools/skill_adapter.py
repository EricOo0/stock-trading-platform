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


class MarketDataInput(LangChainBaseModel):
    """Input for market data skill."""
    query: str = LangChainField(description="Stock symbol or company name to query")


class SkillAdapter(BaseTool):
    """
    Adapter to wrap Claude Skills as LangChain tools.
    
    This adapter loads the market_data_tool skill and exposes it as a tool
    that the ReAct agent can use.
    """
    
    def __init__(self, skill_path: str = "../skills/market_data_tool"):
        """
        Initialize the skill adapter.
        
        Args:
            skill_path: Path to the skill directory
        """
        self.skill_path = Path(skill_path)
        self._skill_module = None
        self._main_handle = None
        self._load_skill()
    
    def _load_skill(self) -> None:
        """Load the skill module."""
        try:
            # Add skill path to sys.path
            skill_parent = self.skill_path.parent.absolute()
            if str(skill_parent) not in sys.path:
                sys.path.insert(0, str(skill_parent))
            
            # Import the skill module
            skill_file = self.skill_path / "skill.py"
            if not skill_file.exists():
                raise SkillLoadError(f"Skill file not found: {skill_file}")
            
            spec = importlib.util.spec_from_file_location("market_data_tool.skill", skill_file)
            if spec is None or spec.loader is None:
                raise SkillLoadError(f"Failed to load skill spec from {skill_file}")
            
            self._skill_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._skill_module)
            
            # Get the main_handle function
            if not hasattr(self._skill_module, "main_handle"):
                raise SkillLoadError("Skill module does not have main_handle function")
            
            self._main_handle = self._skill_module.main_handle
            logger.info(f"Successfully loaded skill from {self.skill_path}")
            
        except Exception as e:
            logger.error(f"Failed to load skill: {e}")
            raise SkillLoadError(f"Failed to load skill: {e}")
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "market_data"
    
    @property
    def description(self) -> str:
        """Tool description."""
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
            args_schema=MarketDataInput
        )
