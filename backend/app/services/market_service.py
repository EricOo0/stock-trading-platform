import logging
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools

logger = logging.getLogger(__name__)

class MarketService:
    def __init__(self):
        self.tools = Tools()

    def get_stock_price(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """Get real-time stock price."""
        return self.tools.get_stock_price(symbol, market)

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get financial metrics (revenue, income, etc.)."""
        return self.tools.get_financial_metrics(symbol)
    
    def get_financial_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get summarized financial indicators."""
        return self.tools.get_financial_indicators(symbol)

    def get_historical_data(self, symbol: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """Get historical k-line data."""
        return self.tools.get_historical_data(symbol, period, interval)

    def get_technical_indicators(self, symbol: str, period: str = "60d") -> Dict[str, Any]:
        """Get calculated technical indicators (snapshot)."""
        return self.tools.get_technical_indicators(symbol, period)

    def get_technical_history(self, symbol: str, period: str = "1y") -> List[Dict[str, Any]]:
        """Get historical technical data (series)."""
        if hasattr(self.tools, 'get_technical_history'):
            return self.tools.get_technical_history(symbol, period)
        return []
    
    def get_macro_data(self, query: str) -> Dict[str, Any]:
        """Get macro economic data."""
        return self.tools.get_macro_data(query)

    def get_macro_history(self, indicator: str, period: str = "1y") -> Dict[str, Any]:
        """Get macro history data."""
        # Use tools.get_macro_history which was present in registry.py
        # Need to ensure proper delegation
        if hasattr(self.tools, 'get_macro_history'):
             return self.tools.get_macro_history(indicator, period)
        # Fallback if registry helper missing (though it was seen in view_file)
        return {"error": "Macro history tool not available"}

    def get_hot_stocks(self) -> List[Dict[str, Any]]:
        """Get hot stocks data."""
        hot_stocks = ['000001', '600036', 'AAPL', 'TSLA', '00700', '000002']
        results = []
        for symbol in hot_stocks:
            try:
                result = self.tools.get_stock_price(symbol)
                if result and "error" not in result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to fetch hot stock {symbol}: {e}")
                continue
        return results

    def get_fed_probability(self) -> Dict[str, Any]:
        """
        Calculate Fed Implied Probability based on ZQ=F futures.
        Ported from api_server.py.
        """
        import math
        from datetime import datetime
        import yfinance as yf

        # 1. Fetch Current Fed Target Upper Limit (DFEDTARU)
        fed_data = self.get_macro_history("DFEDTARU", "1y")
        
        current_target_upper = 5.50
        
        if fed_data and "data" in fed_data and len(fed_data["data"]) > 0:
            latest = fed_data["data"][-1]
            if latest.get("value") is not None:
                current_target_upper = float(latest["value"])
        
        current_target_mid = current_target_upper - 0.125
        
        # 2. Fetch ZQ=F
        ticker = yf.Ticker("ZQ=F")
        hist = ticker.history(period="5d")
        
        if hist.empty:
            raise Exception("Failed to fetch ZQ=F futures data")
            
        zq_price = hist["Close"].iloc[-1]
        implied_rate = 100 - zq_price
        
        # 3. Calculate Bin Distribution
        def get_bin_name(midpoint):
            low = int((midpoint - 0.125) * 100)
            high = int((midpoint + 0.125) * 100)
            return f"{low}-{high}"
        
        bin_step = 0.25
        shifted_rate = implied_rate - 0.125
        lower_bin_index = math.floor(shifted_rate / bin_step)
        
        lower_bin_mid = 0.125 + lower_bin_index * bin_step
        upper_bin_mid = lower_bin_mid + bin_step
        
        weight_upper = (implied_rate - lower_bin_mid) / bin_step
        weight_upper = max(0.0, min(1.0, weight_upper))
        weight_lower = 1.0 - weight_upper
        
        bins = [
            {
                "bin": get_bin_name(lower_bin_mid),
                "prob": round(weight_lower * 100, 1),
                "is_current": abs(lower_bin_mid - current_target_mid) < 0.01
            },
            {
                "bin": get_bin_name(upper_bin_mid),
                "prob": round(weight_upper * 100, 1),
                "is_current": abs(upper_bin_mid - current_target_mid) < 0.01
            }
        ]
        
        return {
            "status": "success",
            "current_target_rate": f"{current_target_upper-0.25:.2f}-{current_target_upper:.2f}",
            "implied_rate": round(implied_rate, 3),
            "data": bins,
            "timestamp": datetime.now().isoformat()
        }

    # ========================== Sector Analysis ==========================

    def get_sector_fund_flow_ranking(self, sort_by: str = "net_flow", limit: int = 10, sector_type: str = "industry") -> List[Dict[str, Any]]:
        """
        Get sector ranking based on fund flow.
        sort_by: "net_flow" (hot), "net_flow_asc" (cold), "rise_fall" (gainers)
        sector_type: "industry" (default) or "concept"
        """
        if sector_type == "concept":
            rankings = self.tools.akshare.get_concept_fund_flow_rank()
        else:
            rankings = self.tools.akshare.get_sector_fund_flow_rank()
            
        if not rankings:
            return []
            
        if sort_by == "net_flow":
            # Sort by net_flow desc (Hot)
            rankings.sort(key=lambda x: x.get("net_flow", 0), reverse=True)
        elif sort_by == "net_flow_asc":
             # Sort by net_flow asc (Cold)
             rankings.sort(key=lambda x: x.get("net_flow", 0), reverse=False)
        elif sort_by == "rise_fall":
            rankings.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
            
        return rankings[:limit]

    def get_hot_sectors(self, limit: int = 10, sector_type: str = "industry") -> List[Dict[str, Any]]:
        """Get sectors with highest net fund inflow."""
        return self.get_sector_fund_flow_ranking(sort_by="net_flow", limit=limit, sector_type=sector_type)

    def get_cold_sectors(self, limit: int = 10, sector_type: str = "industry") -> List[Dict[str, Any]]:
        """Get sectors with highest net fund outflow."""
        return self.get_sector_fund_flow_ranking(sort_by="net_flow_asc", limit=limit, sector_type=sector_type)

    def get_sector_details(self, sector_name: str, sort_by: str = "amount", limit: int = 5, sector_type: str = "industry") -> Dict[str, Any]:
        """
        Get details of a sector including top stocks.
        """
        if sector_type == "concept":
            components = self.tools.akshare.get_concept_components(sector_name)
        else:
            components = self.tools.akshare.get_sector_components(sector_name)
            
        if not components:
            return {"error": f"Sector {sector_name} not found or empty"}
            
        if sort_by == "amount":
            components.sort(key=lambda x: x.get("amount", 0), reverse=True)
        elif sort_by == "percent":
            components.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
            
        return {
            "sector_name": sector_name,
            "stocks": components[:limit]
        }

market_service = MarketService()

