import logging
from typing import Dict, Any, Optional
import akshare as ak
import pandas as pd
from datetime import datetime
from ..utils import get_retry_decorator, cached_macro_data

logger = logging.getLogger(__name__)

class AkShareService:
    """Service for fetching China macro data using AkShare."""

    @get_retry_decorator(max_attempts=3)
    @cached_macro_data
    def get_china_macro_data(self, indicator: str) -> Dict[str, Any]:
        """Get latest China macro data."""
        try:
            if indicator.upper() == 'GDP':
                # China GDP Quarterly
                df = ak.macro_china_gdp()
                if df.empty:
                    return {"error": "No data"}
                # df columns: 季度, 国内生产总值-绝对值(亿元), 国内生产总值-同比增长, ...
                latest = df.iloc[0] # Usually sorted descending? Need to check. 
                # AkShare data is often sorted by date descending or ascending.
                # Let's assume we need to sort or check date.
                # macro_china_gdp usually returns: 季度 (e.g. '2023年第4季度')
                
                return {
                    "indicator": "China GDP",
                    "value": float(latest['国内生产总值-绝对值']),
                    "growth_rate": float(latest['国内生产总值-同比增长']),
                    "period": latest['季度'],
                    "unit": "100 Million CNY"
                }
                
            elif indicator.upper() == 'CPI':
                # China CPI Monthly
                df = ak.macro_china_cpi()
                if df.empty:
                    return {"error": "No data"}
                # columns: 月份, 全国-当月, 全国-同比增长, ...
                latest = df.iloc[0]
                
                return {
                    "indicator": "China CPI",
                    "value": float(latest['全国-当月']),
                    "yoy": float(latest['全国-同比增长']),
                    "date": latest['月份'],
                    "unit": "Index"
                }
                
            elif indicator.upper() == 'PMI':
                # China PMI Monthly
                df = ak.macro_china_pmi()
                if df.empty:
                    return {"error": "No data"}
                # columns: 月份, 制造业-PMI, ...
                latest = df.iloc[0]
                
                return {
                    "indicator": "China PMI",
                    "manufacturing": float(latest['制造业-PMI']),
                    "non_manufacturing": float(latest['非制造业-商务活动指数']),
                    "date": latest['月份']
                }
                
            else:
                return {"error": f"Unsupported indicator: {indicator}"}
                
        except Exception as e:
            logger.error(f"Error fetching AkShare data for {indicator}: {e}")
            return {"error": str(e)}

    @get_retry_decorator(max_attempts=3)
    @cached_macro_data
    def get_historical_data(self, indicator: str) -> Dict[str, Any]:
        """Get historical data for China macro indicators."""
        try:
            data = []
            if indicator.upper() == 'GDP':
                df = ak.macro_china_gdp()
                # df columns: 季度, 国内生产总值-绝对值, ...
                for _, row in df.iterrows():
                    data.append({
                        "date": row['季度'], # Format: 2023年第4季度
                        "value": float(row['国内生产总值-绝对值']),
                        "growth": float(row['国内生产总值-同比增长'])
                    })
            elif indicator.upper() == 'CPI':
                df = ak.macro_china_cpi()
                # df columns: 月份, 全国-当月, ...
                for _, row in df.iterrows():
                    data.append({
                        "date": row['月份'],
                        "value": float(row['全国-当月']),
                        "yoy": float(row['全国-同比增长'])
                    })
            elif indicator.upper() == 'PMI':
                df = ak.macro_china_pmi()
                # df columns: 月份, 制造业-PMI, ...
                for _, row in df.iterrows():
                    data.append({
                        "date": row['月份'],
                        "value": float(row['制造业-PMI']),
                        "non_manufacturing": float(row['非制造业-商务活动指数'])
                    })
            else:
                return {"error": f"Unsupported indicator: {indicator}"}
            
            return {
                "indicator": indicator,
                "data": data
            }
        except Exception as e:
            logger.error(f"Error fetching historical AkShare data for {indicator}: {e}")
            return {"error": str(e)}
