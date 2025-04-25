"""
Logger setup for the WeCare application.
"""
import logging
import logging.config
from typing import Dict, Any

from wecare.config.settings import LOGGING


def setup_logging() -> None:
    """Configure the logging system based on settings."""
    logging.config.dictConfig(LOGGING)
    
    
def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Name for the logger
    
    Returns:
        Configured logger
    """
    return logging.getLogger(name) 