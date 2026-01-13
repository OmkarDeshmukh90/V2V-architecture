"""
Logging utilities for V2V system
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str = "v2v_system", 
                log_file: Optional[str] = None,
                level: int = logging.INFO,
                debug: bool = False) -> logging.Logger:
    """
    Set up logger for V2V system.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        debug: Enable debug mode
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if debug:
        level = logging.DEBUG
    
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "v2v_system") -> logging.Logger:
    """Get existing logger or create default one"""
    return logging.getLogger(name)
