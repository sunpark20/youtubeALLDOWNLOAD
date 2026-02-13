"""
Logging Configuration

Centralized logging setup for the application
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "YouTubeDownloader", level: int = logging.INFO) -> logging.Logger:
    """
    Setup and configure application logger

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()


if __name__ == "__main__":
    # Test logger
    test_logger = setup_logger("TestLogger", logging.DEBUG)
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
