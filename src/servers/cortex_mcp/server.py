import logging
import os
from contextlib import asynccontextmanager

from typing import AsyncIterator

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from common.MCPContext import MCPContext
from core.config import config

logger = logging.getLogger("Cortex MCP")


@asynccontextmanager
async def mcp_lifespan(mcp_server: FastMCP) -> AsyncIterator[MCPContext]:
    """
    Manage application lifecycle.

    Args:
        mcp_server: FastMCP server

    Yields:
        MCPContext: MCP context.

    Raises:
        ValueError: If required environment variables are not set
    """
    try:
        api_key = os.getenv(config.papi_auth_header_key)
        api_key_id = os.getenv(config.papi_auth_id_key)

        if not api_key or not api_key_id:
            raise ValueError("Missing authentication headers")

        context = MCPContext(auth_headers={"Authorization": api_key, "X-XDR-AUTH-ID": api_key_id})

        # Register dynamic tools
        try:

            logger.info("Registered tools).")
        except Exception as e:
            logger.exception(f"Error registering tools: {e}")
            raise Exception(f"Failed to register tools: {e}") from e

        yield context
    except Exception as e:
        logger.exception(f"Error during mcp server initialization: {e}")
        raise


mcp = FastMCP(
    name="Cortex MCP Server",
    lifespan=mcp_lifespan,
)


@mcp.custom_route("/ping/", methods=["GET"], include_in_schema=False)
async def _health_check_route(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})
