import logging
from typing import Dict, Any, Optional, List

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from .config import Config
from utils.logging import logger
from .providers.base import WebSearchProvider
from .providers.tavily_provider import TavilyProvider
from .providers.serpapi_provider import SerpApiProvider
from .providers.ddg_provider import DuckDuckGoProvider

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to find information on the internet.")

class WebSearchSkill(BaseTool):
    """
    Web Search Skill
    Performs web searches using multiple providers (Tavily, SerpApi, DuckDuckGo) with fallback logic.
    """
    name: str = "web_search_tool"
    description: str = "Performs web searches to find real-time information, news, and events."
    args_schema: type[BaseModel] = WebSearchInput
    
    _providers: List[WebSearchProvider] = []
    _tavily_key: Optional[str] = PrivateAttr(default=None)
    _serpapi_key: Optional[str] = PrivateAttr(default=None)
    _search_kwargs: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, tavily_api_key: Optional[str] = None, serpapi_api_key: Optional[str] = None, search_kwargs: Optional[Dict[str, Any]] = None):
        super().__init__()
        self._tavily_key = tavily_api_key
        self._serpapi_key = serpapi_api_key
        self._search_kwargs = search_kwargs or {}
        self._initialize_providers()
        logger.info("Web Search Skill initialized with providers: " + ", ".join([p.name for p in self._providers]))

    def _initialize_providers(self):
        """Initialize search providers based on available configuration."""
        self._providers = []
        
        # 1. Tavily (Preferred)
        # Prioritize passed key, then Config (env var)
        tavily_key = self._tavily_key or Config.TAVILY_API_KEY
        if tavily_key:
            try:
                self._providers.append(TavilyProvider(tavily_key))
            except Exception as e:
                logger.error(f"Failed to initialize Tavily provider: {e}")
        
        # 2. SerpApi (Fallback 1)
        serpapi_key = self._serpapi_key or Config.SERPAPI_API_KEY
        if serpapi_key:
            try:
                self._providers.append(SerpApiProvider(serpapi_key))
            except Exception as e:
                logger.error(f"Failed to initialize SerpApi provider: {e}")
        
        # 3. DuckDuckGo (Fallback 2 - Always available)
        try:
            self._providers.append(DuckDuckGoProvider())
        except Exception as e:
            logger.error(f"Failed to initialize DuckDuckGo provider: {e}")

    def _run(self, query: str) -> Dict[str, Any]:
        """
        Execute the web search using available providers in order.
        """
        logger.info(f"Searching web for: {query}")
        
        errors = []
        
        for provider in self._providers:
            try:
                logger.info(f"Attempting search with provider: {provider.name}")
                results = provider.search(query, **self._search_kwargs)
                
                if results:
                    logger.info(f"Found {len(results)} results using {provider.name}")
                    formatted_results = self._format_results(results)
                    return {
                        "status": "success",
                        "query": query,
                        "result": formatted_results,
                        "raw_results": results,
                        "provider": provider.name
                    }
                else:
                    logger.warning(f"Provider {provider.name} returned no results.")
            except Exception as e:
                error_msg = f"{provider.name} failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # If all providers failed
        error_summary = "; ".join(errors)
        logger.error(f"All providers failed for query '{query}'. Errors: {error_summary}")
        return {
            "status": "error",
            "query": query,
            "message": f"All search providers failed. Details: {error_summary}"
        }

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format results into a readable string for the LLM."""
        formatted_results = ""
        for i, res in enumerate(results):
            title = res.get('title', 'No Title')
            body = res.get('body', 'No Content')
            href = res.get('href', '')
            formatted_results += f"{i+1}. [{title}]({href})\n   {body}\n\n"
        
        if not formatted_results:
            return "No results found."
            
        return formatted_results

    async def _arun(self, query: str) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        return self._run(query)

