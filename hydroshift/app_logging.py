# logging_config.py
import logging
import logging.handlers
import sys
from pathlib import Path

NOISY_LOGGERS = {
    "watchdog": logging.WARNING,
    "PIL": logging.INFO,
    "urllib3": logging.INFO,
    "matplotlib": logging.WARNING,
    "fiona": logging.WARNING,
    "rasterio": logging.WARNING,
}
for logger_name, level in NOISY_LOGGERS.items():
    logging.getLogger(logger_name).setLevel(level)

def handle_uncaught(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger().critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging(log_dir: str = "logs", console_level: int = logging.INFO, file_level: int = logging.DEBUG, log_file: str = "app.log") -> None:
    # Make dir
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / log_file

    # Establish format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s"
    formatter = logging.Formatter(log_format, "%Y-%m-%d %H:%M:%S")

    # Establish global settings
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=int(1e7), backupCount=5, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Handle uncaught
    if sys.excepthook != handle_uncaught:
        sys.excepthook = handle_uncaught
