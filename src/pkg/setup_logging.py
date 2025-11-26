# fmt: off
import logging
import sys
from pathlib import Path

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
        - Log format: "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        - Time format: "%Y-%m-%d %H:%M:%S"
        - Logs to both stderr and file (cortex-mcp.log)
    """
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_formatter = logging.Formatter(
        fmt="%(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Create stderr handler (for MCP protocol)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(simple_formatter)

    # Create file handler for persistent logs
    log_file = Path(__file__).parent.parent.parent / "cortex-mcp.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(detailed_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(stderr_handler)
    root_logger.addHandler(file_handler)

    # Also configure Uvicorn loggers
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.handlers.clear()
        logger.addHandler(stderr_handler)
        logger.addHandler(file_handler)

    # Log the log file location
    root_logger.info(f"Logging to file: {log_file.absolute()}")

    return root_logger
# fmt: on
