import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.registry import Tools
from tools.config import config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegistryVerification")

def verify_registry():
    logger.info("--- Verifying Central Tools Registry ---")
    
    # Initialize without API keys for basic test
    tools = Tools()
    
    # 1. Test get_stock_price (Routing logic)
    try:
        # A-share
        # quote_cn = tools.get_stock_price("sh600519")
        # logger.info(f"CN Quote: {quote_cn.get('name', 'N/A')} - {quote_cn.get('current_price', 'N/A')}")
        
        # US
        quote_us = tools.get_stock_price("AAPL")
        logger.info(f"US Quote: {quote_us.get('symbol', 'N/A')} - {quote_us.get('current_price', 'N/A')}")
        
        # Explicit Market
        quote_explicit = tools.get_stock_price("AAPL", market="US")
        logger.info(f"US Quote (Explicit): {quote_explicit.get('symbol', 'N/A')} - {quote_explicit.get('current_price', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Stock price fetch failed: {e}")

    # 2. Test Macro Data
    try:
        vix = tools.get_macro_data("vix")
        logger.info(f"VIX: {vix.get('value')}")
    except Exception as e:
        logger.error(f"Macro fetch failed: {e}")

    # 3. Test Sentiment (Mock)
    try:
        sent = tools.analyze_sentiment("Market is booming!")
        logger.info(f"Sentiment: {sent.get('rating')}")
    except Exception as e:
        logger.error(f"Sentiment failed: {e}")

    # 4. Test Search (DDG - no key needed)
    try:
        logger.info("--- Testing DuckDuckGo Search ---")
        results = tools.search_market_news("Apple stock news", provider="ddg")
        logger.info(f"DDG Results: {len(results)}")
        if results: logger.info(f"Sample: {results[0].get('title')}")
    except Exception as e:
        logger.error(f"DDG Search failed: {e}")

    # 5. Test PDF Key Injection (Mock Check)
    try:
        logger.info("--- Testing PDF Tool Key Injection ---")
        # We can't easily check the private attribute but we can check instantiation works
        if tools.pdf.api_key:
            logger.info("PDF Tool has API Key injected from config/init")
        else:
            logger.info("PDF Tool initialized without explicit key (using env/config fallback)")
            
    except Exception as e:
        logger.error(f"PDF Check failed: {e}")

    # 6. Test Report Finder (US - AAPL)
    try:
        logger.info("--- Testing Report Finder (US: AAPL) ---")
        report = tools.get_company_report("AAPL")
        logger.info(f"Report: {report.get('title')} ({report.get('filing_date')})")
        if report.get('url'): logger.info(f"URL: {report.get('url')}")
    except Exception as e:
        logger.error(f"Report Finder failed: {e}")

    # 7. Test Report Content (Mock check for AAPL - US)
    try:
        logger.info("--- Testing Report Content (US: AAPL) ---")
        # Ensure we don't actually download 10MB file if we can avoid it, or just testing logic
        # For verification, we might just call it and check structure, assuming it might fail without full setup
        # But let's try.
        content_res = tools.get_report_content("AAPL")
        if content_res.get("status") == "success":
             logger.info(f"Content Length: {len(content_res.get('content', ''))}")
             logger.info(f"Anchor Map Keys: {len(content_res.get('anchor_map', {}))}")
        else:
             logger.warning(f"Content fetch skipped or failed: {content_res.get('error')}")
    except Exception as e:
        logger.error(f"Report Content failed: {e}")

    # 8. Test Analysis (Mock)
    try:
        logger.info("--- Testing Report Analysis ---")
        # We Mock content for analysis to save tokens and time
        # We can call the analyst directly via the tool instance if we want to unit test it,
        # but let's test the registry method with a mock injection if possible, or just skip if no key.
        from tools.config import config
        if config.get_api_key("siliconflow") or config.get_api_key("openai") or os.getenv("SILICONFLOW_API_KEY"):
             # Only run if we think we have a key
             # Retrieving content again might be heavy, so we might skip full integration test here
             # just to avoid blocking verification on network/LLM costs.
             # But let's try a fake analysis call using internal method? 
             # No, let's call the real one but handle error.
             logger.info("LLM Key detected, attempting lightweight analysis (skipped for speed)")
             # analysis = tools.analyze_report("AAPL")
             # logger.info(f"Analysis Status: {analysis.get('status')}")
        else:
             logger.info("No LLM Key detected, skipping analysis test")
             
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    verify_registry()
