import logging
import os

from fastmcp import Context

from common.MCPContext import MCPContext
from core.client import PAPIClient
from core.config import config

logger = logging.getLogger(__name__)


async def get_fetcher(ctx: Context):
    url = get_papi_url()
    lifespan: MCPContext = ctx.request_context.lifespan_context
    api_key = lifespan.auth_headers.get("Authorization")
    xdr_id = lifespan.auth_headers.get("X-XDR-AUTH-ID")
    if not (api_key and xdr_id):
        api_key = os.getenv(config.papi_auth_header_key)
        xdr_id = os.getenv(config.papi_auth_id_key)

    logger.info(f"Creating new fetcher for auth ID {xdr_id}")
    fetcher = Fetcher(url, api_key, xdr_id)
    ctx.set_state("fetcher", fetcher)
    return fetcher

class Fetcher:
    """
    Fetcher class for interacting with public API endpoints.
    """

    def __init__(self, url: str, api_key: str, api_key_id: str):
        """
        Initialize the Fetcher with a URL and an API key for authentication.

        Args:
            url (str): The url of the public API.
            api_key (str): The API key to use with the public API
            api_key_id (str): The API key ID to use with the public API
        """
        self.client: PAPIClient = PAPIClient(url, api_key, api_key_id)

    def send_request(self, path: str, method: str = "POST", data: dict = None, headers: dict = None, omit_papi_prefix: bool = False):
        if not omit_papi_prefix:
            # Add the API path
            if "/public_api/v1" not in path and "/public_api/v1/" not in path:
                path = os.path.join("/public_api/v1", path.lstrip("/"))
        self.client.send_request(method, path, data, headers)


def get_papi_url():
    custom_url = os.getenv(config.papi_url_custom_key)
    url = os.getenv(config.papi_url_env_key)
    if not url or (custom_url is not None and custom_url != ""):
        url = custom_url

    if not url.startswith("https://"):
        if url.startswith("http://"):
            url = url.replace("http://", "https://")
        else:
            url = f"https://{url}"

    if "api-" not in url:
        url = url.replace("https://", "https://api-")

    return url
