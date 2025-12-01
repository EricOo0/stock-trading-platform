import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from fredapi import Fred
from ..utils import get_retry_decorator, cached_macro_data

logger = logging.getLogger(__name__)

class FredService:
    """Service for interacting with FRED API."""
    
    # Indicator mapping to FRED Series IDs
    INDICATORS = {
        'CPI': 'CPIAUCSL',  # Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
        'CORE_CPI': 'CPILFESL', # Consumer Price Index for All Urban Consumers: All Items Less Food and Energy
        'GDP': 'GDP',       # Gross Domestic Product
        'NONFARM_PAYROLLS': 'PAYEMS', # All Employees, Total Nonfarm
        'UNEMPLOYMENT_RATE': 'UNRATE', # Unemployment Rate
        'FED_FUNDS_RATE': 'FEDFUNDS', # Federal Funds Effective Rate
        'M2': 'M2SL',       # M2
        'US10Y': 'DGS10',   # Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity
        'VIX': 'VIXCLS',    # CBOE Volatility Index
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                self.client = Fred(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize FRED client: {e}")

    @get_retry_decorator(max_attempts=3)
    @cached_macro_data
    def get_latest_data(self, indicator: str) -> Dict[str, Any]:
        """Get the latest data for a specific indicator."""
        if not self.client:
            return {"error": "FRED API key not configured"}

        series_id = self.INDICATORS.get(indicator.upper())
        if not series_id:
            return {"error": f"Unknown indicator: {indicator}"}

        try:
            # Get latest observation
            series = self.client.get_series(series_id, limit=1, sort_order='desc')
            if series.empty:
                return {"error": "No data found"}

            latest_date = series.index[0]
            latest_value = series.iloc[0]
            
            # Get info for units/frequency
            info = self.client.get_series_info(series_id)
            
            return {
                "indicator": indicator,
                "series_id": series_id,
                "value": float(latest_value),
                "date": latest_date.strftime('%Y-%m-%d'),
                "units": info.get('units', ''),
                "frequency": info.get('frequency', ''),
                "title": info.get('title', '')
            }
        except Exception as e:
            logger.error(f"Error fetching FRED data for {indicator}: {e}")
            return {"error": str(e)}

    @get_retry_decorator(max_attempts=3)
    @cached_macro_data
    def get_historical_data(self, indicator: str, limit: int = 12) -> Dict[str, Any]:
        """Get historical data for a specific indicator."""
        if not self.client:
            return {"error": "FRED API key not configured"}

        series_id = self.INDICATORS.get(indicator.upper())
        if not series_id:
            return {"error": f"Unknown indicator: {indicator}"}

        try:
            series = self.client.get_series(series_id, limit=limit, sort_order='desc')
            if series.empty:
                return {"error": "No data found"}

            data = []
            for date, value in series.items():
                data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "value": float(value)
                })
            
            info = self.client.get_series_info(series_id)

            return {
                "indicator": indicator,
                "series_id": series_id,
                "data": data,
                "units": info.get('units', ''),
                "frequency": info.get('frequency', ''),
                "title": info.get('title', '')
            }
        except Exception as e:
            logger.error(f"Error fetching historical FRED data for {indicator}: {e}")
            return {"error": str(e)}
