
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FredTool:
    """
    Tool for fetching US macro economic data from FRED (Federal Reserve Economic Data).
    """
    BASE_URL = "https://api.stlouisfed.org/fred"

    # Common indicator mapping to FRED Series IDs
    INDICATORS = {
        "GDP": "GDP",
        "CPI": "CPIAUCSL", # Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
        "UNEMPLOYMENT": "UNRATE", # Unemployment Rate
        "NONFARM_PAYROLLS": "PAYEMS", # All Employees, Total Nonfarm
        "FED_FUNDS": "FEDFUNDS", # Federal Funds Effective Rate
        "M2": "M2SL", # M2 Money Stock
        "US10Y": "DGS10", # Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity
        "VIX": "VIXCLS", # CBOE Volatility Index
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_data(self, series_id: str, observation_start: Optional[str] = None, observation_end: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch observations for a specific series.
        """
        if not self.api_key:
            return {"error": "FRED API key is not configured"}

        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json"
        }

        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"DEBUG: FRED URL: {response.url}") # Debugging
            response.raise_for_status()
            data = response.json()
            
            observations = data.get("observations", [])
            results = []
            for obs in observations:
                val = obs.get("value")
                # Handle "." which represents missing data in FRED
                if val == ".":
                    val = None
                else:
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        val = None
                
                results.append({
                    "date": obs.get("date"),
                    "value": val
                })
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"FRED API Request Error: {e}")
            return {"error": f"FRED API Error: {str(e)}"}
        except Exception as e:
            logger.error(f"FRED Data Parse Error: {e}")
            return {"error": f"FRED Data Error: {str(e)}"}

    def get_macro_history(self, indicator: str, period: str = "1y") -> Dict[str, Any]:
        """
        Get historical data for a named indicator (e.g., 'CPI', 'GDP').
        Period format: '1y', '5y', 'max'.
        """
        series_id = self.INDICATORS.get(indicator.upper())
        if not series_id:
            # Fallback: try using the indicator string directly as ID
            series_id = indicator.upper()

        # Calculate start date based on period
        start_date = None
        now = datetime.now()
        if period == "1y":
            start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
        elif period == "3y":
             start_date = (now - timedelta(days=365*3)).strftime("%Y-%m-%d")
        elif period == "5y":
            start_date = (now - timedelta(days=365*5)).strftime("%Y-%m-%d")
        elif period == "10y":
            start_date = (now - timedelta(days=365*10)).strftime("%Y-%m-%d")
        # 'max' implies no start_date param

        data = self.get_data(series_id, observation_start=start_date)
        
        if isinstance(data, dict) and "error" in data:
             return data

        return {
            "status": "success",
            "indicator": indicator,
            "data_source": "FRED",
            "series_id": series_id,
            "data": data
        }
