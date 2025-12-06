# Financial Tools Library

This## Directory Structure

```
tools/
├── market/             # Market Data
│   ├── sina.py         # Sina Finance (A-share/HK/US)
│   ├── akshare.py      # AkShare (A-share/Macro)
│   └── yahoo.py        # Yahoo Finance (Global)
├── search/             # Web Search
│   ├── tavily.py       # Tavily API
│   ├── serp.py         # SerpApi (Google)
│   └── duckduckgo.py   # DuckDuckGo (No API)
├── reports/            # Financial Reports
│   ├── finder.py       # Report Metadata Fetcher (SEC/Cninfo/HKEX)
│   ├── content.py      # Content Extractor (HTML/PDF)
│   ├── analysis.py     # LLM Analysis
│   └── pdf_parse.py    # PDF Parser (LlamaParse/PyMuPDF)
├── analysis/           # Analysis Tools
│   └── finbert.py      # Sentiment Analysis (FinBERT)
├── registry.py         # Central Registry (Entry Point)
└── config.py           # Configuration Loader
```

## Data Sources

*   **Stock Quotes**: Sina Finance (Real-time), Yahoo Finance (Backup), AkShare (A-share).
*   **Financials**: AkShare (A-share), Yahoo Finance (Global).
*   **News**: Sina Finance (Scraper), Tavily/Google/DuckDuckGo (Search).
*   **Reports**: SEC EDGAR (US), Cninfo (A-share), HKEX (HK).
*   **Macro**: AkShare (China Data), Yahoo Finance (Global Indicators).
y`: Fast real-time quotes for A-shares; News scraping from Sina.
*   **`akshare_data.py` (`AkShareTool`)**:
    *   **Markets**: A-share (CN).
    *   **Features**: Real-time quotes, financial indicators (revenue, profit, etc.), China macro data (GDP, CPI).
    *   **Specialty**: Comprehensive A-share data and Chinese macro indicators.
*   **`yahoo_finance.py` (`YahooFinanceTool`)**:
    *   **Markets**: US, HK, A-share.
    *   **Features**: Real-time quotes, historical data, financial statements, Global macro data (VIX, DXY, US10Y).
    *   **Specialty**: Global market coverage.

### 2. Information Retrieval
*   **`tavily_search.py` (`TavilyTool`)**:
    *   **Features**: Web search optimized for AI agents.
    *   **Methods**: `search(query, topic='general'|'news')`.
*   **`pdf_parse.py` (`PDFParseTool`)**:
    *   **Features**: Parses PDF documents into markdown.
    *   **Methods**: `parse(file_path)`. Uses LlamaParse with PyMuPDF fallback.

### 3. Analysis
*   **`finbert.py` (`FinBERTTool`)**:
    *   **Features**: Financial sentiment analysis using `ProsusAI/finbert`.
    *   **Methods**: `analyze(news_items)`. Returns sentiment score (0-100), rating (Bullish/Bearish), and key drivers.

## Usage

```python
from tools.registry import Tools
# or
# from tools import Tools

# Initialize Tools
tools = Tools()

# Get A-share Quote
quote = tools.get_stock_price("sh600519")

# Get Macro Data
gdp = tools.get_macro_data("gdp")
```

## Setup
Ensure all dependencies are installed and the `Tavily` API key is set in your environment if using search.
