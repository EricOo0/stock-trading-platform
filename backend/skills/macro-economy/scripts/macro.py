import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import akshare as ak
import yfinance as yf
import pandas as pd
import argparse
import json
import logging
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("macro-economy-skill")

class MacroEconomySkill:
    """
    Macro Economy Skill
    Provides China and US macro economic data, market risk indicators, and economic calendar.
    """

    def __init__(self):
        self._setup_yfinance_session()

    def _setup_yfinance_session(self):
        """Setup custom session for yfinance to avoid some blocking."""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            yf.utils.session = session
        except Exception:
            pass

    def get_cn_macro(self, indicator: str) -> Dict[str, Any]:
        """
        Get China macro economic data.
        
        Args:
            indicator: One of 'GDP', 'CPI', 'PMI', 'PPI', 'M2', 'LPR'
        """
        try:
            indicator_upper = indicator.upper()
            if indicator_upper == 'GDP':
                df = ak.macro_china_gdp()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China GDP",
                    "value": float(latest['国内生产总值-绝对值']),
                    "growth_rate": float(latest['国内生产总值-同比增长']),
                    "period": str(latest['季度']),
                    "unit": "100 Million CNY"
                }
            elif indicator_upper == 'CPI':
                df = ak.macro_china_cpi()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China CPI",
                    "value": float(latest['全国-当月']),
                    "yoy": float(latest['全国-同比增长']),
                    "date": str(latest['月份']),
                    "unit": "Index"
                }
            elif indicator_upper == 'PMI':
                df = ak.macro_china_pmi()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China PMI",
                    "manufacturing": float(latest['制造业-指数']),
                    "non_manufacturing": float(latest['非制造业-指数']),
                    "date": str(latest['月份'])
                }
            elif indicator_upper == 'PPI':
                df = ak.macro_china_ppi_yearly()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China PPI",
                    "value": float(latest['今值']),
                    "date": str(latest['日期'])
                }
            elif indicator_upper == 'M2':
                df = ak.macro_china_money_supply()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China M2",
                    "value": float(latest['货币和准货币(M2)-数量(亿元)']),
                    "yoy": float(latest['货币和准货币(M2)-同比增长']),
                    "date": str(latest['月份'])
                }
            elif indicator_upper == 'LPR':
                df = ak.macro_china_lpr()
                if df.empty: return {"error": "No data"}
                # Sort by date desc to get latest
                df = df.sort_values('TRADE_DATE', ascending=False)
                latest = df.iloc[0]
                return {
                    "indicator": "China LPR",
                    "1y": float(latest['LPR1Y']),
                    "5y": float(latest['LPR5Y']),
                    "date": str(latest['TRADE_DATE'])
                }
            else:
                return {"error": f"Unsupported China indicator: {indicator}"}
        except Exception as e:
            logger.error(f"get_cn_macro failed: {e}")
            return {"error": str(e)}

    def get_us_macro(self, indicator: str) -> Dict[str, Any]:
        """
        Get US macro economic data.
        
        Args:
            indicator: 'CPI', 'UNEMPLOYMENT', 'GDP', 'INTEREST_RATE'
        """
        try:
            indicator_upper = indicator.upper()
            
            # Use AkShare for official stats where available
            if indicator_upper == 'CPI':
                # ak.macro_usa_cpi_monthly()
                try:
                    df = ak.macro_usa_cpi_monthly()
                    if not df.empty:
                        latest = df.iloc[0]
                        return {
                            "indicator": "US CPI",
                            "value": float(latest['今值']),
                            "date": str(latest['日期']),
                            "unit": "%" # Usually monthly rate or index, depends on specific API return. macro_usa_cpi_monthly is monthly rate usually.
                        }
                except:
                    pass
                
            elif indicator_upper == 'UNEMPLOYMENT':
                try:
                    df = ak.macro_usa_unemployment_rate() # Returns monthly rate
                    if not df.empty:
                        latest = df.iloc[0]
                        return {
                            "indicator": "US Unemployment Rate",
                            "value": float(latest['今值']),
                            "date": str(latest['日期']),
                            "unit": "%"
                        }
                except:
                    pass

            elif indicator_upper == 'INTEREST_RATE':
                # Fed funds rate
                try:
                    df = ak.macro_usa_fed_interest_rate()
                    if not df.empty:
                        latest = df.iloc[0]
                        return {
                            "indicator": "Fed Funds Rate",
                            "value": float(latest['今值']),
                            "date": str(latest['日期']),
                            "unit": "%"
                        }
                except:
                    pass

            # Fallback or additional market-based macro using Yahoo
            # E.g. US10Y handled in get_market_risk
            
            return {"error": f"Unsupported or unavailable US indicator: {indicator}"}

        except Exception as e:
            logger.error(f"get_us_macro failed: {e}")
            return {"error": str(e)}

    def get_market_risk(self) -> Dict[str, Any]:
        """
        Get Global Market Risk Indicators (VIX, DXY, US10Y, Gold, Oil).
        """
        symbols = {
            'VIX': '^VIX',          # CBOE Volatility Index
            'US10Y': '^TNX',        # Treasury Yield 10 Years
            'DXY': 'DX=F',          # US Dollar Index
            'GOLD': 'GC=F',         # Gold Futures
            'CRUDE_OIL': 'CL=F'     # Crude Oil
        }
        
        results = {}
        try:
            tickers = yf.Tickers(" ".join(symbols.values()))
            
            for key, symbol in symbols.items():
                try:
                    ticker = tickers.tickers[symbol]
                    # Use fast_info for latest price
                    # Note: fast_info might be 'last_price'
                    price = None
                    change = None
                    
                    # Try history for consistency
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        current = float(hist['Close'].iloc[-1])
                        prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
                        price = round(current, 3)
                        change = round(current - prev, 3)
                        pct_change = round((change / prev) * 100, 2) if prev else 0.0
                        
                        results[key] = {
                            "value": price,
                            "change": change,
                            "pct_change": pct_change,
                            "date": hist.index[-1].strftime('%Y-%m-%d')
                        }
                    else:
                        results[key] = {"error": "No data"}
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch {key} ({symbol}): {e}")
                    results[key] = {"error": str(e)}
                    
            return results
        except Exception as e:
            logger.error(f"get_market_risk failed: {e}")
            return {"error": str(e)}

    def get_economic_calendar(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get economic calendar events.
        
        Args:
            date_str: YYYYMMDD string. If None, use today.
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y%m%d")

            df = ak.news_economic_baidu(date=date_str)
            if df.empty:
                return []

            events = []
            for _, row in df.iterrows():
                region = str(row['地区'])
                # Filter for key regions
                if region not in ["中国", "美国", "欧元区", "日本", "英国"]:
                    continue

                events.append({
                    "date": str(row['日期']),
                    "time": str(row['时间']),
                    "region": region,
                    "event": str(row['事件']),
                    "previous": row['前值'],
                    "consensus": row['预期'],
                    "actual": row['公布'],
                    "importance": row['重要性']
                })
            return events
        except Exception as e:
            logger.error(f"get_economic_calendar failed: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Macro Economy Skill")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: cn_macro
    cn_parser = subparsers.add_parser("cn_macro", help="Get China macro data")
    cn_parser.add_argument("indicator", type=str, help="Indicator name (GDP, CPI, PMI, etc.)")

    # Command: us_macro
    us_parser = subparsers.add_parser("us_macro", help="Get US macro data")
    us_parser.add_argument("indicator", type=str, help="Indicator name (CPI, UNEMPLOYMENT, etc.)")

    # Command: risk
    subparsers.add_parser("risk", help="Get market risk indicators")

    # Command: calendar
    cal_parser = subparsers.add_parser("calendar", help="Get economic calendar")
    cal_parser.add_argument("--date", type=str, help="Date YYYYMMDD", default=None)

    args = parser.parse_args()
    skill = MacroEconomySkill()

    if args.command == "cn_macro":
        print(json.dumps(skill.get_cn_macro(args.indicator), indent=2, ensure_ascii=False))
    elif args.command == "us_macro":
        print(json.dumps(skill.get_us_macro(args.indicator), indent=2, ensure_ascii=False))
    elif args.command == "risk":
        print(json.dumps(skill.get_market_risk(), indent=2, ensure_ascii=False))
    elif args.command == "calendar":
        print(json.dumps(skill.get_economic_calendar(args.date), indent=2, ensure_ascii=False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
