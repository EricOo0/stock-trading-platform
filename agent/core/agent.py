"""ReAct agent implementation using LangChain."""

from typing import Any, Dict, List, Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from core.config import Config
from core.prompts import REACT_SYSTEM_PROMPT
from core.memory import ConversationMemory
from tools.manager import ToolManager
from utils.exceptions import LLMError, AgentException


class StockAnalysisAgent:
    """
    LangChain ReAct agent for stock analysis.
    
    This agent uses the Reasoning + Acting (ReAct) paradigm to:
    1. Think about the user's question
    2. Decide which tool to use
    3. Observe the tool output
    4. Repeat until it has enough information
    5. Provide a final answer
    """
    
    def __init__(self, config: Config):
        """
        Initialize the stock analysis agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.llm = self._init_llm()
        self.tool_manager = ToolManager(config)
        self.tools = self.tool_manager.get_tools()
        self.agent_executor = self._create_agent_executor()
        logger.info("Stock Analysis Agent initialized successfully")
    
    def _init_llm(self) -> ChatOpenAI:
        """
        Initialize the LLM.
        
        Returns:
            ChatOpenAI instance
        """
        try:
            llm = ChatOpenAI(
                model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                openai_api_key=self.config.llm.api_key,
                openai_api_base=self.config.llm.api_base,
            )
            logger.info(f"LLM initialized: {self.config.llm.model}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMError(f"Failed to initialize LLM: {e}")
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        Create the ReAct agent executor.
        
        Returns:
            AgentExecutor instance
        """
        try:
            # Create prompt template
            prompt = PromptTemplate.from_template(REACT_SYSTEM_PROMPT)
            
            # Create ReAct agent
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=self.config.agent.verbose,
                max_iterations=self.config.agent.max_iterations,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )
            
            logger.info("ReAct agent executor created successfully")
            return agent_executor
            
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            raise AgentException(f"Failed to create agent executor: {e}")
    
    async def run(
        self,
        query: str,
        memory: Optional[ConversationMemory] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with a user query.
        
        Args:
            query: User query
            memory: Optional conversation memory
            
        Returns:
            Dict with response and intermediate steps
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Prepare chat history
            chat_history = ""
            if memory:
                chat_history = memory.get_chat_history()
            
            # Run agent
            result = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": chat_history
            })
            
            # Extract response
            response = {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
            # Update memory
            if memory:
                memory.add_message("user", query)
                memory.add_message("assistant", response["output"])
            
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "output": f"抱歉，处理您的请求时出现了错误：{str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e)
            }
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return self.tool_manager.get_tool_names()
