"""
=====================================================================
Logging Module (src/utils/logger.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Provides standardized console and file logging with timestamps,
log levels, and clean formatting for academic viva demonstrations.
"""

import logging
import sys
from pathlib import Path
from src.utils.config import PROJECT_ROOT

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_DIR / "pipeline.log"


def get_logger(name: str = "API-Anomaly-System") -> logging.Logger:
    """Configures and returns a thread-safe singleton logger."""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formatter: Timestamp - LoggerName - Level - Message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-7s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
