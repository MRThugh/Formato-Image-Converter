"""
Utility helpers: logging, validation
"""
import logging
from pathlib import Path

def setup_logger():
    """Return a basic logger for the app."""
    logger = logging.getLogger("formato")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_output_folder(path):
    """Ensure output folder exists (Path or str)."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
