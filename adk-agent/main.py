"""
Fintech Multi-Agent System Entry Point

⚠️ CRITICAL: Environment configuration MUST happen BEFORE importing agents!
This ensures that Tools() receives the correct API keys during initialization.
"""

# Step 1: Configure environment FIRST (before any agent imports)
from core.llm import configure_environment
configure_environment()

# Step 2: Now it's safe to import (this triggers agent initialization)
from api.receptionist import start

if __name__ == "__main__":
    print("Starting Fintech Multi-Agent Receptionist...")
    print("Environment configured ✓")
    start()

