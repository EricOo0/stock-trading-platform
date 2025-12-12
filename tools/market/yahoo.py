
import yfinance as yf
import pandas as pd
import requests
import random
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class YahooFinanceTool:
    """
    Yahoo Finance Tool
    Provides market data (US/HK/A-share), financial indicators, and macro indicators (VIX, DXY, etc.).
    """

    MACRO_SYMBOLS = {
        'VIX': '^VIX',          # CBOE Volatility Index
        'US10Y': '^TNX',        # Treasury Yield 10 Years
        'DXY': 'DX-Y.NYB',      # US Dollar Index
        'FED_FUNDS_FUTURES': 'ZQ=F' # Fed Funds Futures
    }

    def __init__(self, enable_rotation: bool = True):
        self.session = requests.Session()
        self.enable_rotation = enable_rotation
        self._setup_session_headers()
        self._setup_yfinance_session()

    def _setup_session_headers(self):
        user_agent = self._rotate_user_agent() if self.enable_rotation else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

    def _rotate_user_agent(self) -> str:
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)

    def _setup_yfinance_session(self):
        try:
            # Set custom session for yfinance globally/utils to avoid blocking
            if hasattr(yf, 'utils') and hasattr(yf.utils, 'session'):
                 yf.utils.session = self.session
            yf.session = self.session
        except: pass

    # ========================== Market Data ==========================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """Get real-time stock quote."""
        try:
            yahoo_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yahoo_symbol)
            
            # Fetch minimal history for price
            hist = ticker.history(period="2d")
            if hist.empty: return {"error": "Symbol not found"}
            
            # info = ticker.fast_info # Use fast_info for speed
            # But fast_info misses some fundamental data used in source
            # We can use fast_info for price and info for fundamentals if needed
            # For "quote", fast_info is good.
            # However source used fast_info but accessed fundamental keys from it? 
            # Actually fast_info has specific keys. Source mixed info and fast_info keys logic.
            # I will use fast_info for price and ticker.info for fundamentals if needed, but info is slow.
            # Let's stick to history for price + fast_info for basic metadata
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price # Approx
            
            # Volume unit conversion
            volume = int(hist['Volume'].iloc[-1])
            volume_display = volume // 100 if market == "A-share" else volume

            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close else 0.0

            return {
                "symbol": symbol,
                "current_price": round(float(current_price), 2),
                "open": round(float(hist['Open'].iloc[-1]), 2),
                "high": round(float(hist['High'].iloc[-1]), 2),
                "low": round(float(hist['Low'].iloc[-1]), 2),
                "prev_close": round(float(prev_close), 2),
                "change_amount": round(change_amount, 2),
                "change_percent": round(change_percent, 2),
                "volume": volume_display,
                "turnover": round(float(current_price * volume_display), 2),
                "timestamp": datetime.now().isoformat(),
                "market": market,
                "source": "yahoo"
            }
        except Exception as e:
            logger.error(f"Yahoo get_stock_quote failed for {symbol}: {e}")
            return {"error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_stock_history(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """Get historical data."""
        try:
            yahoo_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty: return []
            
            history = []
            for date, row in hist.iterrows():
                vol = int(row['Volume'])
                vol_display = vol // 100 if market == "A-share" else vol
                
                history.append({
                    'timestamp': date.strftime('%Y-%m-%d'),
                    'open': round(float(row['Open']), 2),
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': vol_display
                })
            return history
        except Exception as e:
            logger.error(f"Yahoo get_stock_history failed: {e}")
            return []

    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """Alias for get_stock_history."""
        return self.get_stock_history(symbol, market, period, interval)

    # ========================== Financial Data ==========================

    def get_financial_indicators(self, symbol: str, market: str, years: int = 3) -> Dict[str, Any]:
        """Get financial indicators (Revenue, Profit, Cashflow, Debt, Returns)."""
        try:
            yahoo_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yahoo_symbol)
            
            # Fetch all statements
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            # info = ticker.info # Slow! Avoid if possible or cache. Source uses it.
            # I will try to extract without info if possible, or accept latency.
            info = {} 
            try: info = ticker.info 
            except: pass
            
            if financials.empty and balance_sheet.empty: return self._empty_indicators()

            return {
                "revenue": self._extract_revenue(financials, cashflow),
                "profit": self._extract_profit(financials),
                "cashflow": self._extract_cashflow(cashflow, financials),
                "debt": self._extract_debt(balance_sheet),
                "shareholder_return": self._extract_shareholder_return(info, financials, balance_sheet),
                "valuation": self._extract_valuation(info),
                "history": self._extract_financial_history(financials, balance_sheet)
            }
        except Exception as e:
            logger.error(f"Yahoo get_financial_indicators failed: {e}")
            return self._empty_indicators()

    # ========================== Macro Data ==========================

    def get_macro_data(self, indicator: str) -> Dict[str, Any]:
        """Get macro data for supported indicators (VIX, US10Y, DXY, etc.)"""
        try:
             symbol = self.MACRO_SYMBOLS.get(indicator.upper(), indicator)
             ticker = yf.Ticker(symbol)
             hist = ticker.history(period="1d")
             if hist.empty: return {"error": "No data"}
             
             latest = hist.iloc[-1]
             return {
                 "indicator": indicator,
                 "symbol": symbol,
                 "value": float(latest['Close']),
                 "change": float(latest['Close'] - latest['Open']),
                 "date": latest.name.strftime('%Y-%m-%d')
             }
        except Exception as e:
            logger.error(f"Yahoo get_macro_data failed: {e}")
            return {"error": str(e)}

    def get_macro_history(self, indicator: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical macro data."""
        try:
             symbol = self.MACRO_SYMBOLS.get(indicator.upper(), indicator)
             ticker = yf.Ticker(symbol)
             # interval 1d
             hist = ticker.history(period=period, interval="1d")
             if hist.empty: return {"error": "No data"}
             
             data = []
             for date, row in hist.iterrows():
                 data.append({
                     "date": date.strftime('%Y-%m-%d'),
                     "value": float(row['Close']),
                     "open": float(row['Open']),
                     "high": float(row['High']),
                     "low": float(row['Low'])
                 })
             return {"indicator": indicator, "symbol": symbol, "data": data}
        except Exception as e:
            logger.error(f"Yahoo get_macro_history failed: {e}")
            return {"error": str(e)}

    # ========================== Helpers ==========================

    def _convert_symbol(self, symbol: str, market: str) -> str:
        if market == "A-share":
            if symbol.startswith(('600', '601', '603')): return f"{symbol}.SS"
            else: return f"{symbol}.SZ"
        elif market == "HK":
            # 0700 -> 0700.HK (Yahoo uses 4 digits usually? Source says 00700 -> 0700.HK)
            # Source: if symbol.startswith('00') and len==5 -> symbol[1:] . HK
            if len(symbol) == 5 and symbol.startswith("0"):
                 # Yahoo usually expects 4 digits for HK if leading zero, e.g. 0700.HK
                 # But strict check: 
                 if symbol.startswith("00"): return f"{symbol[1:]}.HK" # 00700 -> 0700.HK
                 return f"{symbol}.HK"
            return f"{symbol}.HK"
        return symbol.upper() # US

    def _empty_indicators(self):
         return {k: {} for k in ["revenue", "profit", "cashflow", "debt", "shareholder_return", "valuation"]} | {"history": []}

    # Extraction helpers (copied/adapted from source)
    def _safe_get(self, df, key, idx=0):
        try: 
            if key in df.index: return float(df.loc[key].iloc[idx])
        except: pass
        return 0.0

    def _extract_revenue(self, financials, cashflow):
        rev_now = self._safe_get(financials, 'Total Revenue', 0)
        rev_prev = self._safe_get(financials, 'Total Revenue', 1)
        ocf = self._safe_get(cashflow, 'Operating Cash Flow', 0)
        
        yoy = ((rev_now - rev_prev)/rev_prev * 100) if rev_prev else 0.0
        ratio = (ocf / rev_now) if rev_now else 0.0
        return {
            "revenue_yoy": round(yoy, 2), 
            "cash_to_revenue": round(ratio, 2),
            "core_revenue_ratio": None
        }

    def _extract_profit(self, financials):
        net = self._safe_get(financials, 'Net Income', 0)
        rev = self._safe_get(financials, 'Total Revenue', 0)
        gross = self._safe_get(financials, 'Gross Profit', 0)
        
        return {
            "gross_margin": round((gross/rev*100) if rev else 0, 2),
            "net_margin": round((net/rev*100) if rev else 0, 2),
            "non_recurring_eps": self._safe_get(financials, 'Basic EPS', 0)
        }

    def _extract_cashflow(self, cashflow, financials):
        ocf = self._safe_get(cashflow, 'Operating Cash Flow', 0)
        net = self._safe_get(financials, 'Net Income', 0)
        fcf = self._safe_get(cashflow, 'Free Cash Flow', 0)
        return {
            "ocf_to_net_profit": round((ocf/net) if net else 0, 2),
            "free_cash_flow": round(fcf, 2) if fcf else None
        }

    def _extract_debt(self, bs):
        liab = self._safe_get(bs, 'Total Liabilities Net Minority Interest', 0)
        assets = self._safe_get(bs, 'Total Assets', 0)
        curr_assets = self._safe_get(bs, 'Current Assets', 0)
        curr_liab = self._safe_get(bs, 'Current Liabilities', 0)
        
        return {
            "asset_liability_ratio": round((liab/assets*100) if assets else 0, 2),
            "current_ratio": round((curr_assets/curr_liab) if curr_liab else 0, 2)
        }

    def _extract_shareholder_return(self, info, fin, bs):
        roe = 0.0
        if not fin.empty and not bs.empty:
            net = self._safe_get(fin, 'Net Income', 0)
            equity = self._safe_get(bs, 'Stockholders Equity', 0)
            roe = (net/equity*100) if equity else 0
        
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        return {"roe": round(roe, 2), "dividend_yield": round(div_yield, 2)}

    def _extract_financial_history(self, fin, bs):
        hist = []
        if fin.empty: return hist
        for i in range(min(4, len(fin.columns))):
             try:
                 date = str(fin.columns[i].date())
                 net = self._safe_get(fin, 'Net Income', i)
                 rev = self._safe_get(fin, 'Total Revenue', i)
                 equity = self._safe_get(bs, 'Stockholders Equity', i)
                 
                 hist.append({
                     "date": date,
                     "net_margin": round((net/rev*100) if rev else 0, 2),
                         "roe": round((net/equity*100) if equity else 0, 2)
                 })
             except: pass
        return hist
        
    def _extract_valuation(self, info):
        """Extract PE and PB ratios."""
        try:
            pe = info.get('trailingPE', 0) or info.get('forwardPE', 0)
            pb = info.get('priceToBook', 0)
            return {
                "pe_ratio": round(pe, 2) if pe else None,
                "pb_ratio": round(pb, 2) if pb else None,
                "market_cap": info.get('marketCap', 0)
            }
        except:
            return {"pe_ratio": None, "pb_ratio": None}

if __name__ == "__main__":
    tool = YahooFinanceTool()
    # print(tool.get_stock_quote("AAPL", "US"))
    # print(tool.get_macro_data("VIX"))
