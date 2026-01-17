from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from LLM output."""
    text = (text or "").strip()
    
    # Try regex for markdown code block first
    # Match ```json ... ``` or just ``` ... ```
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            pass  # Fallback if regex match isn't valid JSON

    # Fallback: Find first '{' and last '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx : end_idx + 1]
        try:
            return json.loads(json_str)
        except Exception:
            pass
            
    # Legacy fallback for simple strings
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except Exception:
            pass

    return None


def extract_response_content(resp: Any) -> str:
    """Helper to extract string content from various agent response formats."""
    # Case 1: AIMessage or object with content attribute
    if hasattr(resp, "content"):
        return str(resp.content)
    
    # Case 2: Dict response (AgentExecutor or Chain)
    if isinstance(resp, dict):
        # Prefer 'output' key (AgentExecutor default)
        if "output" in resp:
            return str(resp["output"])
        
        # Fallback: check for 'messages' key (LangGraph state)
        if "messages" in resp and isinstance(resp["messages"], list) and resp["messages"]:
            last_msg = resp["messages"][-1]
            if hasattr(last_msg, "content"):
                return str(last_msg.content)
    
    # Case 3: Fallback string conversion
    return str(resp)


def summarize_portfolio(
    portfolio: Dict[str, Any], max_assets: int = 50
) -> Dict[str, Any]:
    assets = portfolio.get("assets") or []
    if not isinstance(assets, list):
        assets = []
    
    # Debug log for portfolio data issues
    cash = portfolio.get("cash_balance", 0.0)
    # logger.info(f"[Utils] Portfolio Summary Input - Cash: {cash}, Asset Count: {len(assets)}")
    
    total_market_value = 0.0
    trimmed = []
    
    # Process assets first to calculate missing total values
    for a in assets:
        if not isinstance(a, dict):
            continue
            
        qty = float(a.get("quantity") or 0)
        curr_price = float(a.get("current_price") or 0)
        
        # Calculate or get total_value
        raw_val = a.get("total_value")
        if raw_val is not None:
             val = float(raw_val)
        else:
             val = qty * curr_price
             
        total_market_value += val
        
        # Add to trimmed list if within limit
        if len(trimmed) < max_assets:
            trimmed.append(
                {
                    "symbol": a.get("symbol"),
                    "name": a.get("name"),
                    "type": a.get("type"),
                    "quantity": qty,
                    "cost_basis": a.get("cost_basis"),
                    "current_price": curr_price,
                    "total_value": val,
                }
            )
            
    if total_market_value == 0 and len(assets) > 0:
         logger.warning("[Utils] Warning: Assets exist but total value is 0. Check price updates.")
    
    cash_balance = float(portfolio.get("cash_balance") or 0.0)
    total_equity = total_market_value + cash_balance
    
    return {
        "assets": trimmed, 
        "cash_balance": cash_balance,
        "total_market_value": total_market_value,
        "total_equity": total_equity
    }


def extract_top_symbols(portfolio: Dict[str, Any], limit: int = 50) -> List[str]:
    assets = portfolio.get("assets") or []
    symbols: List[str] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        sym = a.get("symbol")
        if sym:
            # Clean symbol format (remove sh/sz prefix if strictly needed, 
            # though orchestrator does this. We'll keep it consistent)
            symbols.append(str(sym).replace("sh", "").replace("sz", ""))
    return symbols[:limit]
