
import logging
import re
from typing import Dict, Any, List, Optional, Union

# Import underlying tools
from tools.market.sina import SinaFinanceTool
from tools.market.akshare import AkShareTool
from tools.market.yahoo import YahooFinanceTool
from tools.search.tavily import TavilyTool
from tools.search.serp import SerpAppTool
from tools.search.duckduckgo import DuckDuckGoTool
from tools.analysis.finbert import FinBERTTool
from tools.reports.pdf_parse import PDFParseTool
from tools.reports.finder import ReportFinderTool
from tools.reports.content import ReportContentTool
from tools.reports.analysis import ReportAnalysisTool
from edgar import Company

from tools.config import config

logger = logging.getLogger(__name__)

class Tools:
    """
    Unified entry point for all financial tools.
    Handles routing, fallbacks, and parameter normalization.
    """

    def __init__(self, tavily_api_key: Optional[str] = None, serp_api_key: Optional[str] = None, llama_cloud_api_key: Optional[str] = None):
        # Load config automatically if keys not provided
        if not tavily_api_key:
            tavily_api_key = config.get_api_key("tavily")
        
        if not serp_api_key:
            serp_api_key = config.get_api_key("serpapi")

        if not llama_cloud_api_key:
            llama_cloud_api_key = config.get_api_key("llama_cloud")

        # Initialize sub-tools
        self.sina = SinaFinanceTool()
        self.akshare = AkShareTool()
        self.yahoo = YahooFinanceTool()
        self.finbert = FinBERTTool()
        self.report_finder = ReportFinderTool()
        self.report_content = ReportContentTool()
        self.report_analyst = ReportAnalysisTool()
        
        # Pass key explicitly to PDF tool
        self.pdf = PDFParseTool(api_key=llama_cloud_api_key) 
        
        # Search Tools
        self.tavily = TavilyTool(tavily_api_key) if tavily_api_key else None
        self.serp = SerpAppTool(serp_api_key) if serp_api_key else None
        self.ddg = DuckDuckGoTool()

    def get_stock_price(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time stock price with automatic market detection and fallback.
        If market is provided ('A-share', 'US', 'HK'), auto-detection is skipped.
        """
        market = market or self._detect_market(symbol)
        
        # Strategy: A-share (Sina->AkShare->Yahoo), US/HK (Yahoo->Sina)
        if market == "A-share":
            res = self.sina.get_stock_quote(symbol, market="A-share")
            if not self._is_error(res): return res
            res = self.akshare.get_stock_quote(symbol) 
            if not self._is_error(res): return res
            res = self.yahoo.get_stock_quote(symbol, market="A-share")
            if not self._is_error(res): return res
            
        elif market in ["US", "HK"]:
            res = self.yahoo.get_stock_quote(symbol, market=market)
            if not self._is_error(res): return res
            res = self.sina.get_stock_quote(symbol, market=market)
            if not self._is_error(res): return res

        return {"error": f"Could not fetch price for {symbol} in {market}"}

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get financial indicators."""
        market = self._detect_market(symbol)
        if market == "A-share": return self.akshare.get_financial_indicators(symbol)
        return self.yahoo.get_financial_indicators(symbol, market=market)
            
    def get_company_report(self, symbol: str) -> Dict[str, Any]:
        """Get the latest financial report metadata."""
        market = self._detect_market(symbol)
        return self.report_finder.get_latest_report(symbol, market=market)

    def get_report_content(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches the content of the latest financial report.
        Orchestrates fetching metadata and then extracting content.
        """
        try:
            # 1. Get metadata
            report_info = self.get_company_report(symbol)
            if report_info.get("error") or report_info.get("status") == "error":
                return report_info
            
            market = report_info.get("market")
            download_url = report_info.get("download_url")
            
            content, pdf_url, anchor_map = "", "", {}
            
            # 2. Extract content
            if market == 'US':
                # US Logic: Use Edgar tool to get Markdown/HTML
                try:
                    company = Company(symbol)
                    filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
                    if filings:
                         content = filings.markdown() or filings.text()
                         # Proxy HTML for frontend if possible
                         if filings.html():
                             html_content = filings.html()
                             # Handle SEC Index URL resolution if needed
                             real_url = filings.url
                             if "index.html" in real_url:
                                 real_url = self.report_content.extract_sec_report_url(real_url)
                             
                             _, local_url, html_anchor_map = self.report_content.save_html_content(html_content, symbol, real_url)
                             pdf_url = local_url
                             anchor_map = html_anchor_map
                         else:
                             pdf_url = filings.url
                except Exception as e:
                    logger.error(f"US content extraction failed: {e}")
                    
            elif download_url:
                if download_url.lower().endswith('.pdf'):
                    content, pdf_url, anchor_map = self.report_content.download_and_parse_pdf(download_url, symbol)
                else:
                    _, pdf_url, anchor_map = self.report_content.get_html_content(download_url, symbol)
                    # For HTML, we need the text too
                    # In get_html_content logic, it returns formatted text with anchors
                    content, _, _ = self.report_content.get_html_content(download_url, symbol)
                    
            if content:
                truncated = len(content) > 300000
                return {
                    "status": "success",
                    "symbol": symbol,
                    "market": market,
                    "content": content[:300000],
                    "content_truncated": truncated,
                    "report_info": report_info,
                    "pdf_url": pdf_url,
                    "anchor_map": anchor_map
                }
            
            return {"error": "No content extracted", "report_info": report_info}

        except Exception as e:
            logger.error(f"Error getting report content for {symbol}: {e}")
            return {"error": str(e)}

    def analyze_report(self, symbol: str) -> Dict[str, Any]:
        """
        Analyzes the financial report using LLM.
        """
        try:
            # 1. Get Content
            content_res = self.get_report_content(symbol)
            if content_res.get("error") or content_res.get("status") == "error":
                return {"error": content_res.get("error")}
            
            content = content_res.get("content", "")
            market = content_res.get("market", "Unknown")
            report_info = content_res.get("report_info", {})
            pdf_url = content_res.get("pdf_url", "")
            anchor_map = content_res.get("anchor_map", {})

            # 2. Analyze
            return self.report_analyst.analyze_content(
                content, symbol, market, report_info, pdf_url, anchor_map
            )

        except Exception as e:
             logger.error(f"Analysis failed: {e}")
             return {"error": str(e)}

    def get_macro_data(self, query: str) -> Dict[str, Any]:
        """Get macro economic data based on query."""
        query = query.lower()
        if "china" in query or "cn" in query:
            if "gdp" in query: return self.akshare.get_macro_data("gdp")
            if "cpi" in query: return self.akshare.get_macro_data("cpi")
            if "pmi" in query: return self.akshare.get_macro_data("pmi")
        if "vix" in query: return self.yahoo.get_macro_data("VIX")
        if "dxy" in query: return self.yahoo.get_macro_data("DXY")
        if "yield" in query or "us10y" in query: return self.yahoo.get_macro_data("US10Y")
        if "fed" in query: return self.yahoo.get_macro_data("FED_FUNDS_FUTURES")
        return {"error": "Unknown macro indicator requested"}

    def search_market_news(self, query: str, provider: str = "auto") -> List[Dict[str, Any]]:
        """Search for market news."""
        if provider == "auto":
            if self.tavily: provider = "tavily"
            elif self.serp: provider = "serp"
            else: provider = "ddg"

        if provider == "tavily" and self.tavily: return self.tavily.search(query, topic="news")
        if provider == "serp" and self.serp: return self.serp.search(query, topic="news")
        if provider == "ddg": return self.ddg.search(query, topic="news")
        return [{"title": "Search failed", "content": "Provider not available"}]

    def analyze_sentiment(self, text_or_items: Union[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze sentiment."""
        if isinstance(text_or_items, str): items = [{"title": text_or_items}]
        else: items = text_or_items
        return self.finbert.analyze(items)

    def parse_pdf(self, file_path: str) -> str:
        """Parse PDF to markdown."""
        result = self.pdf.parse(file_path)
        return result.get("content", "")

    # --- Helpers ---

    def _detect_market(self, symbol: str) -> str:
        """Detect market by symbol format."""
        if re.match(r'^(sh|sz)?(60|00|30)\d{4}$', symbol): return "A-share"
        if re.match(r'^\d{4,5}$', symbol) or symbol.endswith('.HK'): return "HK"
        return "US"

    def _is_error(self, response: Dict) -> bool:
        return "error" in response or response is None

if __name__ == "__main__":
    pass
