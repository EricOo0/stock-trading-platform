import logging

from langchain_openai import ChatOpenAI

from backend.infrastructure.config.loader import config

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Configures and returns the LLM instance for personal_finance agents."""

    openai_key = config.get_api_key("openai")
    silicon_key = config.get_api_key("siliconflow")
    base_url = config.get("api_url")
    model_name = config.get("model", "gpt-4o")

    api_key = openai_key

    # Placeholder guard
    if openai_key and openai_key.startswith("sk-") and "xxxx" in openai_key:
        api_key = None

    # Prefer SiliconFlow if base_url indicates or OpenAI key invalid
    if "siliconflow" in (base_url or ""):
        api_key = silicon_key or api_key
    elif not api_key:
        api_key = silicon_key

    if not api_key and silicon_key:
        api_key = silicon_key

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )
