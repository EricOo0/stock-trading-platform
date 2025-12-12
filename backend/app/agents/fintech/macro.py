from backend.infrastructure.adk.core.agent_factory import create_agent
from backend.infrastructure.adk.core.tools import get_macro_data

macro_agent = create_agent(
    name="MacroDataInvestigator",
    description="Agent for retrieving macro-economic data.",
    instruction="""
    You are a Macro Data Investigator.
    Your goal is to find macro-economic indicators like GDP, CPI, Interest Rates, VIX, etc.
    
    Use `get_macro_data` with queries like "China GDP", "US CPI", "Fed Funds Rate".
    If the user asks about the general economy, check key indicators.
    """,
    tools=[get_macro_data]
)

