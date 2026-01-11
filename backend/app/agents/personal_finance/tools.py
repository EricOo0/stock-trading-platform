import json
import logging
import asyncio
from typing import Optional

from backend.app.agents.personal_finance.sub_agents import (
    MacroAnalyst,
    MarketAnalyst,
    NewsAnalyst,
    TechnicalAnalyst,
    DailyReviewAnalyst
)

logger = logging.getLogger(__name__)

async def run_macro_analysis(session_id: str = "default") -> str:
    """
    Runs the Macro Analyst (independent sub-agent) and returns the analysis.
    """
    logger.info("Starting Macro Analysis Sub-task...")
    try:
        analyst = MacroAnalyst()
        result = await analyst.analyze()
        return result
    except Exception as e:
        logger.error(f"Failed to run macro analysis: {e}")
        return f"Error running macro analysis: {str(e)}"

async def run_market_analysis() -> str:
    """
    Runs the Market Analyst (independent sub-agent) and returns the analysis.
    """
    logger.info("Starting Market Analysis Sub-task...")
    try:
        analyst = MarketAnalyst()
        result = await analyst.analyze()
        return result
    except Exception as e:
        logger.error(f"Failed to run market analysis: {e}")
        return f"Error running market analysis: {str(e)}"

async def run_technical_analysis(symbol: str, session_id: str = "default") -> str:
    """
    Runs the Technical Analyst (independent sub-agent) for a specific symbol.
    """
    logger.info(f"Starting Technical Analysis Sub-task for {symbol}...")
    try:
        analyst = TechnicalAnalyst()
        result = await analyst.analyze(symbol)
        return result
    except Exception as e:
        logger.error(f"Failed to run technical analysis for {symbol}: {e}")
        return f"Error running technical analysis for {symbol}: {str(e)}"

async def run_news_analysis(query: str, session_id: str = "default") -> str:
    """
    Runs the News Analyst (independent sub-agent) for a specific query.
    """
    logger.info(f"Starting News Analysis Sub-task for query: {query}...")
    try:
        analyst = NewsAnalyst()
        result = await analyst.analyze(query)
        return result
    except Exception as e:
        logger.error(f"Failed to run news analysis: {e}")
        return f"Error running news analysis: {str(e)}"

async def run_daily_review_analysis(symbol: str, session_id: str = "default") -> str:
    """
    Runs the Daily Review Analyst (independent sub-agent) for a specific symbol.
    """
    logger.info(f"Starting Daily Review Analysis Sub-task for {symbol}...")
    try:
        analyst = DailyReviewAnalyst()
        result = await analyst.analyze(symbol)
        return result
    except Exception as e:
        logger.error(f"Failed to run daily review analysis for {symbol}: {e}")
        return f"Error running daily review analysis for {symbol}: {str(e)}"

