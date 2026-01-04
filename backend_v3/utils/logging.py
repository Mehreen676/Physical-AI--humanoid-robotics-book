"""Structured logging utilities."""

import json
import logging
from datetime import datetime


class StructuredLogger:
    """Structured JSON logger."""

    @staticmethod
    def log_event(event: str, level: str = "INFO", **kwargs):
        """
        Log structured JSON event.

        Args:
            event: Event name
            level: Log level
            **kwargs: Additional event data
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs
        }

        logger = logging.getLogger("agentic_rag")
        getattr(logger, level.lower())(json.dumps(log_entry))

    @staticmethod
    def log_latency(operation: str, latency_ms: float):
        """
        Log operation latency.

        Args:
            operation: Operation name
            latency_ms: Latency in milliseconds
        """
        StructuredLogger.log_event(
            "latency_metric",
            operation=operation,
            latency_ms=round(latency_ms, 2)
        )
