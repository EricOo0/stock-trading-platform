"""Logging configuration for the Stock Analysis Agent."""

import sys
from loguru import logger
from pathlib import Path


def setup_logging(verbose: bool = True, log_file: str = "agent.log") -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO
        log_file: Path to log file
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / log_file,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    # Separate logs for each agent
    agents = ["Chairman", "MarketDataInvestigator", "MacroDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator", "Receptionist", "Critic"]
    for agent in agents:
        logger.add(
            log_dir / f"{agent}.log",
            filter=lambda record, a=agent: a in record["message"] or a in record["extra"].get("agent_name", ""),
            rotation="5 MB",
            retention="3 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        )
    
    logger.info("Logging configured successfully")


# Create a logger instance for the agent
agent_logger = logger.bind(name="agent")
