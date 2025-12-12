import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.infrastructure.config.loader import config
from backend.infrastructure.logging.setup import setup_logging
from backend.infrastructure.adk.core.llm import configure_environment

# Configure Logging (Detailed)
setup_logging()
logger = logging.getLogger(__name__)

# Configure Environment (Critical for API Keys)
configure_environment()

# Routers
from backend.entrypoints.api.routers import market, agent, adk, browser, macro, search, report, simulation

app = FastAPI(title="AI Funding Backend", version="2.0")

# Mount Static Files (Reports)
import os
static_dir = os.path.join(os.getcwd(), "backend", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(market.router)
app.include_router(agent.router)
app.include_router(adk.router)  # /chat
app.include_router(browser.router)
app.include_router(macro.router)
app.include_router(search.router)
app.include_router(report.router)
app.include_router(simulation.router) # /api/simulation

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0"}

def print_registered_routes(app: FastAPI):
    """Print all registered routes."""
    logger.info("Registered API Routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ",".join(route.methods)
            logger.info(f"  {methods} {route.path}")

def start():
    """Entry point for programmable start."""
    port = int(config.get("port", 8000))
    print_registered_routes(app) # Print routes on start
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start()
