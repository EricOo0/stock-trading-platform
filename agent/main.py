"""Main FastAPI application entry point for the Stock Analysis Agent."""

import sys
from pathlib import Path

# Add agent directory to path for absolute imports
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))
# Add project root to path for cross-module imports (e.g. skills)
sys.path.insert(0, str(agent_dir.parent))

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from loguru import logger

from api.routes import router
from api.middleware import setup_middleware
from utils.logging import setup_logging
from core.config import get_config

# Initialize logging
setup_logging(verbose=True)

# Create FastAPI app
app = FastAPI(
    title="Stock Analysis Agent API",
    description="LangChain-based ReAct agent for stock market analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting Stock Analysis Agent API...")
    try:
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"LLM Model: {config.llm.model}")
        logger.info(f"Skills enabled: {config.skills.enabled}")
        logger.info(f"Agent max iterations: {config.agent.max_iterations}")
        
        # Initialize A2A
        from api.a2a import setup_a2a
        
        # Pass config to setup_a2a
        setup_a2a(app, config)
        
    except Exception as e:
        logger.error(f"Failed to load configuration or setup A2A: {e}")
        logger.warning("Using default configuration")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down Stock Analysis Agent API...")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/api/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}


if __name__ == "__main__":
    import uvicorn
    
    # Get server config
    try:
        config = get_config()
        host = config.server.host
        port = config.server.port
        reload = config.server.reload
    except:
        host = "0.0.0.0"
        port = 8001
        reload = True
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload
    )
