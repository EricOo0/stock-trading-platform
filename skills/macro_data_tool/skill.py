import logging
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from agent.core.config import get_config
from .services.fred_service import FredService
from .services.yahoo_service import YahooMacroService
from .services.akshare_service import AkShareService
from .prompts import MACRO_DATA_TOOL_DESCRIPTION

logger = logging.getLogger(__name__)

class MacroDataInput(BaseModel):
    query: str = Field(description="The query about macroeconomic data or market indicators")

class MacroDataSkill(BaseTool):
    name: str = "macro_data_tool"
    description: str = MACRO_DATA_TOOL_DESCRIPTION
    args_schema: type[BaseModel] = MacroDataInput
    
    _fred_service: FredService = PrivateAttr()
    _yahoo_service: YahooMacroService = PrivateAttr()
    _akshare_service: AkShareService = PrivateAttr()
    
    def __init__(self):
        super().__init__()
        config = get_config()
        self._fred_service = FredService(api_key=config.skills.fred_api_key)
        self._yahoo_service = YahooMacroService()
        self._akshare_service = AkShareService()

    def _run(self, query: str) -> Dict[str, Any]:
        """Run the tool."""
        query = query.lower()
        results = {}
        
        try:
            # 1. Determine intent and route to appropriate service
            
            # US Data (FRED)
            if "cpi" in query and "china" not in query:
                results["us_cpi"] = self._fred_service.get_latest_data("CPI")
            if "gdp" in query and "china" not in query:
                results["us_gdp"] = self._fred_service.get_latest_data("GDP")
            if "non-farm" in query or "payroll" in query or "employment" in query:
                results["nonfarm"] = self._fred_service.get_latest_data("NONFARM_PAYROLLS")
                results["unemployment"] = self._fred_service.get_latest_data("UNEMPLOYMENT_RATE")
            if "fed funds" in query or "interest rate" in query:
                results["fed_rate"] = self._fred_service.get_latest_data("FED_FUNDS_RATE")
            
            # Market Indicators (Yahoo)
            if "vix" in query or "fear" in query or "volatility" in query:
                results["vix"] = self._yahoo_service.get_market_indicators().get("VIX")
            if "treasury" in query or "yield" in query or "bond" in query:
                results["us10y"] = self._yahoo_service.get_market_indicators().get("US10Y")
            if "dollar" in query or "dxy" in query:
                results["dxy"] = self._yahoo_service.get_market_indicators().get("DXY")
            if "probability" in query or "cut" in query or "hike" in query:
                results["fed_probs"] = self._yahoo_service.analyze_fed_rate_probability()
                
            # China Data (AkShare)
            if "china" in query or "cn" in query:
                if "gdp" in query:
                    results["cn_gdp"] = self._akshare_service.get_china_macro_data("GDP")
                if "cpi" in query:
                    results["cn_cpi"] = self._akshare_service.get_china_macro_data("CPI")
                if "pmi" in query:
                    results["cn_pmi"] = self._akshare_service.get_china_macro_data("PMI")

            # If no specific keywords matched, try to get a general market overview
            if not results:
                results["market_overview"] = self._yahoo_service.get_market_indicators()

            return {
                "status": "success",
                "data": results,
                "query": query
            }

        except Exception as e:
            logger.error(f"Error in MacroDataSkill: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_historical_data(self, indicator: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical data for a specific indicator."""
        try:
            # Handle China indicators with prefix
            if indicator.upper().startswith('CN_'):
                clean_indicator = indicator[3:] # Remove CN_
                return self._akshare_service.get_historical_data(clean_indicator)

            # Determine source based on indicator name
            # FRED indicators
            if indicator.upper() in self._fred_service.INDICATORS:
                return self._fred_service.get_historical_data(indicator)
            
            # Yahoo indicators
            if indicator.upper() in self._yahoo_service.SYMBOLS:
                return self._yahoo_service.get_historical_data(indicator, period)
            
            # AkShare indicators (fallback if no prefix but known)
            if indicator.upper() in ['GDP', 'CPI', 'PMI']: # China indicators
                return self._akshare_service.get_historical_data(indicator)
                
            return {"error": f"Unknown indicator: {indicator}"}
            
        except Exception as e:
            logger.error(f"Error getting historical data for {indicator}: {e}")
            return {"error": str(e)}

    async def _arun(self, query: str) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        # For now, just call the sync version
        return self._run(query)
