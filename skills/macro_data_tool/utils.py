import logging
import requests
import random
from typing import Optional, Callable, Any
from functools import wraps
from cachetools import TTLCache, cached
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# 1. Session Management with User-Agent Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

def get_session() -> requests.Session:
    """Create a requests session with User-Agent rotation."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    return session

# 2. Retry Decorator
def get_retry_decorator(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Get a configured retry decorator.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying {retry_state.fn.__name__} due to {retry_state.outcome.exception()} "
            f"(Attempt {retry_state.attempt_number}/{max_attempts})"
        )
    )

# 3. Caching
# Cache for macro data (long TTL: 24 hours)
macro_cache = TTLCache(maxsize=100, ttl=86400)

def cached_macro_data(func):
    """Decorator to cache macro data results for 24 hours."""
    return cached(cache=macro_cache)(func)

# Cache for market indicators (short TTL: 5 minutes)
market_cache = TTLCache(maxsize=100, ttl=300)

def cached_market_data(func):
    """Decorator to cache market data results for 5 minutes."""
    return cached(cache=market_cache)(func)
