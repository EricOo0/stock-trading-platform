from abc import ABC, abstractmethod
from typing import List, Dict, Any

class WebSearchProvider(ABC):
    """Abstract base class for web search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a web search.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.

        Returns:
            A list of dictionaries, where each dictionary represents a search result
            and contains at least 'title', 'href', and 'body' keys.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""
        pass
