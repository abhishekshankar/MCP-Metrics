"""Structured logging and metrics."""

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

logger = structlog.get_logger("analytics-mcp")

_metrics: dict[str, int] = {
    "sites_created": 0,
    "operations_total": 0,
    "operations_failed": 0,
    "mcp_invocations": 0,
}


def increment_metric(name: str, amount: int = 1) -> None:
    _metrics[name] = _metrics.get(name, 0) + amount


def get_metrics() -> dict[str, int]:
    return dict(_metrics)


def log_operation(operation: str, **kwargs) -> None:
    increment_metric("operations_total")
    logger.info(operation, **kwargs)


def log_failure(operation: str, error: str, **kwargs) -> None:
    increment_metric("operations_failed")
    logger.error(operation, error=error, **kwargs)
