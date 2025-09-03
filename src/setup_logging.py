# fmt: off
from pydantic_settings import BaseSettings

import logging
import sys

def setup_logging(config: BaseSettings):

    from rich.logging import RichHandler

    handler = RichHandler( # noqa
        markup=True,
        tracebacks_show_locals=True,
        show_path=True,
        omit_repeated_times=False,
    )
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

    return root_logger
# fmt: on
