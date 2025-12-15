import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TechnicalAnalysisCallbackHandler:
    """
    Callback handler specifically for Technical Analysis Agent.
    """

    def __init__(self):
        # We don't really use this member anymore since we stream from runner,
        # but kept for compatibility or debugging.
        self.latest_response: Optional[Dict[str, Any]] = None

    def on_model_start(self, *args, **kwargs):
        """
        Triggered before the LLM is called.
        Logs the prompt for debugging.
        """
        try:
            llm_request = kwargs.get('llm_request')
            if not llm_request and len(args) >= 2:
                llm_request = args[1] # fallback

            # Debug Log - mirroring news_sentiment style
            if llm_request:
                # Use vars() if available as seen in news_sentiment logs
                debug_data = vars(llm_request) if hasattr(llm_request, '__dict__') else str(llm_request)
                
                # Try to format nicely
                try:
                    # vars() might contain objects that aren't json serializable default
                    prompt_str = str(debug_data) 
                    logger.info(f"[Technical Agent Debug] LLM Request Prompt:\n{prompt_str}")
                except Exception:
                     logger.info(f"[Technical Agent Debug] LLM Request Prompt: {debug_data}")
            else:
                 logger.info(f"[Technical Agent Debug] LLM Request: None found in args/kwargs")

        except Exception as e:
            logger.warning(f"[Technical Agent Debug] Error in on_model_start: {e}")

    def on_model_end(self, *args, **kwargs):
        """
        Triggered when LLM output is received.
        """
        try:
            llm_response = kwargs.get('llm_response')
            if not llm_response and len(args) >= 2:
                llm_response = args[1]

            content_text = ""
            
            # ADK Object Attribute Access
            if llm_response and hasattr(llm_response, 'content'):
                # llm_response.content is likely a Content object
                content_obj = llm_response.content
                if hasattr(content_obj, 'parts') and content_obj.parts:
                    for part in content_obj.parts:
                        if hasattr(part, 'text') and part.text:
                            content_text += part.text
            
            logger.info(f"[Technical Agent Debug] LLM Response Length: {len(content_text)}")
            logger.info(f"[Technical Agent Debug] LLM Response: {content_text}")

            # Store simple dict for whatever legacy need
            self.latest_response = {"content": content_text}

        except Exception as e:
            logger.error(f"[Technical Agent Debug] Error in on_model_end: {e}")
