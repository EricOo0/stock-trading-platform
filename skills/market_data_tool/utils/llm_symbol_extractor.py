"""
LLM-based stock symbol extractor
Uses LLM to intelligently extract stock symbols from natural language queries
"""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json

class StockSymbolExtraction(BaseModel):
    """Extracted stock symbols with metadata"""
    symbols: List[str] = Field(description="List of stock symbols (e.g., ['NVDA', '000001', '00700'])")
    companies: List[str] = Field(description="List of company names mentioned")
    markets: List[str] = Field(description="List of markets (US, A-share, HK)")

class LLMSymbolExtractor:
    """
    Uses LLM to extract stock symbols from natural language queries
    Supports Chinese/English company names and fuzzy matching
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a stock market expert. Extract stock symbols from user queries.

Rules:
1. For US stocks: Use standard ticker symbols (e.g., AAPL, NVDA, TSLA)
2. For A-share stocks: Use 6-digit codes (e.g., 000001, 600519)
3. For HK stocks: Use 5-digit codes with leading zeros (e.g., 00700, 09988)
4. Support both English and Chinese company names
5. If a company name is mentioned but you're not sure of the exact symbol, make your best guess based on common knowledge
6. Return empty lists if no stock symbols can be extracted

Common mappings:
- NVIDIA / 英伟达 → NVDA
- Apple / 苹果 → AAPL
- Tesla / 特斯拉 → TSLA
- Microsoft / 微软 → MSFT
- Tencent / 腾讯 → 00700 (HK) or 0700
- Alibaba / 阿里巴巴 → BABA (US) or 9988 (HK)
- Ping An Bank / 平安银行 → 000001 (A-share)
- Kweichow Moutai / 贵州茅台 → 600519 (A-share)

Return JSON format:
{{
  "symbols": ["NVDA", "AAPL"],
  "companies": ["NVIDIA", "Apple"],
  "markets": ["US", "US"]
}}"""),
            ("human", "{query}")
        ])
    
    def extract(self, query: str) -> List[str]:
        """
        Extract stock symbols from natural language query
        
        Args:
            query: Natural language query (e.g., "What's the price of NVIDIA?")
            
        Returns:
            List of stock symbols
        """
        try:
            # Create chain with structured output
            chain = self.prompt | self.llm
            
            # Invoke LLM
            response = chain.invoke({"query": query})
            content = response.content
            
            # Parse JSON response
            try:
                data = json.loads(content)
                symbols = data.get("symbols", [])
                
                # Normalize and validate symbols
                normalized = []
                # Common false positives to filter out
                invalid_symbols = {'US', 'STOCK', 'PRICE', 'MARKET', 'DATA', 'QUERY', 'GET', 'FIND', 'SEARCH'}
                
                for symbol in symbols:
                    symbol = symbol.strip().upper()
                    
                    # Skip invalid symbols
                    if symbol in invalid_symbols:
                        continue
                    
                    # Skip if it's just a number (not a valid symbol)
                    if symbol.isdigit() and len(symbol) < 4:
                        continue
                    
                    # Ensure HK stocks have 5 digits
                    if symbol.isdigit() and len(symbol) == 4:
                        symbol = symbol.zfill(5)
                    
                    normalized.append(symbol)
                
                return normalized
            except json.JSONDecodeError:
                # Fallback: try to extract symbols from text
                import re
                # Extract potential symbols
                us_symbols = re.findall(r'\b([A-Z]{2,5})\b', content)
                a_share_symbols = re.findall(r'\b(\d{6})\b', content)
                hk_symbols = re.findall(r'\b(0\d{4})\b', content)
                
                # Filter out invalid symbols
                invalid_symbols = {'US', 'STOCK', 'PRICE', 'MARKET', 'DATA', 'QUERY', 'GET', 'FIND', 'SEARCH'}
                us_symbols = [s for s in us_symbols if s not in invalid_symbols]
                
                return us_symbols + a_share_symbols + hk_symbols
                
        except Exception as e:
            # Fallback to regex-based extraction
            import re
            symbols = []
            
            # Extract US symbols
            us_matches = re.findall(r'\b([A-Z]{2,5})\b', query.upper())
            # Filter out common false positives
            invalid_symbols = {'US', 'STOCK', 'PRICE', 'MARKET', 'DATA', 'QUERY', 'GET', 'FIND', 'SEARCH', 'THE', 'AND', 'FOR'}
            us_matches = [s for s in us_matches if s not in invalid_symbols]
            symbols.extend(us_matches)
            
            # Extract A-share codes
            a_share_matches = re.findall(r'\b(\d{6})\b', query)
            symbols.extend(a_share_matches)
            
            # Extract HK codes
            hk_matches = re.findall(r'\b(0\d{4})\b', query)
            symbols.extend(hk_matches)
            
            return symbols[:5]  # Limit to 5 symbols
