import logging
import json
import os
from typing import AsyncGenerator
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from backend.infrastructure.config.loader import config
from backend.app.registry import Tools
from backend.app.agents.macro.prompts import MACRO_ANALYSIS_INSTRUCTION

logger = logging.getLogger(__name__)

class MacroAgentService:
    def __init__(self):
        self.tools = Tools()
        
        # Initialize LLM (aligned with ReportAnalysisTool pattern)
        api_key = config.get_api_key("siliconflow") or config.get_api_key("openai") or os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Determine base URL and Model
        self.api_base = "https://api.siliconflow.cn/v1" if config.get_api_key("siliconflow") or os.getenv("SILICONFLOW_API_KEY") else "https://api.openai.com/v1"
        self.model = "deepseek-ai/DeepSeek-V3.1-Terminus" if "siliconflow" in self.api_base else "gpt-4o"
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.1, # Low temperature for consistent JSON output
            base_url=self.api_base,
            api_key=api_key or "dummy",
            streaming=True
        )

    async def analyze_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        Generates macro analysis and streams the output.
        """
        logger.info(f"Starting macro analysis stream for session {session_id}")
        
        # 1. Fetch Data
        try:
            logger.info("Fetching macro data...")
            # China Data
            cn_gdp = self.tools.get_macro_data("china gdp")
            cn_cpi = self.tools.get_macro_data("china cpi")
            cn_pmi = self.tools.get_macro_data("china pmi")
            cn_m2 = self.tools.get_macro_data("china m2")
            
            # US Data
            us_cpi = self.tools.get_macro_data("us cpi")
            us_rate = self.tools.get_macro_data("us fed funds")
            us_unemp = self.tools.get_macro_data("us unemployment")
            
            # Market
            us10y = self.tools.get_macro_data("us10y")
            dxy = self.tools.get_macro_data("dxy")
            vix = self.tools.get_macro_data("vix")
            
            macro_context = {
                "China": { "GDP": cn_gdp, "CPI": cn_cpi, "PMI": cn_pmi, "M2": cn_m2 },
                "US": { "CPI": us_cpi, "FedFundsRate": us_rate, "Unemployment": us_unemp },
                "Market": { "US10Y": us10y, "VIX": vix, "DXY": dxy }
            }
            context_json = json.dumps(macro_context, indent=2, default=str)
            logger.info("Macro data fetched successfully.")
            
        except Exception as e:
            logger.error(f"Data fetch error: {e}")
            context_json = "{}" # Proceed with empty or return error? Proceed for resilience.
        
        # 2. Construct Prompt
        prompt = f"""
{MACRO_ANALYSIS_INSTRUCTION}

### 当前宏观数据 (Current Data Context)
{context_json}
"""
        
        # 3. Stream Response
        try:
            messages = [
                SystemMessage(content="You are a professional macro-economic analyst."),
                HumanMessage(content=prompt)
            ]
            
            logger.info("Invoking LLM stream...")
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    # Wrap in the format expected by frontend
                    yield json.dumps({"type": "agent_response", "content": chunk.content}) + "\n"
                    
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

macro_agent_service = MacroAgentService()
