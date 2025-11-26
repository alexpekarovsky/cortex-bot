import logging
import httpx

logger = logging.getLogger(__name__)


class OpenAPIClient(httpx.AsyncClient):
    """
    OpenAPI-compatible async HTTP client for FastMCP integration.

    This client extends httpx.AsyncClient and properly returns Response objects
    instead of parsed JSON, which is what FastMCP.from_openapi() expects.
    """

    def __init__(self, base_url: str, headers: dict[str, str], timeout: int = 30, **kwargs):
        """
        Initialize OpenAPIClient as an AsyncClient.

        Args:
            base_url (str): Base URL for the PAPI server
            headers (dict): default headers for PAPI
            timeout (int): Request timeout in seconds
            **kwargs: Additional arguments passed to httpx.AsyncClient
        """
        # Set default timeout if not provided in kwargs
        if 'timeout' not in kwargs:
            kwargs['timeout'] = timeout

        super().__init__(base_url=base_url, headers=headers, **kwargs)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Send an HTTP request and return the Response object.

        This method overrides the parent's request method to ensure proper
        error handling and logging while returning the raw Response object
        that FastMCP expects.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            url (str): API endpoint path
            **kwargs: Additional arguments (json, data, params, etc.)

        Returns:
            httpx.Response: The raw HTTP response object

        Raises:
            httpx.HTTPStatusError: For 4xx and 5xx responses
            httpx.RequestError: For connection and request errors
        """
        logger.debug(f"OpenAPI client request: {method} {url}")

        # Call the parent request method
        response = await super().request(method, url, **kwargs)

        # Raise for status to trigger error handling
        response.raise_for_status()

        return response
