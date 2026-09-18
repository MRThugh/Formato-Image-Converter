import logging
import sys
from utils.paths import get_log_dir


_logger_initialized = False


def setup_logger(name: str = "Formato") -> logging.Logger:
    global _logger_initialized
    logger = logging.getLogger(name)
    if _logger_initialized and logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler with UTF-8 support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_dir = get_log_dir()
    log_file = log_dir / "formato.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file logger at {log_file}: {e}")

    logger.propagate = False
    _logger_initialized = True
    return logger


def get_logger(name: str = "Formato") -> logging.Logger:
    return setup_logger(name)
