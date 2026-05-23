from __future__ import annotations

import logging
import structlog
from pathlib import Path

from mimo_tui.constants import LOG_FILE


def configure_logging(debug: bool = False) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        filename=str(LOG_FILE),
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[return-value]
