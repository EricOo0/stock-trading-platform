import uvicorn
import time
from fastapi import FastAPI, Request
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
    
    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # 记录请求
        logger.info(f"📥 {request.method} {request.url.path}")
        if request.query_params:
            logger.debug(f"   Query params: {dict(request.query_params)}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
    
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
