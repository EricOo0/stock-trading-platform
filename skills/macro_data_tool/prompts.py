"""Prompts for the Macro Data Skill."""

MACRO_DATA_TOOL_DESCRIPTION = """
Useful for getting macroeconomic data and market indicators.
You can query:
1. US Economic Data (from FRED): CPI, GDP, Non-Farm Payrolls, Unemployment Rate, Fed Funds Rate.
2. Market Indicators (from Yahoo): VIX (Fear Index), US 10Y Treasury Yield, Dollar Index, Fed Rate Probabilities.
3. China Economic Data (from AkShare): GDP, CPI, PMI.

Input should be a specific question or request about these indicators.
Examples:
- "What is the latest US CPI?"
- "Show me the fear index (VIX)"
- "How is China's GDP growth?"
- "What is the probability of a rate cut?"
"""

MACRO_ANALYSIS_PROMPT = """
You are a macroeconomic analyst. Analyze the following data and explain its impact on the stock market.
Data: {data}

Focus on:
1. What the data means (Good/Bad/Neutral).
2. How it typically affects the stock market (e.g., High inflation -> Rate hike fears -> Stocks down).
3. Any specific trends visible in the data.

Keep the analysis concise and actionable for an investor.
"""
