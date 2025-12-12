"""Logging configuration"""

import logging
import sys
from src.config import LOG_FORMAT, LOG_LEVEL, LOG_FILE


def setup_logging():
    """Configure logging with both file and console output"""
    log_format = logging.Formatter(LOG_FORMAT)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # File handler
    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Could not create log file: {e}")

    return root_logger
