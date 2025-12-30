"""
Structured logging configuration for BookRAGAgent.

Sets up JSON logging for production and colored logging for development.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "bookragagent.log"


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Never log API keys or secrets
        message_str = log_data["message"]
        if any(secret in message_str.lower() for secret in ["api_key", "password", "token", "secret"]):
            log_data["message"] = "[REDACTED]"

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development logging."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format log record with colors."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)

        # Format the log message
        log_format = (
            f"{color}[{levelname}]{self.RESET} "
            f"{record.name}:{record.funcName}:{record.lineno} - {record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            log_format += f"\n{self.formatException(record.exc_info)}"

        return log_format


def setup_logging(log_level: str = "INFO", production: bool = False):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        production: If True, use JSON formatting; if False, use colored formatting
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if production:
        formatter = JsonFormatter()
    else:
        formatter = ColoredFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (JSON format always)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at level {log_level}")
