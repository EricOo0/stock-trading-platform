import logging
from typing import Dict, Any, List
import yfinance as yf
from datetime import datetime
from ..utils import get_session, get_retry_decorator, cached_market_data

logger = logging.getLogger(__name__)

class YahooMacroService:
    """Service for fetching market indicators from Yahoo Finance."""

    SYMBOLS = {
        'VIX': '^VIX',          # CBOE Volatility Index
        'US10Y': '^TNX',        # Treasury Yield 10 Years
        'DXY': 'DX-Y.NYB',      # US Dollar Index
        'FED_FUNDS_FUTURES': 'ZQ=F' # Fed Funds Futures
    }

    def __init__(self):
        self.session = get_session()

    @get_retry_decorator(max_attempts=3)
    @cached_market_data
    def get_market_indicators(self) -> Dict[str, Any]:
        """Get current values for key market indicators."""
        results = {}
        
        for name, symbol in self.SYMBOLS.items():
            try:
                # Use custom session for yfinance
                ticker = yf.Ticker(symbol, session=self.session)
                # Get fast info or history
                # fast_info is faster but sometimes incomplete
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    results[name] = {
                        "symbol": symbol,
                        "price": float(latest['Close']),
                        "change": float(latest['Close'] - latest['Open']), # Approx change
                        "date": latest.name.strftime('%Y-%m-%d'),
                        "name": name
                    }
                else:
                    results[name] = {"error": "No data"}
                    
            except Exception as e:
                logger.error(f"Error fetching {name} ({symbol}): {e}")
                results[name] = {"error": str(e)}
                
        return results

    @get_retry_decorator(max_attempts=3)
    @cached_market_data
    def get_historical_data(self, symbol_name: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical data for a specific market indicator."""
        symbol = self.SYMBOLS.get(symbol_name.upper())
        if not symbol:
            # Try to use the input as symbol if not in map (e.g. for indices)
            symbol = symbol_name
            
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"error": "No data found"}
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "value": float(row['Close']),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": int(row['Volume'])
                })
                
            return {
                "indicator": symbol_name,
                "symbol": symbol,
                "data": data
            }
        except Exception as e:
            logger.error(f"Error fetching historical Yahoo data for {symbol_name}: {e}")
            return {"error": str(e)}

    @get_retry_decorator(max_attempts=3)
    @cached_market_data
    def analyze_fed_rate_probability(self) -> Dict[str, Any]:
        """
        Analyze Fed Funds Futures to estimate rate expectations.
        Note: This is a simplified approximation.
        Price of ZQ = 100 - Expected Fed Funds Rate
        """
        try:
            ticker = yf.Ticker(self.SYMBOLS['FED_FUNDS_FUTURES'], session=self.session)
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                price = float(hist.iloc[-1]['Close'])
                implied_rate = 100 - price
                
                return {
                    "futures_price": price,
                    "implied_fed_rate": implied_rate,
                    "date": hist.iloc[-1].name.strftime('%Y-%m-%d'),
                    "note": "Implied rate derived from 30-Day Fed Funds Futures (ZQ=F). 100 - Price = Rate."
                }
            return {"error": "No data for Fed Funds Futures"}
        except Exception as e:
            logger.error(f"Error analyzing Fed Rate probability: {e}")
            return {"error": str(e)}
