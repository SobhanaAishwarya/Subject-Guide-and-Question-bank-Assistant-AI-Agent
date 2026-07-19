import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str = "agentic_ai_clean", log_level: Optional[str] = None) -> logging.Logger:
    """
    Configures and returns a highly detailed production-grade logger with console
    and rotating file outputs. Fully type-hinted and structured.
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Resolve numerical logging level
    numeric_level = getattr(logging, log_level, logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    logger = logging.getLogger(name)
    
    # Avoid duplicate handler execution if logger is already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(numeric_level)

    # Standardized microsecond-accurate log formatting
    log_format = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Streaming Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # 2. Production Rotating File Handler
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, "app.log")
        
        # Rotates file at 5MB, keeping up to 5 backup historic fragments
        file_handler = RotatingFileHandler(
            file_path, 
            maxBytes=5 * 1024 * 1024, 
            backupCount=5, 
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if filesystem write permissions fail during initial setup
        print(f"Warning: Failed to initialize file logging fallback to console only: {str(e)}", file=sys.stderr)

    return logger

# Single instantiation point for global import across application modules
logger = setup_logger()