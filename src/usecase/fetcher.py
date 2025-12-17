import io
import logging
import os
from typing import Optional

from fastmcp import Context

from config.config import get_config
from entities.MCPContext import MCPContext
from pkg.client import PAPIClient
from pkg.util import get_papi_auth_headers, get_papi_url

logger = logging.getLogger(__name__)

class Fetcher:
    """
    Fetcher class for interacting with public API endpoints.
    """

    def __init__(self, url: str, api_key: str, api_key_id: str) -> None:
        """
        Initialize the Fetcher with a URL and an API key for authentication.

        Args:
            url (str): The url of the public API.
            api_key (str): The API key to use with the public API
            api_key_id (str): The API key ID to use with the public API
        """
        self.url = url
        self.api_key = api_key
        self.api_key_id = api_key_id

    async def send_request(self, path: str, method: str = "POST", data: Optional[dict | str] = None, headers: Optional[dict] = None, omit_papi_prefix: bool = False, stream: bool = False) -> dict | io.BytesIO:
        """
        Send an HTTP request to the public API.

        Automatically prepends the public API v1 path prefix unless omit_papi_prefix is True.
        Delegates the actual request to the underlying PAPIClient.

        Args:
            path (str): The API endpoint path to send the request to.
            method (str, optional): The HTTP method to use. Defaults to "POST".
            data (dict | str, optional): The request payload data. Defaults to None.
            headers (dict, optional): Additional HTTP headers to include. Defaults to None.
            omit_papi_prefix (bool, optional): Whether to skip adding the /public_api/v1 prefix. Defaults to False.
            stream (bool, optional): Whether to stream response. Defaults to False.

        Returns:
            dict: The response from the request.
        """
        if not omit_papi_prefix:
            # Add the API path
            if "/public_api/v1" not in path and "/public_api/v1/" not in path:
                path = os.path.join("/public_api/v1", path.lstrip("/"))

        headers = get_papi_auth_headers(self.api_key, self.api_key_id)
        async with PAPIClient(self.url, headers) as client:
            if stream:
                result = await client.stream(method, path, data=data, headers=headers)
            else:
                result = await client.request(method, path, json=data, headers=headers)

        return result


async def get_fetcher(ctx: Context) -> Fetcher:
    """
    Create and configure a Fetcher instance with authentication credentials.

    Retrieves authentication credentials from the context lifespan or environment variables,
    creates a new Fetcher instance, and stores it in the context state.

    Args:
        ctx (Context): The FastMCP context containing request and lifespan information.

    Returns:
        Fetcher: A configured Fetcher instance ready to make API requests.
    """
    config = get_config()
    url = get_papi_url(config.papi_url_env_key)
    lifespan: MCPContext = ctx.request_context.lifespan_context
    api_key = lifespan.auth_headers.get("Authorization")
    xdr_id = lifespan.auth_headers.get("X-XDR-AUTH-ID")
    if not (api_key and xdr_id):
        api_key = config.papi_auth_header_key
        xdr_id = config.papi_auth_id_key

    logger.info(f"Creating new fetcher for auth ID {xdr_id}")
    fetcher = Fetcher(url, api_key, xdr_id)
    ctx.set_state("fetcher", fetcher)
    return fetcher
