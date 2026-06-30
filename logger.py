import logging
import sys
from datetime import datetime, timezone

from config import settings


def setup_logger(name: str = "github-agent") -> logging.Logger:
    """
    Creates a structured logger with consistent formatting.
    Logs go to both console and a file in the logs/ directory.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    # Format: timestamp | level | module | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler("logs/github_agent.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Single shared logger instance
logger = setup_logger()
