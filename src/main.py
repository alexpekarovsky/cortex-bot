"""
Cortex MCP Server Main Module

This module serves as the entry point for the Cortex MCP (Model Context Protocol) Server.
It handles server initialization, signal handling for graceful shutdown, and manages
the async event loop for the MCP server operations.

The server can operate in different transport modes (stdio, streamable-http) and integrates
with XSIAM (Extended Security Intelligence and Automation Management) services.
"""
import os

# Enable advanced FastMCP OpenAPI parser for enhanced API specification processing
# This must be set before importing FastMCP to ensure the new parser is used for
# better compatibility with complex OpenAPI schemas and improved error handling
os.environ.setdefault("FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER", "true") # noqa: E402

import asyncio
import logging
import signal
from functools import partial

from fastmcp import FastMCP
from fastmcp.server.server import Transport

from config.config import get_config
from pkg.client import PAPIClient
from pkg.setup_logging import setup_logging
from pkg.util import bundle_openapi_from_folders, get_papi_auth_headers, get_papi_url
from service.cortex_mcp.server import create_mcp_server
from usecase.module_util import discover_and_register_modules

logger = logging.getLogger("Cortex MCP")

mcp = FastMCP()

async def shutdown(sig: signal.Signals, loop: asyncio.AbstractEventLoop):
    """
    Handle graceful shutdown of the Cortex MCP Server.

    This function is called when the server receives termination signals (SIGINT/SIGTERM).
    It cancels all running tasks and stops the event loop cleanly.

    Args:
        sig (signal.Signals): The signal that triggered the shutdown (SIGINT or SIGTERM)
        loop (asyncio.AbstractEventLoop): The current asyncio event loop to be stopped

    Returns:
        None
    """
    logger.info(f"Received exit signal {sig.name}...")

    # Get all running tasks except the current shutdown task
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    logger.info("Cancelling outstanding tasks")
    # Wait for all tasks to complete or be canceled
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Stopping the event loop")
    loop.stop()


async def async_main(transport: Transport):
    """
    Main async function that initializes and runs the Cortex MCP Server.

    This function sets up logging, configures signal handlers for graceful shutdown,
    creates the MCP server with authentication, imports the XSIAM server module,
    and starts the server with the appropriate transport configuration.

    Args:
        transport (Transport): The transport mechanism for the MCP server
                              (e.g., 'stdio', 'streamable-http')

    Returns:
        None

    Raises:
        Exception: Any exception that occurs during server initialization or runtime.
    """
    config = get_config()
    setup_logging(config)
    logger.info("Starting Cortex MCP Server")

    loop = asyncio.get_running_loop()

    # Add signal handlers for SIGINT and SIGTERM for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, partial(lambda s: asyncio.create_task(shutdown(s, loop)), sig))

    # Retrieve API credentials from environment variables
    api_key = config.papi_auth_header_key
    api_key_id = config.papi_auth_id_key
    papi_url = config.papi_url_env_key

    mcp = await initialize_mcp_server(api_key, api_key_id, papi_url)

    # Start server with appropriate transport configuration
    if transport == "stdio":
        await mcp.run_async(transport=transport)
    else:
        # Use http stream or other transport with host/port configuration
        await mcp.run_async(
            transport=transport,
            host=config.mcp_host,
            port=config.mcp_port,
            path=config.mcp_path,
        )


async def initialize_mcp_server(api_key: str, api_key_id: str, papi_url: str) -> FastMCP:
    # Create MCP server instance with authentication
    mcp = create_mcp_server(api_key, api_key_id)

    # Discover mcp components from modules
    discover_and_register_modules(mcp)

    # Discover mcp components from openapi specs and import them
    spec = bundle_openapi_from_folders()
    open_api_mcp = FastMCP.from_openapi(spec,
                                        PAPIClient(get_papi_url(papi_url), get_papi_auth_headers(api_key, api_key_id)))
    await mcp.import_server(server=open_api_mcp)

    return mcp


def main():
    """
    Entry point for the Cortex MCP Server application.

    This function serves as the main entry point that wraps the async main function
    in an asyncio.run() call. It handles top-level exception catching and ensures
    proper cleanup and logging during shutdown.

    Returns:
        None

    Side Effects:
        - Starts the asyncio event loop
        - Logs server startup and shutdown events
        - Handles exceptions and ensures graceful shutdown
    """
    try:
        asyncio.run(async_main(get_config().mcp_transport))
    except Exception as e:
        logger.exception(f"Main loop stopped: {e}")
    finally:
        logger.info("Cortex MCP Server has shut down.")


if __name__ == "__main__":
    main()
