"""
Structured JSON logging setup for AITester.
Emits machine-parseable JSON log lines compatible with
Datadog, CloudWatch, ELK, and other log aggregators.

Usage:
    from aitester.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("test_run_started", extra={"run_id": "abc", "project": "MyAPI"})
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.
    Extra fields passed via `extra={}` are merged into the JSON output,
    enabling structured context like request_id, run_id, endpoint, etc.
    """

    # Fields that exist on every LogRecord but should NOT be forwarded as extras
    _BUILTIN_ATTRS: frozenset[str] = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "message",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
            "taskName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Append exception traceback if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Append stack info if present
        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)

        # Merge any extra fields provided by the caller
        for key, value in record.__dict__.items():
            if key not in self._BUILTIN_ATTRS and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class PlainFormatter(logging.Formatter):
    """
    Human-readable formatter for local development.
    Used when ENVIRONMENT=development and LOG_LEVEL=DEBUG.
    """

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, "")
        ts = datetime.now(UTC).strftime("%H:%M:%S")
        prefix = f"{color}[{record.levelname:8s}]{self.RESET}"
        return f"{ts} {prefix} {record.name}: {record.getMessage()}"


def setup_logging(
    level: str = "INFO",
    use_json: bool = True,
    stream: Any = None,
) -> None:
    """
    Configure root and aitester loggers.

    Args:
        level:    Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        use_json: If True, emit JSON. If False, use human-readable format.
        stream:   Output stream (defaults to stdout).
    """
    if stream is None:
        stream = sys.stdout

    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter() if use_json else PlainFormatter())

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure the aitester package logger
    aitester_logger = logging.getLogger("aitester")
    aitester_logger.setLevel(numeric_level)
    aitester_logger.handlers.clear()
    aitester_logger.addHandler(handler)
    aitester_logger.propagate = False

    # Suppress noisy third-party loggers in non-debug mode
    if numeric_level > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that inherits from the aitester root logger.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured Logger instance.

    Example:
        logger = get_logger(__name__)
        logger.info("Parser started", extra={"spec_path": path})
    """
    return logging.getLogger(name)
