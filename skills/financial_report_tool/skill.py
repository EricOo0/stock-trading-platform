import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import edgar
from edgar import set_identity, Company
import re
import requests
import akshare as ak

class FinancialReportSkill:
    def __init__(self):
        self.name = "financial_report_tool"
        self.description = "Fetches financial report data and documents for companies."
        # Initialize Edgar (identity is required by SEC)
        try:
            set_identity("StockAnalysisAgent <agent@example.com>")
        except Exception as e:
            logger.warning(f"Failed to set edgar identity: {e}")

    def detect_market(self, symbol: str) -> Tuple[str, str]:
        """
        Detect which market the stock belongs to based on symbol format.
        Returns: (market, normalized_symbol)
        
        Markets:
        - 'US': American stocks (e.g., AAPL, TSLA)
        - 'HK': Hong Kong stocks (e.g., 0700.HK, 9988.HK)
        - 'A-SHARE': Chinese A-shares (e.g., 600036.SS, 000001.SZ)
        """
        symbol_upper = symbol.upper()
        
        # Hong Kong stocks
        if '.HK' in symbol_upper:
            return ('HK', symbol_upper)
        
        # A-shares (Shanghai/Shenzhen)
        if '.SS' in symbol_upper or '.SZ' in symbol_upper:
            # Extract the base code for AkShare (e.g., 600036.SS -> 600036)
            base_code = symbol_upper.split('.')[0]
            return ('A-SHARE', base_code)
        
        # Check if it's a pure number (likely Chinese stock without suffix)
        if symbol.isdigit():
            if len(symbol) == 6:
                # Could be A-share or HK
                if symbol.startswith('6'):
                    return ('A-SHARE', symbol)  # Shanghai
                elif symbol.startswith(('0', '3')):
                    return ('A-SHARE', symbol)  # Shenzhen
                else:
                    return ('HK', f"{symbol}.HK")  # Hong Kong
        
        # Default to US stock
        return ('US', symbol_upper)

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches key financial metrics (Revenue, Net Income, etc.) for the last few years.
        Supports US, HK, and A-share stocks via yfinance.
        """
        try:
            market, normalized_symbol = self.detect_market(symbol)
            logger.info(f"Fetching financial metrics for {symbol} (Market: {market}, Normalized: {normalized_symbol})")
            
            # For yfinance, we need the proper suffix
            if market == 'A-SHARE':
                # Determine exchange (Shanghai or Shenzhen)
                if normalized_symbol.startswith('6'):
                    yf_symbol = f"{normalized_symbol}.SS"
                else:
                    yf_symbol = f"{normalized_symbol}.SZ"
            elif market == 'HK':
                yf_symbol = normalized_symbol if '.HK' in normalized_symbol else f"{normalized_symbol}.HK"
            else:
                yf_symbol = normalized_symbol
            
            ticker = yf.Ticker(yf_symbol)
            
            # Get Financials (Income Statement)
            financials = ticker.financials
            if financials.empty:
                logger.warning(f"No financial data found for {yf_symbol}")
                return {
                    "status": "error", 
                    "message": "No financial data found",
                    "market": market
                }

            # Extract key metrics
            metrics = []
            financials_T = financials.T
            financials_T.sort_index(inplace=True)
            
            for date, row in financials_T.iterrows():
                item = {
                    "date": date.strftime("%Y-%m-%d"),
                    "revenue": row.get("Total Revenue", 0),
                    "net_income": row.get("Net Income", 0),
                    "gross_profit": row.get("Gross Profit", 0),
                    "operating_income": row.get("Operating Income", 0)
                }
                # Handle NaN
                for k, v in item.items():
                    if pd.isna(v):
                        item[k] = 0
                metrics.append(item)

            return {
                "status": "success",
                "symbol": symbol,
                "market": market,
                "normalized_symbol": yf_symbol,
                "currency": ticker.info.get("currency", "USD"),
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "unknown"}

    def get_latest_report(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches metadata about the latest financial report.
        Different strategies for different markets:
        - US: SEC EDGAR (edgartools)
        - HK: Web search for IR page
        - A-Share: AkShare announcement API
        """
        try:
            market, normalized_symbol = self.detect_market(symbol)
            logger.info(f"Fetching latest report for {symbol} (Market: {market})")
            
            if market == 'US':
                # Use SEC EDGAR for US stocks
                return self._get_us_report(normalized_symbol)
            elif market == 'HK':
                # Hong Kong stocks - use web search
                return self._get_hk_report(normalized_symbol)
            elif market == 'A-SHARE':
                # A-share stocks - use AkShare
                return self._get_ashare_report(normalized_symbol)
            else:
                return {
                    "status": "error",
                    "message": "Unknown market type",
                    "market": market
                }

        except Exception as e:
            logger.error(f"Error fetching report for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def _get_us_report(self, symbol: str) -> Dict[str, Any]:
        """Get US stock report from SEC EDGAR"""
        try:
            company = Company(symbol)
            filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
            
            if not filings:
                return {"status": "error", "message": "No filings found", "market": "US"}
            
            filing = filings
            
            return {
                "status": "success",
                "market": "US",
                "symbol": symbol,
                "form_type": filing.form,
                "filing_date": filing.filing_date,
                "accession_number": filing.accession_number,
                "url": filing.url,
                "download_url": filing.url  # SEC page URL
            }
        except Exception as e:
            logger.error(f"Error fetching US report for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "US"}

    def _get_hk_report(self, symbol: str) -> Dict[str, Any]:
        """Get HK stock report via web search"""
        try:
            # Extract stock code (remove .HK suffix)
            stock_code = symbol.replace('.HK', '')
            
            # Common HK company IR pages (Top companies)
            ir_pages = {
                '0700': 'https://www.tencent.com/zh-cn/investors.html',
                '9988': 'https://www.alibabagroup.com/cn/ir/home',
                '0941': 'https://www.cmhk.com/tc/ir/',
                '0388': 'https://www.hkex.com.hk/Investor-Relations',
                '0939': 'https://www.ccbintl.com/investor_relations/',
            }
            
            result = {
                "status": "partial",
                "market": "HK",
                "symbol": symbol,
                "message": "港股财报需要从公司投资者关系页面或披露易获取"
            }
            
            # If we have a known IR page, provide it
            if stock_code in ir_pages:
                result["ir_url"] = ir_pages[stock_code]
                result["download_url"] = ir_pages[stock_code]
                result["status"] = "success"
            
            # Always provide HKEXnews search link
            hkex_search_url = f"https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh&searchtype=1&code={stock_code}"
            result["hkexnews_url"] = hkex_search_url
            
            # If no direct IR, use HKEXnews as download URL
            if "download_url" not in result:
                result["download_url"] = hkex_search_url
            
            result["suggestions"] = [
                f"访问披露易搜索: {hkex_search_url}",
                "在搜索结果中查找'年度报告'或'Annual Report'"
            ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching HK report for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "HK"}

    def _get_cninfo_org_id(self, symbol: str) -> Optional[str]:
        """Get OrgID from cninfo for a given symbol"""
        try:
            search_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
            payload = {"keyWord": symbol}
            resp = requests.post(search_url, data=payload, headers=headers, timeout=5)
            data = resp.json()
            for item in data:
                if item.get("code") == symbol:
                    return item.get("orgId")
            return data[0].get("orgId") if data else None
        except Exception as e:
            logger.warning(f"Failed to get OrgID for {symbol}: {e}")
            return None

    def _fetch_cninfo_pdf(self, symbol: str, target: str = "latest") -> Dict[str, Any]:
        """
        Fetch PDF link from cninfo
        target: "latest" (any report), "annual" (annual report), "quarter" (quarterly)
        """
        try:
            clean_symbol = re.sub(r"\D", "", symbol)
            org_id = self._get_cninfo_org_id(clean_symbol)
            if not org_id:
                return {"status": "error", "message": "Stock not found"}

            query_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            base_file_url = "http://static.cninfo.com.cn/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            # Category mapping
            category_map = {
                "annual": "category_ndbg_szsh;category_ndbg_shmb;category_ndbg_bj;",
                "quarter": "category_sjdbg_szsh;category_sjdbg_shmb;category_sjdbg_bj;",
                "semi": "category_bndbg_szsh;category_bndbg_shmb;category_bndbg_bj;",
                "latest": "category_ndbg_szsh;category_bndbg_szsh;category_sjdbg_szsh;category_ndbg_shmb;category_bndbg_shmb;category_sjdbg_shmb;category_ndbg_bj;category_bndbg_bj;category_sjdbg_bj;"
            }
            
            selected_category = category_map.get(target, category_map["latest"])

            payload = {
                "pageNum": 1,
                "pageSize": 30,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": f"{clean_symbol},{org_id}",
                "category": selected_category,
                "isHLtitle": "true"
            }

            resp = requests.post(query_url, data=payload, headers=headers, timeout=10)
            data = resp.json()
            
            if not data.get("announcements"):
                return {"status": "error", "message": "No announcements found"}

            # Filter logic
            found_report = None
            for item in data["announcements"]:
                title = item["announcementTitle"]
                
                # Exclude summary, cancellation, english version
                if "摘要" in title or "取消" in title or "英文版" in title:
                    continue
                
                if item.get("adjunctUrl"):
                    found_report = item
                    break

            if found_report:
                raw_title = found_report["announcementTitle"]
                clean_title = re.sub(r'<[^>]+>', '', raw_title)
                
                report_type_str = "定期报告"
                if "年度" in clean_title: report_type_str = "年报"
                elif "半年度" in clean_title: report_type_str = "半年报"
                elif "季" in clean_title: report_type_str = "季报"

                return {
                    "status": "success",
                    "symbol": clean_symbol,
                    "title": clean_title,
                    "form_type": report_type_str,
                    "filing_date": pd.to_datetime(found_report['announcementTime'], unit='ms').strftime('%Y-%m-%d'),
                    "download_url": base_file_url + found_report["adjunctUrl"]
                }
            else:
                return {"status": "fail", "message": "未找到有效的 PDF 文件"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_ashare_report(self, symbol: str) -> Dict[str, Any]:
        """Get A-share stock report via cninfo API (PDF) or fallback to search page"""
        try:
            # 1. Try to fetch PDF directly using cninfo API
            logger.info(f"Fetching A-share report PDF for {symbol} via cninfo API")
            pdf_result = self._fetch_cninfo_pdf(symbol, target="latest")
            
            cninfo_search_url = f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={symbol}&orgId="

            if pdf_result.get("status") == "success":
                return {
                    "status": "success",
                    "market": "A-SHARE",
                    "symbol": symbol,
                    "title": pdf_result["title"],
                    "form_type": pdf_result["form_type"],
                    "filing_date": pdf_result["filing_date"],
                    "download_url": pdf_result["download_url"],
                    "url": pdf_result["download_url"],
                    "cninfo_url": cninfo_search_url,
                    "suggestions": [
                        f"已找到: {pdf_result['title']}",
                        "点击上方按钮直接下载 PDF",
                        "如需其他报告，请访问巨潮资讯网"
                    ]
                }
            else:
                logger.warning(f"Cninfo PDF fetch failed: {pdf_result.get('message')}, falling back to search page")
                # Fallback to search page
                return {
                    "status": "partial",
                    "market": "A-SHARE",
                    "symbol": symbol,
                    "message": "未找到最新财报PDF，请访问巨潮资讯网查看",
                    "cninfo_url": cninfo_search_url,
                    "download_url": cninfo_search_url,
                    "suggestions": [
                        f"访问巨潮资讯网: {cninfo_search_url}",
                        "在页面中筛选'定期报告'查看年报"
                    ]
                }
            
        except Exception as e:
            logger.error(f"Error fetching A-share report for {symbol}: {e}")
            cninfo_url = f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={symbol}"
            return {
                "status": "partial",
                "message": f"获取失败: {str(e)}",
                "market": "A-SHARE",
                "symbol": symbol,
                "cninfo_url": cninfo_url,
                "download_url": cninfo_url,
                "suggestions": [
                    f"访问巨潮资讯网: {cninfo_url}",
                    "手动搜索年度报告"
                ]
            }
if __name__ == "__main__":
    # Test
    skill = FinancialReportSkill()
    
    # Test US stock
    print("=== US Stock (AAPL) ===")
    print(skill.get_financial_metrics("AAPL"))
    print(skill.get_latest_report("AAPL"))
    
    # Test HK stock
    print("\n=== HK Stock (0700.HK) ===")
    print(skill.get_financial_metrics("0700.HK"))
    print(skill.get_latest_report("0700.HK"))
    
    # Test A-share
    print("\n=== A-Share (600036.SS) ===")
    print(skill.get_financial_metrics("600036.SS"))
    print(skill.get_latest_report("600036.SS"))
