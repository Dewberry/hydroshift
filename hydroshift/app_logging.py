# logging_config.py
import logging
import logging.handlers
import sys
from pathlib import Path


def handle_uncaught(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger().critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO, log_file: str = "app.log") -> None:
    # Make dir
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / log_file

    # Establish format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s"
    formatter = logging.Formatter(log_format, "%Y-%m-%d %H:%M:%S")

    # Establish global settings
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=int(1e7), backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Handle uncaught
    if sys.excepthook != handle_uncaught:
        sys.excepthook = handle_uncaught
