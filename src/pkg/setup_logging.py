# fmt: off
import logging
import sys

from pydantic_settings import BaseSettings


def setup_logging(config: BaseSettings):
    """
    Configure logging for the application with a consistent format and handler.

    Sets up a StreamHandler that outputs to stdout with a custom formatter,
    and configures both the root logger and Uvicorn-specific loggers to use
    the same handler and formatting.

    Args:
        config (BaseSettings): Configuration object that must contain a
            'log_level' attribute specifying the desired logging level
            (e.g., logging.DEBUG, logging.INFO, etc.)

    Returns:
        logging.Logger: The configured root logger instance

    Note:
        - Clears any existing handlers on the root logger and Uvicorn loggers
        - Uvicorn loggers are configured with propagate=False to prevent
          duplicate log messages
        - Log format: "%(name)s | %(message)s"
        - Time format: "%H:%M:%S"
    """
    handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        fmt="%(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Also configure Uvicorn loggers
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.handlers.clear()
        logger.addHandler(handler)

    configure_library_logging()

    return root_logger
# fmt: on

def configure_library_logging():
    """
    Configure logging levels for external libraries to reduce verbose output.
    """
    # Set library logging to WARNING level to suppress debug/info logs
    for name in ("mcp.server.lowlevel.server", "mcp.server.streamable_http_manager", "sse_starlette.sse", "httpx", "httpcore", "httpcore.http11", "httpcore.connection"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
