import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_system.config import settings

print(f"CWD: {os.getcwd()}")
print(f"Settings LLM Model: {settings.LLM_MODEL}")
print(f"Settings API Base: {settings.OPENAI_API_BASE}")
