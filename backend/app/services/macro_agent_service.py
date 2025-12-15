import logging
import json
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from backend.app.agents.macro.agent import create_macro_agent
from backend.app.agents.macro.callbacks import MacroCallbackHandler
from backend.app.registry import Tools

logger = logging.getLogger(__name__)

class MacroAgentService:
    def __init__(self):
        self.tools = Tools()
        self.session_service = InMemorySessionService()

    async def analyze_stream(self, session_id: str):
        """
        Generates macro analysis and streams the output.
        """
        callback_handler = MacroCallbackHandler()
        agent = create_macro_agent(callback_handler=callback_handler)
        
        # 1. Fetch Data
        try:
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
        except Exception as e:
             logger.error(f"Data fetch error: {e}")
             context_json = "{}" # Proceed with empty or return error? Proceed for resilience.
        
        # Prepare User and Session
        user_id = "macro_user"
        # Ensure session exists
        try:
             await self.session_service.create_session(
                app_name="macro_app",
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            pass # Session might already exist

        runner = Runner(agent=agent, app_name="macro_app", session_service=self.session_service)
        
        try:
            from google.genai import types
            input_content = types.Content(role="user", parts=[types.Part(text=f"Current Macro Data Context:\n{context_json}")])

            events = runner.run_async(user_id=user_id, session_id=session_id, new_message=input_content)
            
            async for event in events:
                # logger.info(f"raw event: {event}")
                try:
                    if hasattr(event, 'content') and event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                logger.info(f"Yielding chunk: {part.text[:50]}...")
                                yield json.dumps({"type": "agent_response", "content": part.text}) + "\n"
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    pass
                     
        except Exception as e:
            logger.error(f"Runner error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

macro_agent_service = MacroAgentService()
