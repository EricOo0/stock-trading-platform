import sys
from loguru import logger
from pathlib import Path
from config.settings import settings

def setup_logger():
    """配置全局日志"""
    
    # 移除默认的 handler
    logger.remove()
    
    # === 控制台输出 ===
    # 开发环境显示详细 Debug 信息，生产环境只显示 Info
    level = "DEBUG" if settings.DEBUG else "INFO"
    
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # === 文件输出 ===
    log_dir = settings.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 错误日志
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        rotation="10 MB",  # 文件大小超过 10MB 时轮转
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )
    
    # 访问日志/业务日志
    logger.add(
        log_dir / "app.log",
        level="INFO",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info(f"Logger initialized. Level: {level}")

# 自动初始化logger
setup_logger()

# 导出 logger 实例
__all__ = ["logger", "setup_logger"]
