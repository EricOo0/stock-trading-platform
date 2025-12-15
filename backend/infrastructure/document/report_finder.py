
import logging
import requests
import pandas as pd
import re
from typing import Dict, Any, Optional
from edgar import Company, set_identity

logger = logging.getLogger(__name__)

class ReportFinderTool:
    """
    Finds financial reports (annual/quarterly) for US, HK, and A-share stocks.
    """
    
    def __init__(self):
        try:
            # Set identity for SEC EDGAR
            set_identity("StockTradingPlatform <agent@example.com>")
            
            # Suppress noisy edgar logs (especially 304 errors which act as cache hits but log as errors)
            logging.getLogger("edgar").setLevel(logging.CRITICAL)
            logging.getLogger("edgar.core").setLevel(logging.CRITICAL)
            
        except Exception as e:
            logger.warning(f"Failed to set EDGAR identity: {e}")

    def get_latest_report(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        Fetch metadata for the latest financial report.
        """
        try:
            if market == 'US':
                return self._get_us_report(symbol)
            elif market == 'HK':
                return self._get_hk_report(symbol)
            elif market == 'A-share':
                return self._get_ashare_report(symbol)
            else:
                return {"error": f"Unsupported market: {market}"}
        except Exception as e:
            logger.error(f"Error fetching report for {symbol}: {e}")
            return {"error": str(e)}

    def _get_us_report(self, symbol: str) -> Dict[str, Any]:
        try:
            company = Company(symbol)
            filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
            
            if not filings:
                return {"error": "No filings found", "market": "US"}
            
            # edgartools latest() returns a filing object which might need adjustment to get dict
            # Assuming standard usage
            return {
                "status": "success",
                "market": "US",
                "symbol": symbol,
                "title": f"{filings.form} Filing",
                "form_type": filings.form,
                "filing_date": str(filings.filing_date),
                "url": filings.url, # SEC URL
                "download_url": filings.url # Usually HTML/Text, PDF might be separate but url is standard
            }
        except Exception as e:
            logger.warning(f"edgartools failed: {e}. Attempting manual SEC fetch.")
            try:
                return self._get_us_report_manual(symbol)
            except Exception as manual_e:
                logger.error(f"US report fetch failed (both methods): {manual_e}")
                return {"error": str(manual_e)}

    def _get_us_report_manual(self, symbol: str) -> Dict[str, Any]:
        """
        Manual fallback to fetch SEC filings without using edgartools.
        """
        headers = {
            "User-Agent": "StockTradingPlatform <agent@example.com>",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        
        # 1. Get CIK from Tickers JSON
        # Note: We use a different URL or just ignores cache to avoid 304 if possible, 
        # or just standard requests which handles 304 as distinct from error if handled right.
        # Here we just fetch it.
        try:
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            resp = requests.get(tickers_url, headers=headers, timeout=10)
            resp.raise_for_status()
            tickers_data = resp.json()
            
            cik_str = None
            for idx, item in tickers_data.items():
                if item['ticker'] == symbol.upper():
                    cik_str = str(item['cik_str']).zfill(10)
                    break
            
            if not cik_str:
                raise ValueError(f"Symbol {symbol} not found in SEC tickers")

            # 2. Fetch Submissions
            # https://data.sec.gov/submissions/CIKxxxxxxxxxx.json
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
            # Host must be data.sec.gov
            headers["Host"] = "data.sec.gov"
            
            resp = requests.get(submissions_url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            # 3. Find latest 10-K or 10-Q
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
                 
            # Construct URL
            # https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primaryDoc}
            # Accession number needs dashes removed for the path
            acc_num_clean = accession_nums[found_idx].replace('-', '')
            doc_name = primary_docs[found_idx]
            
            # Use IX Viewer URL for better readability? Or direct?
            # Direct: https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_num_clean}/{doc_name}
            # NOTE: CIK in path is integer (no leading zeros usually? check standard)
            # Actually SEC Archives path uses CIK as integer usually.
            
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
        """Get HK stock report via web search knowledge (heuristic)"""
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
        """Get A-share stock report via cninfo API (PDF)"""
        try:
            # Remove prefixes
            clean_symbol = re.sub(r"\D", "", symbol)
            
            # 1. Get OrgID
            org_id = self._get_cninfo_org_id(clean_symbol)
            if not org_id:
                return {"error": "Stock not found on cninfo"}

            # 2. Query Announcements
            query_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            base_file_url = "http://static.cninfo.com.cn/"
            
            # "latest" category
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
