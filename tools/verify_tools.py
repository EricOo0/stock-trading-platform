
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.market.sina import SinaFinanceTool
from tools.market.akshare import AkShareTool
from tools.market.yahoo import YahooFinanceTool
from tools.search.tavily import TavilyTool
from tools.analysis.finbert import FinBERTTool
from tools.reports.pdf_parse import PDFParseTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def verify_sina():
    logger.info("--- Verifying SinaFinanceTool ---")
    try:
        tool = SinaFinanceTool()
        quote = tool.get_stock_quote("sh600519", market="A-share") 
        logger.info(f"Quote (Moutai): {quote.get('name')} Price: {quote.get('current_price')}")
        
        hist = tool.get_historical_data("sh600519", market="A-share", period="5d", interval="60m")
        logger.info(f"History (Moutai) len: {len(hist)}")
        
        return True
    except Exception as e:
        logger.error(f"Sina verification failed: {e}")
        return False

def verify_akshare():
    logger.info("--- Verifying AkShareTool ---")
    try:
        tool = AkShareTool()
        # Use a stable symbol, e.g., 600519 (Moutai in A-share code for AkShare might differ, usually just '600519')
        quote = tool.get_stock_quote("600519") 
        logger.info(f"Quote (Moutai): {quote.get('name')} Price: {quote.get('current_price')}")
        logger.info(f"Quote (Moutai): {quote}")
        # Macro
        macro = tool.get_macro_data("gdp")
        logger.info(f"Macro (GDP): {macro.get('value')} {macro.get('unit')}")
        logger.info(f"Macro (GDP): {macro}")

        return True
    except Exception as e:
        logger.error(f"AkShare verification failed: {e}")
        return False

def verify_yahoo():
    logger.info("--- Verifying YahooFinanceTool ---")
    try:
        tool = YahooFinanceTool(enable_rotation=False) # Simple verification
        quote = tool.get_stock_quote("AAPL", market="US")
        logger.info(f"Quote (AAPL): {quote.get('current_price')}")
        
        macro = tool.get_macro_data("VIX")
        logger.info(f"Macro (VIX): {macro.get('value')}")
        return True
    except Exception as e:
        logger.error(f"Yahoo verification failed: {e}")
        return False

def verify_tavily():
    logger.info("--- Verifying TavilyTool ---")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.warning("Skipping Tavily verification: TAVILY_API_KEY not set")
        return True
    
    try:
        tool = TavilyTool(api_key)
        results = tool.search("AAPL stock")
        logger.info(f"Search results: {len(results)}")
        return True
    except Exception as e:
        logger.error(f"Tavily verification failed: {e}")
        return False

def verify_finbert():
    logger.info("--- Verifying FinBERTTool ---")
    try:
        # This might be slow if downloading model, but we want to know if it works
        tool = FinBERTTool()
        result = tool.analyze([{"title": "Markets rally on good news", "summary": "Investors are happy."}])
        logger.info(f"Analysis result: {result.get('rating')} ({result.get('method')})")
        return True
    except Exception as e:
        logger.error(f"FinBERT verification failed: {e}")
        return False

def verify_pdf():
    logger.info("--- Verifying PDFParseTool ---")
    # Just check instantiation and method signature exists, don't parse real file to save API/time
    try:
        tool = PDFParseTool()
        logger.info("PDFParseTool instantiated successfully")
        return True
    except Exception as e:
        logger.error(f"PDF verification failed: {e}")
        return False

if __name__ == "__main__":
    results = {
        "Sina": verify_sina(),
        "AkShare": verify_akshare(),
        "Yahoo": verify_yahoo(),
        "Tavily": verify_tavily(),
        "FinBERT": verify_finbert(),
        "PDF": verify_pdf()
    }
    
    logger.info("--- Verification Summary ---")
    failed = False
    for k, v in results.items():
        status = "PASS" if v else "FAIL"
        logger.info(f"{k}: {status}")
        if not v: failed = True
        
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)
