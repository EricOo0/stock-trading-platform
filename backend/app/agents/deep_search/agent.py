from google.adk.agents import Agent
from backend.infrastructure.config.loader import config
from .tools import search_web, visit_page, scroll_page
from .prompts import INSTRUCTION

# Load model dynamically
model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
if not model_name.startswith("openai/"):
    model_name = f"openai/{model_name}"

deep_search_agent = Agent(
    name="deep_search_agent",
    model=model_name,
    instruction=INSTRUCTION,
    tools=[search_web, visit_page, scroll_page],
    description="Deep Search Agent for market sentiment research."
)
