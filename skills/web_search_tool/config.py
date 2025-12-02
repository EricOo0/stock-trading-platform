import os

class Config:
    LOG_LEVEL = "INFO"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
