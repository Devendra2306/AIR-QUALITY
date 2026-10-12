import logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

from pathlib import Path
from app.config.settings import settings


def setup_logging():
    """Configure structured logging or fallback to standard logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    if HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger()
    else:
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(message)s",
            level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        )
        return logging.getLogger("air_quality")


logger = setup_logging()
