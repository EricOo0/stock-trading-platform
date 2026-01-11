"""Personal finance agent entrypoint.

This module keeps the historical factory name `create_personal_finance_graph` for
API compatibility, but the implementation is now an orchestrator with a multi-turn
task loop (Master-Worker pattern) instead of a static LangGraph DAG.
"""

from backend.app.agents.personal_finance.orchestrator import PersonalFinanceOrchestrator


def create_personal_finance_graph() -> PersonalFinanceOrchestrator:
    """Factory used by API layer; returns an object exposing `astream(initial_state)`."""

    return PersonalFinanceOrchestrator()
