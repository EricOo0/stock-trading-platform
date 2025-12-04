import os
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from edgar import set_identity, Company
from langchain_openai import ChatOpenAI

# Import sub-skills
from .modules.market import detect_market
from .modules.metrics import get_financial_metrics, fetch_financial_data_as_text
from .modules.report_finder import get_latest_report_metadata
from .modules.content_extractor import (
    download_and_parse_pdf, 
    get_html_content, 
    save_html_content, 
    extract_sec_report_url
)
from .modules.analyst import analyze_report_content

class FinancialReportSkill:
    def __init__(self):
        self.name = "financial_report_tool"
        self.description = "Fetches financial report data and documents for companies."
        # Initialize Edgar (identity is required by SEC)
        try:
            set_identity("StockAnalysisAgent <agent@example.com>")
        except Exception as e:
            logger.warning(f"Failed to set edgar identity: {e}")

        # Try to load config from agent/config.yaml
        try:
            # Ensure project root is in path to import agent
            import sys
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            if project_root not in sys.path:
                sys.path.append(project_root)
                
            from agent.core.config import get_config
            config = get_config()
            llm_config = config.llm
            
            # Use config values, falling back to defaults or env vars if necessary
            api_key = llm_config.api_key or os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
            api_base = llm_config.api_base or "https://api.siliconflow.cn/v1"
            model = llm_config.model or "deepseek-ai/DeepSeek-V3.1-Terminus"
            temperature = llm_config.temperature
            
        except Exception as e:
            logger.warning(f"Could not load agent configuration: {e}. Falling back to environment variables.")
            api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
            api_base = "https://api.siliconflow.cn/v1"
            model = "deepseek-ai/DeepSeek-V3.1-Terminus"
            temperature = 0

        if not api_key:
            logger.warning("No API key found for SiliconFlow/OpenAI. Please set SILICONFLOW_API_KEY or OPENAI_API_KEY.")
            
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            base_url=api_base,
            api_key=api_key
        )

    def detect_market(self, symbol: str) -> Tuple[str, str]:
        """
        Detect which market the stock belongs to based on symbol format.
        Delegates to market module.
        """
        return detect_market(symbol)

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches key financial metrics.
        Delegates to metrics module.
        """
        return get_financial_metrics(symbol)

    def get_latest_report(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches metadata about the latest financial report.
        Delegates to report_finder module.
        """
        return get_latest_report_metadata(symbol)

    def get_report_content(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches the content of the latest financial report.
        Returns text content directly or parses PDF if necessary.
        Orchestrates fetching and parsing using sub-skills.
        """
        try:
            # 1. Get report metadata
            report_info = self.get_latest_report(symbol)
            if report_info.get("status") != "success":
                return report_info
            
            market = report_info.get("market")
            download_url = report_info.get("download_url")
            content = ""
            pdf_url = "" # Can be PDF or HTML proxy URL
            anchor_map = {} # Map of anchor_id -> metadata (coords/DOM id)
            
            # 2. Fetch content based on market/type
            if market == 'US':
                # Re-fetch filing object to get content
                try:
                    company = Company(symbol)
                    filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
                    if filings:
                        # Try markdown first (better structure), then text
                        try:
                            content = filings.markdown()
                        except:
                            content = filings.text()
                        
                        # For US stocks, handle URL extraction and proxying
                        # Try to get HTML content directly from edgartools first
                        html_content = None
                        try:
                            html_content = filings.html()
                        except Exception as e:
                            logger.warning(f"Could not get HTML from edgartools: {e}")

                        if html_content:
                             # If we have the HTML, save it directly
                             logger.info(f"Got HTML content from edgartools for {symbol}")
                             
                             # Fix: filings.url is often the index page (e.g. ...-index.html), 
                             # but the content is the actual report in a subdirectory.
                             # We need to resolve the correct URL to set the correct <base> tag.
                             real_url = filings.url
                             if "index.html" in real_url or "index.htm" in real_url:
                                 try:
                                     resolved = extract_sec_report_url(real_url)
                                     if resolved != real_url:
                                         real_url = resolved
                                         logger.info(f"Resolved real report URL: {real_url}")
                                 except Exception as e:
                                     logger.warning(f"Failed to resolve real URL from index: {e}")

                             full_text, local_url, html_anchor_map = save_html_content(html_content, symbol, real_url)
                             pdf_url = local_url
                             # Use the full text with anchors for analysis
                             content = full_text
                             # Merge anchor maps if needed, but for now just use the one from HTML
                             anchor_map = html_anchor_map
                        elif hasattr(filings, 'url'):
                             original_url = filings.url
                             logger.info(f"Processing US report URL: {original_url}")
                             
                             # 1. Check if it's an index page and extract actual report URL
                             target_url = original_url
                             if "index.html" in original_url:
                                 target_url = extract_sec_report_url(original_url)
                                 logger.info(f"Extracted SEC target URL: {target_url}")
                             
                             # 2. Download and save content locally (proxy)
                             # US SEC reports often block iframe via X-Frame-Options, so we must proxy
                             if target_url:
                                 full_text, local_url, html_anchor_map = get_html_content(target_url, symbol)
                                 if local_url:
                                     pdf_url = local_url
                                     anchor_map = html_anchor_map
                                     content = full_text
                                     logger.info(f"Proxied US report to: {pdf_url}")
                                 else:
                                     # Fallback to original if proxy fails (though likely to be blocked)
                                     pdf_url = target_url
                             else:
                                 pdf_url = original_url
                                 
                except Exception as e:
                    logger.error(f"Error extracting US report content: {e}")
                    return {"status": "error", "message": f"Failed to extract US report content: {e}"}

            elif download_url:
                if download_url.lower().endswith('.pdf'):
                    # PDF URL
                    logger.info(f"Downloading and parsing PDF from {download_url}")
                    content, local_url, anchor_map = download_and_parse_pdf(download_url, symbol)
                    pdf_url = local_url
                else:
                    # HTML URL (e.g. HK/A-Share announcement page)
                    logger.info(f"Fetching HTML content from {download_url}")
                    content, local_url, anchor_map = get_html_content(download_url, symbol)
                    if local_url:
                        pdf_url = local_url # Point to our local proxy
            
            elif market == 'A-SHARE':
                 # Should have been caught by download_url check, but just in case
                 pass

            else:
                # Fallback: Use yfinance data as content for analysis
                logger.info(f"Fetching structured financial data from yfinance as fallback content for {symbol}")
                content = fetch_financial_data_as_text(symbol, market)
                if not content:
                    return {
                        "status": "partial",
                        "message": "Content extraction not supported and financial data unavailable",
                        "report_info": report_info
                    }
            
            if content:
                truncated = len(content) > 300000
                return {
                    "status": "success",
                    "symbol": report_info.get("symbol", symbol),
                    "market": market,
                    "content": content[:300000],
                    "content_truncated": truncated,
                    "report_info": report_info,
                    "pdf_url": pdf_url, # Return the URL for frontend display
                    "anchor_map": anchor_map # Return anchor mapping
                }
            else:
                 return {
                    "status": "error",
                    "message": "No content extracted",
                    "report_info": report_info,
                    "symbol": report_info.get("symbol", symbol)
                }

        except Exception as e:
            logger.error(f"Error getting report content for {symbol}: {e}")
            return {"status": "error", "message": str(e), "symbol": symbol}

    def analyze_report(self, symbol: str) -> Dict[str, Any]:
        """
        Analyzes the financial report using LLM.
        Returns a markdown report.
        """
        try:
            # 1. Get Content
            content_res = self.get_report_content(symbol)
            if content_res.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to fetch report content: {content_res.get('message')}",
                    "symbol": symbol
                }
            
            content = content_res.get("content", "")
            market = content_res.get("market", "Unknown")
            real_symbol = content_res.get("symbol", symbol)
            report_info = content_res.get("report_info", {})
            
            # Use the pdf_url from content_res if available
            pdf_url = content_res.get("pdf_url")
            anchor_map = content_res.get("anchor_map", {})

            # 2. Delegate to analyst module
            return analyze_report_content(
                llm=self.llm,
                content=content,
                symbol=real_symbol,
                market=market,
                report_info=report_info,
                pdf_url=pdf_url,
                anchor_map=anchor_map
            )

        except Exception as e:
            logger.error(f"Error analyzing report for {symbol}: {e}")
            return {"status": "error", "message": str(e), "symbol": symbol}

if __name__ == "__main__":
    # Test
    skill = FinancialReportSkill()
    
    # Test US stock
    print("=== US Stock (AAPL) ===")
    # print(skill.get_financial_metrics("AAPL"))
    # print(skill.get_latest_report("AAPL"))
    
    # Test HK stock
    print("\n=== HK Stock (0700.HK) ===")
    # print(skill.get_financial_metrics("0700.HK"))
    # print(skill.get_latest_report("0700.HK"))
    
    # Test A-share
    print("\n=== A-Share (600036.SS) ===")
    # print(skill.get_financial_metrics("600036.SS"))
    # print(skill.get_latest_report("600036.SS"))
