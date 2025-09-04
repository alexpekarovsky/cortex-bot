import asyncio
import os
import signal
import logging
from functools import partial

from fastmcp.server.server import Transport

from config.config import config
from service.cortex_mcp.server import create_mcp_server
from usecase.xsiam import xsiam_mcp
from pkg.setup_logging import setup_logging

logger = logging.getLogger("Cortex MCP")

async def shutdown(sig: signal.Signals, loop: asyncio.AbstractEventLoop):
    logger.info(f"Received exit signal {sig.name}...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    logger.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Stopping the event loop")
    loop.stop()


async def async_main(transport: Transport):
    setup_logging(config)
    logger.info(f"Starting Cortex MCP Server")

    loop = asyncio.get_running_loop()

    # Add signal handlers for SIGINT and SIGTERM
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, partial(lambda s: asyncio.create_task(shutdown(s, loop)), sig))

    api_key = os.getenv(config.papi_auth_header_key)
    api_key_id = os.getenv(config.papi_auth_id_key)
    mcp = create_mcp_server(api_key, api_key_id)
    await mcp.import_server(prefix="cortex", server=xsiam_mcp)
    if config.mcp_transport == "stdio":
        await mcp.run_async(transport=transport)
    else:
        await mcp.run_async(
            transport=transport,
            host=config.mcp_host,
            port=config.mcp_port,
            path=config.mcp_path,
        )


def main():
    try:
        asyncio.run(async_main(config.mcp_transport))
    except Exception as e:
        logger.exception(f"Main loop stopped: {e}")
    finally:
        logger.info("Cortex MCP Server has shut down.")


if __name__ == "__main__":
    main()
