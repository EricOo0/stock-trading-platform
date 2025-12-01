from fastapi import FastAPI
from loguru import logger
from core.config import Config

# Import setup functions from individual agents
from core.agents.receptionist import setup_a2a as setup_receptionist
from core.agents.macro import setup_a2a as setup_macro
from core.agents.market import setup_a2a as setup_market
from core.agents.sentiment import setup_a2a as setup_sentiment
from core.agents.web_search import setup_a2a as setup_web_search
from core.agents.chairman import setup_a2a as setup_chairman
from core.agents.critic import setup_a2a as setup_critic

def setup_a2a(app: FastAPI, config: Config):
    """Initialize all A2A agents by calling their individual setup functions."""
    try:
        setup_receptionist(app, config)
        setup_macro(app, config)
        setup_market(app, config)
        setup_sentiment(app, config)
        setup_web_search(app, config)
        setup_chairman(app, config)
        setup_critic(app, config)
        
        logger.info("All A2A agents initialized and mounted successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup A2A: {e}")
