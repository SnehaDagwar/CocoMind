"""Structured logging + OpenTelemetry + Prometheus instrumentation."""

from __future__ import annotations

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON logging with trace context."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "cocomind") -> structlog.BoundLogger:
    """Get a structured logger with application context."""
    return structlog.get_logger(name)
