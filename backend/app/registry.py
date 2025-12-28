import logging
import re
from typing import Dict, Any, Optional, List, Union
from backend.infrastructure.config.loader import config

# Market Tools
from backend.infrastructure.market.akshare import AkShareTool
from backend.infrastructure.market.fred import FredTool
from backend.infrastructure.market.sina import SinaFinanceTool
from backend.infrastructure.market.yahoo import YahooFinanceTool
from backend.infrastructure.market.xueqiu import XueqiuTool
from backend.domain.services.technical_analysis import TechnicalAnalysisTool

# Search & Analysis
from backend.infrastructure.search.tavily import TavilyTool
from backend.infrastructure.search.serp import SerpAppTool
from backend.infrastructure.search.duckduckgo import DuckDuckGoTool
from backend.infrastructure.analysis.finbert import FinBERTTool

# from backend.infrastructure.utils.nlu import NLU # Removed, only function available

# Reports
from backend.infrastructure.document.pdf_parser import PDFParseTool
from backend.infrastructure.document.report_finder import ReportFinderTool
from backend.domain.entities.report_content import ReportContentTool
from backend.app.services.report_analysis import ReportAnalysisTool
from edgar import Company

logger = logging.getLogger(__name__)


class Tools:
    """
    Unified entry point for all financial tools.
    Handles routing, fallbacks, and parameter normalization.
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        serp_api_key: Optional[str] = None,
        llama_cloud_api_key: Optional[str] = None,
        fred_api_key: Optional[str] = None,
    ):
        # Load config automatically if keys not provided
        if not tavily_api_key:
            tavily_api_key = config.get_api_key("tavily")

        if not serp_api_key:
            serp_api_key = config.get_api_key("serpapi")

        if not llama_cloud_api_key:
            llama_cloud_api_key = config.get_api_key("llama_cloud")

        if not fred_api_key:
            fred_api_key = config.get_api_key("fred_api_key")

        # Initialize sub-tools
        self.sina = SinaFinanceTool()
        self.akshare = AkShareTool()
        self.yahoo = YahooFinanceTool()
        self.xueqiu = XueqiuTool()
        self.fred = FredTool(fred_api_key)
        self.technical = TechnicalAnalysisTool()
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

    def get_stock_price(
        self, symbol: str, market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get real-time stock price with automatic market detection and fallback.
        If market is provided ('A-share', 'US', 'HK'), auto-detection is skipped.
        """
        market = market or self._detect_market(symbol)

        # Strategy: A-share (Sina->AkShare->Yahoo), US/HK (Yahoo->Sina)
        if market == "A-share":
            res = self.sina.get_stock_quote(symbol, market="A-share")
            if not self._is_error(res):
                return res
            res = self.akshare.get_stock_quote(symbol)
            if not self._is_error(res):
                return res
            res = self.yahoo.get_stock_quote(symbol, market="A-share")
            if not self._is_error(res):
                return res

        elif market in ["US", "HK"]:
            res = self.yahoo.get_stock_quote(symbol, market=market)
            if not self._is_error(res):
                return res
            res = self.sina.get_stock_quote(symbol, market=market)
            if not self._is_error(res):
                return res

        return {"error": f"Could not fetch price for {symbol} in {market}"}

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get financial metrics as an array (revenue, net_income, etc. by date).
        This method returns metrics in the format expected by the frontend.
        For categorized indicators, use get_financial_indicators().
        """
        import yfinance as yf
        import pandas as pd

        market = self._detect_market(symbol)
        metrics = []
        currency = "USD"

        try:
            # Convert symbol for yfinance
            if market == "A-share":
                if symbol.startswith("6"):
                    yf_symbol = f"{symbol}.SS"
                else:
                    yf_symbol = f"{symbol}.SZ"
            elif market == "HK":
                yf_symbol = symbol if ".HK" in symbol else f"{symbol}.HK"
            else:
                yf_symbol = symbol

            # Get data from yfinance
            ticker = yf.Ticker(yf_symbol)
            financials = ticker.financials

            if not financials.empty:
                currency = (
                    ticker.info.get("currency", "USD")
                    if hasattr(ticker, "info")
                    else "USD"
                )
                financials_T = financials.T
                financials_T.sort_index(inplace=True)

                for date, row in financials_T.iterrows():
                    item = {
                        "date": date.strftime("%Y-%m-%d"),
                        "revenue": (
                            float(row.get("Total Revenue", 0))
                            if not pd.isna(row.get("Total Revenue", 0))
                            else 0
                        ),
                        "net_income": (
                            float(row.get("Net Income", 0))
                            if not pd.isna(row.get("Net Income", 0))
                            else 0
                        ),
                        "gross_profit": (
                            float(row.get("Gross Profit", 0))
                            if not pd.isna(row.get("Gross Profit", 0))
                            else 0
                        ),
                        "operating_income": (
                            float(row.get("Operating Income", 0))
                            if not pd.isna(row.get("Operating Income", 0))
                            else 0
                        ),
                    }
                    metrics.append(item)

            # HK fallback to AkShare if no data
            if not metrics and market == "HK":
                try:
                    import akshare as ak

                    code = symbol.replace(".HK", "").strip()
                    if len(code) == 4 and code.isdigit():
                        code = "0" + code

                    df = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
                    if not df.empty:
                        currency = "HKD"
                        df = df.head(5)

                        for _, row in df.iterrows():
                            r_date = pd.to_datetime(row["REPORT_DATE"])
                            item = {
                                "date": r_date.strftime("%Y-%m-%d"),
                                "revenue": (
                                    float(row["OPERATE_INCOME"])
                                    if not pd.isna(row["OPERATE_INCOME"])
                                    else 0
                                ),
                                "net_income": (
                                    float(row["HOLDER_PROFIT"])
                                    if not pd.isna(row["HOLDER_PROFIT"])
                                    else 0
                                ),
                                "gross_profit": 0,
                                "operating_income": 0,
                            }
                            metrics.append(item)
                except Exception as e:
                    logger.error(f"AkShare HK metrics fallback failed: {e}")

            if not metrics:
                return {
                    "status": "error",
                    "message": "No financial data found",
                    "market": market,
                    "symbol": symbol,
                }

            return {
                "status": "success",
                "symbol": symbol,
                "market": market,
                "currency": currency,
                "metrics": metrics,
            }

        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": market}

    def get_financial_indicators(self, symbol: str, years: int = 3) -> Dict[str, Any]:
        """
        Get financial indicators with fallback strategy.
        Strategy:
        - A-share: AkShare -> Yahoo (if AkShare returns empty/invalid data)
        - US/HK: Yahoo
        """
        market = self._detect_market(symbol)
        print("market:", market)
        print("symbol:", symbol)
        if market == "A-share":
            # 1. Try AkShare
            indicators = self.akshare.get_financial_indicators(symbol, years)

            # Check if data is valid (not empty)
            # Logic adapted from skills/financial_report_tool/modules/metrics.py
            is_valid = False
            if indicators and "error" not in indicators:
                # Check if we have actual data in key fields
                # We check if all main categories have valid data, or at least some.
                # A stricter check: if all categories are effectively empty, it's invalid.
                has_data = any(
                    indicators.get(cat, {}).get(key) not in [None, 0, 0.0]
                    for cat in ["revenue", "profit", "cashflow", "debt"]
                    for key in indicators.get(cat, {}).keys()
                )
                if has_data:
                    is_valid = True

            if is_valid:
                return indicators

            logger.warning(
                f"AkShare returned insufficient data for {symbol}, falling back to Yahoo"
            )

            # 2. Fallback to Yahoo
            return self.yahoo.get_financial_indicators(
                symbol, market="A-share", years=years
            )

        else:
            # US / HK -> Yahoo
            return self.yahoo.get_financial_indicators(
                symbol, market=market, years=years
            )

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
            if market == "US":
                # US Logic: Use sec_edgar_downloader (User Requested)
                try:
                    from sec_edgar_downloader import Downloader
                    import glob
                    import os
                    from bs4 import BeautifulSoup
                    import re

                    # 1. Download
                    dl_path = os.path.join(os.getcwd(), "backend", "data", "temp_sec")
                    dl = Downloader(
                        "StockTradingPlatform", "agent@example.com", dl_path
                    )

                    # Store count to check if new file arrived
                    # Store count to check if new file arrived
                    # Try 10-K first, then 10-Q if requested or if 10-K fails
                    doc_type = "10-K"
                    # If report_info suggests 10-Q (e.g. from title '10-Q Filing'), prefer that.
                    # Current logic fetches 10-K. Let's make it smarter.
                    if (
                        "10-Q" in report_info.get("title", "").upper()
                        or "QUARTERLY" in report_info.get("title", "").upper()
                    ):
                        doc_type = "10-Q"

                    try:
                        dl.get(doc_type, symbol, limit=1)
                    except Exception:
                        # Fallback to 10-K if 10-Q failed, or vice versa if needed, but for now simple fallback
                        if doc_type == "10-Q":
                            dl.get("10-K", symbol, limit=1)
                            doc_type = "10-K"

                    # 2. Find Latest File
                    # Path: .../sec-edgar-filings/{symbol}/{doc_type}/{accession}/full-submission.txt
                    search_path = os.path.join(
                        dl_path,
                        "sec-edgar-filings",
                        symbol,
                        "*",
                        "*",
                        "full-submission.txt",
                    )
                    files = glob.glob(search_path)

                    if files:
                        # Get latest downloaded
                        latest_file = max(files, key=os.path.getmtime)
                        logger.info(f"Processing SEC file: {latest_file}")

                        with open(
                            latest_file, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            raw_content = f.read()

                        # 3. Extract Main Document (10-K HTML)
                        # full-submission.txt is SGML. We want the first <DOCUMENT> that is 10-K or just the first HTML.
                        # 3. Extract Main Document
                        # Find ALL 10-K/10-Q documents and pick the largest one.
                        # This avoids getting a small cover page or summary.
                        doc_content = ""
                        matches = re.findall(
                            r"<TYPE>(?:10-K|10-Q).*?<TEXT>(.*?)</TEXT>",
                            raw_content,
                            re.DOTALL | re.IGNORECASE,
                        )

                        if matches:
                            # Pick the largest document text
                            doc_content = max(matches, key=len)
                        else:
                            # Fallback: Look for the first large HTML block
                            html_matches = re.findall(
                                r"<HTML>(.*?)</HTML>",
                                raw_content,
                                re.DOTALL | re.IGNORECASE,
                            )
                            if html_matches:
                                doc_content = max(html_matches, key=len)
                                doc_content = f"<HTML>{doc_content}</HTML>"

                        if not doc_content:
                            # Last resort: use the whole raw content if it looks like HTML
                            doc_content = raw_content
                        else:
                            # Fallback: Look for the first large HTML block
                            # Many modern filings are just XML/HTML.
                            # If we can't find the specific TYPE tag, try to find the first <HTML>...</HTML> block that is significant in size.
                            html_matches = re.findall(
                                r"<HTML>(.*?)</HTML>",
                                raw_content,
                                re.DOTALL | re.IGNORECASE,
                            )
                            if html_matches:
                                # Pick the largest one, usually the main report
                                doc_content = max(html_matches, key=len)
                                # Add back tags as findall removes them
                                doc_content = f"<HTML>{doc_content}</HTML>"

                        # Strip <XBRL> wrappers if present
                        doc_content = re.sub(
                            r"^\s*<XBRL>", "", doc_content, flags=re.IGNORECASE
                        ).strip()
                        doc_content = re.sub(
                            r"</XBRL>\s*$", "", doc_content, flags=re.IGNORECASE
                        ).strip()

                        # Save and Parse
                        # Use a fake URL since we downloaded it
                        fake_url = (
                            f"https://www.sec.gov/Archives/edgar/data/{symbol}/10-k.htm"
                        )
                        full_text_with_anchors, local_url, html_anchor_map = (
                            self.report_content.save_html_content(
                                doc_content, symbol, fake_url
                            )
                        )
                        pdf_url = local_url
                        anchor_map = html_anchor_map

                        # Use the text with anchors!
                        content = full_text_with_anchors

                    else:
                        logger.warning(
                            "sec_edgar_downloader finished but no file found."
                        )

                except Exception as e:
                    logger.error(f"sec_edgar_downloader failed: {e}")
                    # Fallback? No, this is the primary method now.

            elif download_url:
                if download_url.lower().endswith(".pdf"):
                    content, pdf_url, anchor_map = (
                        self.report_content.download_and_parse_pdf(download_url, symbol)
                    )
                else:
                    _, pdf_url, anchor_map = self.report_content.get_html_content(
                        download_url, symbol
                    )
                    # For HTML, we need the text too
                    # In get_html_content logic, it returns formatted text with anchors
                    content, _, _ = self.report_content.get_html_content(
                        download_url, symbol
                    )

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
                    "anchor_map": anchor_map,
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

    def extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text."""
        from backend.infrastructure.utils.nlu import extract_symbols

        return extract_symbols(text)

    def get_historical_data(
        self, symbol: str, period: str = "30d", interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """Get historical data with market routing."""
        market = self._detect_market(symbol)
        if market == "A-share":
            # Sina is preferred for A-share kline? Or AkShare?
            # Source api_server used MarketDataSkill which used Sina or AkShare.
            # SinaFinanceTool.get_historical_data works well for A-share.
            res = self.sina.get_historical_data(
                symbol, market="A-share", period=period, interval=interval
            )
            if res:
                return res
            return self.akshare.get_historical_data(symbol, period=period)

        elif market in ["US", "HK"]:
            return self.yahoo.get_historical_data(
                symbol, market=market, period=period, interval=interval
            )

        return []

    def get_technical_indicators(
        self, symbol: str, period: str = "60d"
    ) -> Dict[str, Any]:
        """Get summarized technical indicators (snapshot)."""
        history = self.get_historical_data(symbol, period=period)
        return self.technical.calculate_indicators(history)

    def get_technical_context(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Get advanced technical context for AI Agent."""
        history = self.get_historical_data(symbol, period=period)
        context = self.technical.calculate_advanced_indicators(history)
        if "error" in context:
            return context

        # Inject metadata
        context["symbol"] = symbol
        context["period"] = period
        return context

    def get_technical_history(
        self, symbol: str, period: str = "1y"
    ) -> List[Dict[str, Any]]:
        """Get historical data with calculated indicators (for charts)."""
        history = self.get_historical_data(symbol, period=period)
        return self.technical.calculate_indicators_history(history)

    def get_macro_history(self, query: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical macro data."""
        query = query.lower()
        if "china" in query or "cn" in query:
            if "gdp" in query:
                return self.akshare.get_macro_history("gdp")
            if "cpi" in query:
                return self.akshare.get_macro_history("cpi")
            if "pmi" in query:
                return self.akshare.get_macro_history("pmi")
            if "ppi" in query:
                return self.akshare.get_macro_history("ppi")
            if "m2" in query:
                return self.akshare.get_macro_history("m2")
            if "lpr" in query:
                return self.akshare.get_macro_history("lpr")

        # FRED macro Data
        if "unemployment" in query:
            return self.fred.get_macro_history("UNEMPLOYMENT", period)
        if "nonfarm" in query:
            return self.fred.get_macro_history("NONFARM_PAYROLLS", period)
        if "us cpi" in query or "cpi us" in query or "us_cpi" in query:
            return self.fred.get_macro_history("CPI", period)
        if "fed funds" in query or "fed_funds" in query:
            return self.fred.get_macro_history("FED_FUNDS", period)
        if "m2" in query and "us" in query:
            return self.fred.get_macro_history("M2", period)
        if "dxy" in query:
            return self.fred.get_macro_history(
                "DTWEXM", period
            )  # FRED Major Currencies
        if "dfedtaru" in query:
            return self.fred.get_macro_history("DFEDTARU", period)

        # Yahoo macro
        indicator = None
        if "vix" in query:
            indicator = "VIX"
        # elif "dxy" in query: indicator = "DXY"
        elif "yield" in query or "us10y" in query:
            indicator = "US10Y"
        elif "fed" in query and "future" in query:
            indicator = "FED_FUNDS_FUTURES"

        if indicator:
            return self.yahoo.get_macro_history(indicator, period)

        return {"error": "Unknown macro indicator requested"}

    def get_macro_data(self, query: str) -> Dict[str, Any]:
        """Get macro economic data based on query."""
        query = query.lower()
        if "china" in query or "cn" in query:
            if "gdp" in query:
                return self.akshare.get_macro_data("gdp")
            if "cpi" in query:
                return self.akshare.get_macro_data("cpi")
            if "pmi" in query:
                return self.akshare.get_macro_data("pmi")
            if "ppi" in query:
                return self.akshare.get_macro_data("ppi")
            if "m2" in query:
                return self.akshare.get_macro_data("m2")
            if "lpr" in query:
                return self.akshare.get_macro_data("lpr")
            if "social" in query:
                return self.akshare.get_macro_data("SOCIAL_FINANCING")

        if "vix" in query:
            return self.yahoo.get_macro_data("VIX")
        # if "dxy" in query: return self.yahoo.get_macro_data("DXY") # Yahoo DXY Unreliable, used FRED below
        if "yield" in query or "us10y" in query:
            return self.yahoo.get_macro_data("US10Y")
        if "fed" in query and "future" in query:
            return self.yahoo.get_macro_data("FED_FUNDS_FUTURES")

        # FRED Macro Data (Fallbacks for US Economy)
        if (
            "us" in query
            or "fed" in query
            or "unemployment" in query
            or "nonfarm" in query
            or "dxy" in query
        ):
            if "unemployment" in query:
                return self.fred.get_macro_history("UNEMPLOYMENT", "1y")
            if "nonfarm" in query:
                return self.fred.get_macro_history("NONFARM_PAYROLLS", "1y")
            if "cpi" in query:
                return self.fred.get_macro_history("CPI", "1y")
            if "fed" in query and "funds" in query:
                return self.fred.get_macro_history("FED_FUNDS", "1y")
            if "m2" in query:
                return self.fred.get_macro_history("M2", "1y")
            if "dxy" in query:
                return self.fred.get_macro_history("DTWEXM", "1y")
            if "dfedtaru" in query:
                return self.fred.get_macro_history("DFEDTARU", "1y")

        return {"error": "Unknown macro indicator requested"}

    def search_market_news(
        self,
        query: str,
        provider: str = "auto",
        topic: str = "news",
        include_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for market news."""
        if provider == "auto":
            if self.tavily:
                provider = "tavily"
            elif self.serp:
                provider = "serp"
            else:
                provider = "ddg"

        if provider == "tavily" and self.tavily:
            return self.tavily.search(
                query, topic=topic, include_domains=include_domains
            )
        if provider == "serp" and self.serp:
            return self.serp.search(query, topic="news")
        if provider == "ddg":
            return self.ddg.search(query, topic="news")
        return [{"title": "Search failed", "content": "Provider not available"}]

    def analyze_sentiment(
        self, text_or_items: Union[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Analyze sentiment."""
        if isinstance(text_or_items, str):
            items = [{"title": text_or_items}]
        else:
            items = text_or_items
        return self.finbert.analyze(items)

    def parse_pdf(self, file_path: str) -> str:
        """Parse PDF to markdown."""
        result = self.pdf.parse(file_path)
        return result.get("content", "")

    def get_discussion_wordcloud(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get word cloud data and sentiment summary from social media (Xueqiu).
        """
        return self.xueqiu.get_wordcloud_data(
            query, limit=limit, finbert_tool=self.finbert, search_tool=self.tavily
        )

    # --- Helpers ---

    def _detect_market(self, symbol: str) -> str:
        """Detect market by symbol format."""
        if re.match(r"^(sh|sz)?(60|00|30)\d{4}$", symbol):
            return "A-share"
        if re.match(r"^\d{4,5}$", symbol) or symbol.endswith(".HK"):
            return "HK"
        return "US"

    def _is_error(self, response: Dict) -> bool:
        return "error" in response or response is None


if __name__ == "__main__":
    pass
