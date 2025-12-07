import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from config import settings
from utils.logger import logger

def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Multi-Agent Memory System Service"
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router, prefix=settings.API_PREFIX, tags=["Memory"])
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Memory System starting up...")
        
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Memory System shutting down...")
        
    return app

app = create_app()

def start():
    """启动服务器"""
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=10000,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    start()
