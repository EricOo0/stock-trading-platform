import argparse
import json
import logging
import re
import random
import sys
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

import pandas as pd
import requests

# Try imports that might be missing in some environments
try:
    import akshare as ak
except ImportError:
    ak = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from edgar import Company, set_identity
except ImportError:
    Company = None
    set_identity = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("financial-report-skill")

class FinancialReportSkill:
    """
    Financial Report Skill
    Provides financial indicators and report search capabilities for A-share, US, and HK stocks.
    """

    def __init__(self):
        self.session = requests.Session()
        self._setup_session_headers()
        
        # Identity for SEC EDGAR
        if set_identity:
            try:
                set_identity("StockAnalysisTool <admin@stockanalysistool.com>")
                # Suppress noisy edgar logs
                logging.getLogger("edgar").setLevel(logging.CRITICAL)
                logging.getLogger("edgar.core").setLevel(logging.CRITICAL)
            except Exception as e:
                logger.warning(f"Failed to set EDGAR identity: {e}")

        # Setup yfinance session
        if yf:
            try:
                if hasattr(yf, 'utils') and hasattr(yf.utils, 'session'):
                    yf.utils.session = self.session
                yf.session = self.session
            except Exception:
                pass

    def _setup_session_headers(self):
        user_agent = self._rotate_user_agent()
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

    def _detect_market(self, symbol: str) -> str:
        """Detect market type from symbol."""
        if symbol.startswith("."): return 'US_INDEX'
        if symbol in ["HSI", "HSTECH"]: return 'HK_INDEX'
        if symbol in ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]: return 'CN_INDEX'

        if symbol.startswith(("sh", "sz", "bj")): return 'A-share'
        if symbol.isdigit():
            if len(symbol) == 6:
                if symbol.startswith(("51", "159", "56", "58", "16")): return 'ETF'
                if symbol.startswith(("60", "00", "30", "68", "8", "4")): return 'A-share'
            if len(symbol) == 5: return 'HK'
        if symbol.isalpha(): return 'US'
        return 'A-share' # Default

    def get_financial_indicators(self, symbol: str, market: Optional[str] = None, years: int = 3) -> Dict[str, Any]:
        """
        Get financial indicators (Revenue, Profit, Cashflow, Debt, Returns).
        """
        if not market:
            market = self._detect_market(symbol)
        
        logger.info(f"Fetching financial indicators for {symbol} ({market})")

        if market == 'A-share':
            return self._get_ashare_indicators(symbol, years)
        elif market in ['US', 'HK']:
            return self._get_yahoo_indicators(symbol, market, years)
        else:
            return {"error": f"Financial indicators not supported for market: {market}"}

    def _get_ashare_indicators(self, symbol: str, years: int) -> Dict[str, Any]:
        if not ak:
            return {"error": "akshare not installed"}
        
        try:
            # Try primary source first
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df.empty or len(df) < 2 or (len(df) > 0 and df.iloc[0].get('日期') == '1900-01-01'):
                # Fallback to abstract
                logger.info(f"Primary financial indicators empty for {symbol}, trying abstract...")
                return self._get_ashare_indicators_from_abstract(symbol, years)

            # AkShare data is reversed (oldest first)
            df = df.iloc[::-1].reset_index(drop=True)
            df = df.head(years * 4 + 1)

            if len(df) > 0 and df.iloc[0].get('日期') == '1900-01-01':
                df = df.iloc[1:].reset_index(drop=True)

            return {
                "revenue": self._extract_ashare_revenue(df),
                "profit": self._extract_ashare_profit(df),
                "cashflow": self._extract_ashare_cashflow(df),
                "debt": self._extract_ashare_debt(df),
                "shareholder_return": self._extract_ashare_return(df),
                "history": self._extract_ashare_history(df)
            }
        except Exception as e:
            logger.error(f"AkShare get_financial_indicators failed: {e}")
            try:
                return self._get_ashare_indicators_from_abstract(symbol, years)
            except:
                return self._empty_indicators()

    def _get_ashare_indicators_from_abstract(self, symbol: str, years: int) -> Dict[str, Any]:
        try:
            df = ak.stock_financial_abstract(symbol=symbol)
            if df.empty: return self._empty_indicators()

            date_cols = [c for c in df.columns if c.isdigit() and len(c) == 8]
            date_cols.sort(reverse=True)
            
            limit = years * 4 + 1
            selected_dates = date_cols[:limit]
            
            if not selected_dates: return self._empty_indicators()

            def get_series(metric_name):
                row = df[df['指标'] == metric_name]
                if row.empty: return pd.Series(0, index=selected_dates)
                return row.iloc[0][selected_dates].apply(lambda x: float(x) if x else 0.0)

            new_df = pd.DataFrame(index=selected_dates)
            new_df['日期'] = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in selected_dates]

            mapping = {
                '主营业务收入增长率(%)': '营业总收入增长率',
                '每股经营性现金流(元)': '每股经营现金流',
                '销售毛利率(%)': '毛利率',
                '销售净利率(%)': '销售净利率',
                '资产负债率(%)': '资产负债率',
                '流动比率': '流动比率',
                '净资产收益率(%)': '净资产收益率(ROE)'
            }

            for target, source in mapping.items():
                new_df[target] = get_series(source)

            new_df['主营利润比重'] = 0.0
            new_df['每股收益_调整后(元)'] = get_series('基本每股收益')
            new_df['扣除非经常性损益后的每股收益(元)'] = get_series('基本每股收益')
            new_df['股息发放率(%)'] = 0.0

            return {
                "revenue": self._extract_ashare_revenue(new_df),
                "profit": self._extract_ashare_profit(new_df),
                "cashflow": self._extract_ashare_cashflow(new_df),
                "debt": self._extract_ashare_debt(new_df),
                "shareholder_return": self._extract_ashare_return(new_df),
                "history": self._extract_ashare_history(new_df)
            }

        except Exception as e:
            logger.error(f"AkShare abstract fallback failed: {e}")
            return self._empty_indicators()

    def _get_yahoo_indicators(self, symbol: str, market: str, years: int) -> Dict[str, Any]:
        if not yf:
            return {"error": "yfinance not installed"}
        
        try:
            yahoo_symbol = self._convert_yahoo_symbol(symbol, market)
            ticker = yf.Ticker(yahoo_symbol)
            
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            # Use info if available, but wrap in try-except
            info = {}
            try:
                info = ticker.info
            except:
                pass

            if financials.empty and balance_sheet.empty:
                return self._empty_indicators()

            return {
                "revenue": self._extract_yahoo_revenue(financials, cashflow),
                "profit": self._extract_yahoo_profit(financials),
                "cashflow": self._extract_yahoo_cashflow(cashflow, financials),
                "debt": self._extract_yahoo_debt(balance_sheet),
                "shareholder_return": self._extract_yahoo_return(info, financials, balance_sheet),
                "valuation": self._extract_yahoo_valuation(info),
                "history": self._extract_yahoo_history(financials, balance_sheet)
            }
        except Exception as e:
            logger.error(f"Yahoo get_financial_indicators failed: {e}")
            return self._empty_indicators()

    def search_reports(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch metadata for the latest financial report.
        """
        if not market:
            market = self._detect_market(symbol)
        
        if market == 'US':
            return self._get_us_report(symbol)
        elif market == 'HK':
            return self._get_hk_report(symbol)
        elif market == 'A-share':
            return self._get_ashare_report(symbol)
        else:
            return {"error": f"Report search not supported for market: {market}"}

    def _get_us_report(self, symbol: str) -> Dict[str, Any]:
        if not Company:
            return self._get_us_report_manual(symbol)

        try:
            company = Company(symbol)
            filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
            
            if not filings:
                return {"error": "No filings found", "market": "US"}
            
            return {
                "status": "success",
                "market": "US",
                "symbol": symbol,
                "title": f"{filings.form} Filing",
                "form_type": filings.form,
                "filing_date": str(filings.filing_date),
                "url": filings.url,
                "download_url": filings.url
            }
        except Exception as e:
            logger.warning(f"edgartools failed: {e}. Attempting manual SEC fetch.")
            try:
                return self._get_us_report_manual(symbol)
            except Exception as manual_e:
                return {"error": f"US report fetch failed: {manual_e}"}

    def _get_us_report_manual(self, symbol: str) -> Dict[str, Any]:
        headers = {
            "User-Agent": "StockAnalysisTool <admin@stockanalysistool.com>",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
            "Accept": "application/json"
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        try:
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            resp = session.get(tickers_url, timeout=10)
            resp.raise_for_status()
            tickers_data = resp.json()
            
            cik_str = None
            for idx, item in tickers_data.items():
                if item['ticker'] == symbol.upper():
                    cik_str = str(item['cik_str']).zfill(10)
                    break
            
            if not cik_str:
                raise ValueError(f"Symbol {symbol} not found in SEC tickers")

            submissions_url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
            session.headers.update({"Host": "data.sec.gov"})
            
            resp = session.get(submissions_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            filings = data.get('filings', {}).get('recent', {})
            if not filings:
                raise ValueError("No recent filings found")
                
            forms = filings.get('form', [])
            accession_nums = filings.get('accessionNumber', [])
            primary_docs = filings.get('primaryDocument', [])
            dates = filings.get('filingDate', [])
            
            found_idx = -1
            target_forms = ['10-K', '10-Q']
            
            for i, form in enumerate(forms):
                if form in target_forms:
                    found_idx = i
                    break
            
            if found_idx == -1:
                 raise ValueError("No 10-K or 10-Q found in recent filings")
                 
            acc_num_clean = accession_nums[found_idx].replace('-', '')
            doc_name = primary_docs[found_idx]
            cik_int = int(cik_str)
            full_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_num_clean}/{doc_name}"
            
            return {
                "status": "success",
                "market": "US",
                "symbol": symbol,
                "title": f"{forms[found_idx]} Filing",
                "form_type": forms[found_idx],
                "filing_date": dates[found_idx],
                "url": full_url,
                "download_url": full_url
            }

        except Exception as e:
            raise ValueError(f"Manual fetch failed: {e}")

    def _get_hk_report(self, symbol: str) -> Dict[str, Any]:
        stock_code = symbol.replace('.HK', '')
        hkex_search_url = f"https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh&searchtype=1&code={stock_code}"
        
        return {
            "status": "partial",
            "market": "HK",
            "symbol": symbol,
            "title": "HKEX Search",
            "download_url": hkex_search_url,
            "note": "Direct PDF link not available via simple API. Please check HKEX."
        }

    def _get_ashare_report(self, symbol: str) -> Dict[str, Any]:
        try:
            clean_symbol = re.sub(r"\D", "", symbol)
            org_id = self._get_cninfo_org_id(clean_symbol)
            if not org_id:
                return {"error": "Stock not found on cninfo"}

            query_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            base_file_url = "http://static.cninfo.com.cn/"
            category = "category_ndbg_szsh;category_bndbg_szsh;category_sjdbg_szsh;category_ndbg_shmb;category_bndbg_shmb;category_sjdbg_shmb;"
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
            
            payload = {
                "pageNum": 1, "pageSize": 30, "column": "szse", "tabName": "fulltext",
                "plate": "", "stock": f"{clean_symbol},{org_id}",
                "category": category, "isHLtitle": "true"
            }

            resp = requests.post(query_url, data=payload, headers=headers, timeout=10)
            data = resp.json()
            
            if not data.get("announcements"):
                return {"error": "No announcements found"}

            for item in data["announcements"]:
                title = item["announcementTitle"]
                if "摘要" in title or "取消" in title: continue
                
                if item.get("adjunctUrl"):
                    return {
                        "status": "success",
                        "market": "A-share",
                        "symbol": symbol,
                        "title": re.sub(r'<[^>]+>', '', title),
                        "filing_date": pd.to_datetime(item['announcementTime'], unit='ms').strftime('%Y-%m-%d'),
                        "download_url": base_file_url + item["adjunctUrl"]
                    }
            
            return {"error": "No PDF found in recent announcements"}

        except Exception as e:
            logger.error(f"A-share report fetch failed: {e}")
            return {"error": str(e)}

    def _get_cninfo_org_id(self, symbol: str) -> Optional[str]:
        try:
            search_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
            headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            payload = {"keyWord": symbol}
            resp = requests.post(search_url, data=payload, headers=headers, timeout=5)
            data = resp.json()
            for item in data:
                if item.get("code") == symbol: return item.get("orgId")
            return data[0].get("orgId") if data else None
        except Exception:
            return None

    def get_report_content(self, url: str) -> Dict[str, Any]:
        """
        Download and return report content.
        For text/HTML/JSON, return content. For PDF, return info (no parsing in this tool yet).
        """
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            
            content_type = resp.headers.get('Content-Type', '')
            
            if 'pdf' in content_type or url.endswith('.pdf'):
                return {
                    "type": "pdf",
                    "size": len(resp.content),
                    "content": "PDF content not displayed. Use a PDF parser."
                }
            else:
                return {
                    "type": "text",
                    "content": resp.text[:10000] + "..." if len(resp.text) > 10000 else resp.text
                }
        except Exception as e:
            return {"error": f"Download failed: {e}"}

    # --- Helpers ---

    def _convert_yahoo_symbol(self, symbol: str, market: str) -> str:
        if market == "A-share":
            if symbol.startswith(('600', '601', '603')): return f"{symbol}.SS"
            else: return f"{symbol}.SZ"
        elif market == "HK":
            if len(symbol) == 5 and symbol.startswith("0"):
                 if symbol.startswith("00"): return f"{symbol[1:]}.HK"
                 return f"{symbol}.HK"
            return f"{symbol}.HK"
        return symbol.upper()

    def _safe_get(self, obj, key, default=0.0):
        if isinstance(obj, pd.Series) or isinstance(obj, dict):
            val = obj.get(key, default)
        elif hasattr(obj, 'loc') and key in obj.index: # DataFrame/Series check
             return float(obj.loc[key])
        else:
            val = default
            
        if pd.isna(val): return default
        try: return float(val)
        except: return default

    def _empty_indicators(self):
        return {k: {} for k in ["revenue", "profit", "cashflow", "debt", "shareholder_return", "valuation"]} | {"history": []}

    # A-share Extractors
    def _extract_ashare_revenue(self, df):
        if df.empty: return {}
        latest = df.iloc[0]
        return {
            "revenue_yoy": round(self._safe_get(latest, '主营业务收入增长率(%)'), 2),
            "core_revenue_ratio": round(self._safe_get(latest, '主营利润比重'), 2),
            "cash_to_revenue": 1.0 if self._safe_get(latest, '每股经营性现金流(元)') > 0 else 0.0
        }

    def _extract_ashare_profit(self, df):
        if df.empty: return {}
        latest = df.iloc[0]
        return {
            "non_recurring_eps": round(self._safe_get(latest, '扣除非经常性损益后的每股收益(元)'), 4),
            "gross_margin": round(self._safe_get(latest, '销售毛利率(%)'), 2),
            "net_margin": round(self._safe_get(latest, '销售净利率(%)'), 2)
        }

    def _extract_ashare_cashflow(self, df):
        if df.empty: return {}
        latest = df.iloc[0]
        ocf = self._safe_get(latest, '每股经营性现金流(元)')
        eps = self._safe_get(latest, '每股收益_调整后(元)', 1.0)
        return {
            "ocf_to_net_profit": round(ocf / eps if eps != 0 else 0.0, 2),
            "free_cash_flow": None
        }

    def _extract_ashare_debt(self, df):
        if df.empty: return {}
        latest = df.iloc[0]
        return {
            "asset_liability_ratio": round(self._safe_get(latest, '资产负债率(%)'), 2),
            "current_ratio": round(self._safe_get(latest, '流动比率'), 2)
        }

    def _extract_ashare_return(self, df):
        if df.empty: return {}
        latest = df.iloc[0]
        return {
            "dividend_yield": round(self._safe_get(latest, '股息发放率(%)'), 2),
            "roe": round(self._safe_get(latest, '净资产收益率(%)'), 2)
        }

    def _extract_ashare_history(self, df):
        history = []
        for _, row in df.iterrows():
            history.append({
                "date": str(row.get('日期', '')),
                "roe": round(self._safe_get(row, '净资产收益率(%)'), 2),
                "gross_margin": round(self._safe_get(row, '销售毛利率(%)'), 2),
                "net_margin": round(self._safe_get(row, '销售净利率(%)'), 2),
                "asset_liability_ratio": round(self._safe_get(row, '资产负债率(%)'), 2)
            })
        return history

    # Yahoo Extractors
    def _yahoo_safe_get(self, df, key, idx=0):
        try: 
            if key in df.index: return float(df.loc[key].iloc[idx])
        except: pass
        return 0.0

    def _extract_yahoo_revenue(self, financials, cashflow):
        rev_now = self._yahoo_safe_get(financials, 'Total Revenue', 0)
        rev_prev = self._yahoo_safe_get(financials, 'Total Revenue', 1)
        ocf = self._yahoo_safe_get(cashflow, 'Operating Cash Flow', 0)
        
        yoy = ((rev_now - rev_prev)/rev_prev * 100) if rev_prev else 0.0
        ratio = (ocf / rev_now) if rev_now else 0.0
        return {
            "revenue_yoy": round(yoy, 2), 
            "cash_to_revenue": round(ratio, 2),
            "core_revenue_ratio": None
        }

    def _extract_yahoo_profit(self, financials):
        net = self._yahoo_safe_get(financials, 'Net Income', 0)
        rev = self._yahoo_safe_get(financials, 'Total Revenue', 0)
        gross = self._yahoo_safe_get(financials, 'Gross Profit', 0)
        
        return {
            "gross_margin": round((gross/rev*100) if rev else 0, 2),
            "net_margin": round((net/rev*100) if rev else 0, 2),
            "non_recurring_eps": self._yahoo_safe_get(financials, 'Basic EPS', 0)
        }

    def _extract_yahoo_cashflow(self, cashflow, financials):
        ocf = self._yahoo_safe_get(cashflow, 'Operating Cash Flow', 0)
        net = self._yahoo_safe_get(financials, 'Net Income', 0)
        fcf = self._yahoo_safe_get(cashflow, 'Free Cash Flow', 0)
        return {
            "ocf_to_net_profit": round((ocf/net) if net else 0, 2),
            "free_cash_flow": round(fcf, 2) if fcf else None
        }

    def _extract_yahoo_debt(self, bs):
        liab = self._yahoo_safe_get(bs, 'Total Liabilities Net Minority Interest', 0)
        assets = self._yahoo_safe_get(bs, 'Total Assets', 0)
        curr_assets = self._yahoo_safe_get(bs, 'Current Assets', 0)
        curr_liab = self._yahoo_safe_get(bs, 'Current Liabilities', 0)
        
        return {
            "asset_liability_ratio": round((liab/assets*100) if assets else 0, 2),
            "current_ratio": round((curr_assets/curr_liab) if curr_liab else 0, 2)
        }

    def _extract_yahoo_return(self, info, fin, bs):
        roe = 0.0
        if not fin.empty and not bs.empty:
            net = self._yahoo_safe_get(fin, 'Net Income', 0)
            equity = self._yahoo_safe_get(bs, 'Stockholders Equity', 0)
            roe = (net/equity*100) if equity else 0
        
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        return {"roe": round(roe, 2), "dividend_yield": round(div_yield, 2)}
    
    def _extract_yahoo_valuation(self, info):
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

    def _extract_yahoo_history(self, fin, bs):
        hist = []
        if fin.empty: return hist
        for i in range(min(4, len(fin.columns))):
             try:
                 date = str(fin.columns[i].date())
                 net = self._yahoo_safe_get(fin, 'Net Income', i)
                 rev = self._yahoo_safe_get(fin, 'Total Revenue', i)
                 equity = self._yahoo_safe_get(bs, 'Stockholders Equity', i)
                 
                 hist.append({
                     "date": date,
                     "net_margin": round((net/rev*100) if rev else 0, 2),
                     "roe": round((net/equity*100) if equity else 0, 2)
                 })
             except: pass
        return hist

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Report Skill")
    parser.add_argument("--action", choices=["indicators", "search", "content"], required=True, help="Action to perform")
    parser.add_argument("--symbol", help="Stock symbol (e.g. 600036, AAPL)")
    parser.add_argument("--market", help="Market type (A-share, US, HK)")
    parser.add_argument("--url", help="Report URL for content download")
    
    args = parser.parse_args()
    skill = FinancialReportSkill()
    
    if args.action == "indicators":
        if not args.symbol:
            print(json.dumps({"error": "Symbol required"}))
        else:
            print(json.dumps(skill.get_financial_indicators(args.symbol, args.market), indent=2, ensure_ascii=False))
            
    elif args.action == "search":
        if not args.symbol:
            print(json.dumps({"error": "Symbol required"}))
        else:
            print(json.dumps(skill.search_reports(args.symbol, args.market), indent=2, ensure_ascii=False))
            
    elif args.action == "content":
        if not args.url:
            print(json.dumps({"error": "URL required"}))
        else:
            print(json.dumps(skill.get_report_content(args.url), indent=2, ensure_ascii=False))
