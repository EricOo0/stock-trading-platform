import logging
from typing import Dict, Any, Optional, List

from langchain.tools import BaseTool
from ddgs import DDGS  # Updated to use new ddgs package
from pydantic import BaseModel, Field, PrivateAttr

from .config import Config

from .config import Config
from utils.logging import logger

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to find information on the internet.")

class WebSearchSkill(BaseTool):
    """
    Web Search Skill
    Performs web searches to find real-time information, news, and events.
    """
    name: str = "web_search_tool"
    description: str = "Performs web searches to find real-time information, news, and events."
    args_schema: type[BaseModel] = WebSearchInput

    def __init__(self):
        super().__init__()
        logger.info("Web Search Skill initialized")

    def _run(self, query: str) -> Dict[str, Any]:
        """
        Execute the web search.

        Args:
            query: The search query.

        Returns:
            Dictionary containing the search results.
        """
        try:
            logger.info(f"Searching web for: {query}")
            
            results = []
            # Use DDGS directly as per recommended usage
            from ddgs import DDGS  # New package
            import time
            import traceback
            import os
            
            # Retry logic (up to 2 retries)
            max_retries = 2
            
            # Try different backends in order
            backends = ["lite", "html", "auto"]  # lite is usually more reliable
            
            for attempt in range(max_retries + 1):
                for backend in backends:
                    try:
                        # Get proxy from environment variable if set
                        proxy = os.getenv("DDGS_PROXY", None)
                        
                        # Initialize DDGS with optional proxy
                        ddgs = DDGS(proxy=proxy, timeout=20) if proxy else DDGS(timeout=20)
                        
                        # Use different backend to avoid blocks
                        logger.info(f"Attempting search with backend: {backend}")
                        ddgs_gen = ddgs.text(query, backend=backend, max_results=5)
                        
                        if ddgs_gen:
                            results = list(ddgs_gen)
                            if results:
                                logger.info(f"Found {len(results)} results for query: {query} using backend: {backend}")
                                break
                            else:
                                logger.warning(f"No results found for query: {query} with backend: {backend}")
                        else:
                            logger.warning(f"DDGS returned no results for query: {query} with backend: {backend}")
                    except Exception as e:
                        error_details = traceback.format_exc()
                        logger.error(f"DDGS search failed with backend {backend} (attempt {attempt + 1}/{max_retries + 1})")
                        logger.error(f"Error type: {type(e).__name__}")
                        logger.error(f"Error message: {str(e)}")
                        logger.error(f"Full traceback:\n{error_details}")
                        continue  # Try next backend
                
                # If we got results, break out of retry loop
                if results:
                    break
                    
                # If this wasn't the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"All backends failed. Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed for query: {query}")
                    results = []
            
            # Format results into a readable string for the LLM
            formatted_results = ""
            for i, res in enumerate(results):
                title = res.get('title', 'No Title')
                body = res.get('body', 'No Content')
                href = res.get('href', '')
                formatted_results += f"{i+1}. [{title}]({href})\n   {body}\n\n"
            
            if not formatted_results:
                formatted_results = "No results found. The search engine may be experiencing issues or the query may be too specific."
                logger.warning(f"Web search returned no results for: {query}")

            return {
                "status": "success",
                "query": query,
                "result": formatted_results,
                "raw_results": results
            }
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "message": f"Web search failed: {str(e)}"
            }

    async def _arun(self, query: str) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        return self._run(query)
