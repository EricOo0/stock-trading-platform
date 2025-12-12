import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file="backend/logs/app.log", level=logging.INFO):
    """
    Configure detailed logging system with console and file handlers.
    Format: [TIMESTAMP] LEVEL [LOGGER:LINE] - MESSAGE
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Define Format
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Console Handler (Stream)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # 2. File Handler (Rotating)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8' # 10MB per file
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)

    # 3. Third-party loggers adjustment
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging system initialized. Log file: {log_file}")
