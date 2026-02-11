import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from entities.MCPContext import MCPContext

logger = logging.getLogger("Cortex MCP")


def create_mcp_lifespan(api_key: Optional[str] = None, api_key_id: Optional[str] = None):
    """
    Factory function to create mcp_lifespan with injected dependencies.

    Args:
        api_key: API key to inject (falls back to env var if None)
        api_key_id: API key ID to inject (falls back to env var if None)
    """
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

    return mcp_lifespan


# Create MCP server with injected dependencies
def create_mcp_server(api_key: Optional[str] = None, api_key_id: Optional[str] = None) -> FastMCP:
    """
    Create FastMCP server with injected dependencies.

    Args:
        api_key: API key
        api_key_id: API key ID

    Returns:
        FastMCP: Configured server instance
    """
    lifespan = create_mcp_lifespan(api_key, api_key_id)

    mcp = FastMCP(
        name="Cortex MCP Server",
        lifespan=lifespan,
    )

    @mcp.custom_route("/ping/", methods=["GET"], include_in_schema=False)
    async def _health_check_route(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return mcp
