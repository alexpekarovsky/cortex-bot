import json
import logging

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

from entities.exceptions import PAPIConnectionError, PAPIClientError, PAPIResponseError, PAPIAuthenticationError, \
    PAPIClientRequestError, PAPIServerError

logger = logging.getLogger(__name__)


class PAPIClient:
    def __init__(self, url: str, api_key: str, api_key_id: str):
        self.url = url
        self.api_key = api_key
        self.api_key_id = api_key_id

    def send_request(self, method: str, path: str, data: dict = None, headers: dict = None) -> dict:
        """
        Send an HTTP request to the PAPI server.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            path (str): API endpoint path to append to the base URL
            data (dict, optional): Request payload data. Will be JSON serialized.
            headers (dict, optional): Custom HTTP headers. If not provided, default
                                    headers with authentication will be used.

        Returns:
            dict: Parsed JSON response from the server

        Raises:
            PAPIConnectionError: Raised when there are network connectivity issues:
                - Connection cannot be established to the server
                - Request timeout occurs
                - General network/transport errors
                - DNS resolution failures

            PAPIAuthenticationError: Raised for authentication/authorization failures:
                - 401 Unauthorized: Invalid API key or credentials
                - 403 Forbidden: Valid credentials but insufficient permissions

            PAPIClientRequestError: Raised for client-side request errors (4xx):
                - 400 Bad Request: Invalid request format or parameters
                - 404 Not Found: Requested resource doesn't exist
                - 405 Method Not Allowed: HTTP method not supported for endpoint
                - 409 Conflict: Request conflicts with current server state
                - 422 Unprocessable Entity: Request validation failed
                - Other 4xx status codes

            PAPIServerError: Raised for server-side errors (5xx):
                - 500 Internal Server Error: Unexpected server error
                - 502 Bad Gateway: Invalid response from upstream server
                - 503 Service Unavailable: Server temporarily unavailable
                - 504 Gateway Timeout: Upstream server timeout
                - Other 5xx status codes

            PAPIResponseError: Raised for invalid or malformed responses:
                - Server returns None response
                - Invalid JSON in response body
                - Unexpected HTTP status codes outside standard ranges

            PAPIClientError: Raised for unexpected errors that don't fit other categories:
                - Unexpected exceptions during request processing
                - Programming errors or edge cases

        Example:
            >>> client = PAPIClient("https://api.example.com", "api_key", "key_id")
            >>> try:
            ...     result = client.send_request("GET", "/endpoints")
            ... except PAPIAuthenticationError:
            ...     print("Check your API credentials")
            ... except PAPIConnectionError:
            ...     print("Network connection issue")
            ... except PAPIServerError:
            ...     print("Server is experiencing issues")
        """
        if not headers:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.api_key,
                'X-XDR-AUTH-ID': self.api_key_id
            }

        full_url = f'{self.url}{path}'
        logger.info(f'Sending request to {full_url}')

        try:
            response = requests.request(
                method=method,
                url=full_url,
                data=json.dumps(data) if data else None,
                headers=headers
            )
        except ConnectionError as e:
            logger.exception(f'Connection failed for request to {path}: {e}')
            raise PAPIConnectionError(f'Failed to connect to PAPI server at {path}: {e}') from e
        except Timeout as e:
            logger.exception(f'Request timeout for request to {path}: {e}')
            raise PAPIConnectionError(f'Request timeout for {path}: {e}') from e
        except RequestException as e:
            logger.exception(f'Request failed for request to {path}: {e}')
            raise PAPIConnectionError(f'Request failed for {path}: {e}') from e
        except Exception as e:
            logger.exception(f'Unexpected error sending request to {path}: {e}')
            raise PAPIClientError(f'Unexpected error for request to {path}: {e}') from e

        if response is None:
            err_msg = f'Received None response from server for request to {path}'
            logger.error(err_msg)
            raise PAPIResponseError(err_msg)

        # Handle different HTTP status codes more specifically
        if response.status_code == 401:
            err_msg = f'Authentication failed for request to {path}: {response.content}'
            logger.error(err_msg)
            raise PAPIAuthenticationError(err_msg)
        elif response.status_code == 403:
            err_msg = f'Authorization failed for request to {path}: {response.content}'
            logger.error(err_msg)
            raise PAPIAuthenticationError(err_msg)
        elif 400 <= response.status_code < 500:
            err_msg = f'Client error for request to {path}: {response.content} [{response.status_code}]'
            logger.error(err_msg)
            raise PAPIClientRequestError(err_msg)
        elif 500 <= response.status_code < 600:
            err_msg = f'Server error for request to {path}: {response.content} [{response.status_code}]'
            logger.error(err_msg)
            raise PAPIServerError(err_msg)
        elif response.status_code < 200 or response.status_code >= 300:
            err_msg = f'Unexpected response code for request to {path}: {response.content} [{response.status_code}]'
            logger.error(err_msg)
            raise PAPIResponseError(err_msg)

        try:
            return response.json()
        except json.JSONDecodeError as e:
            err_msg = f'Invalid JSON response from server for request to {path}: {e}'
            logger.error(err_msg)
            raise PAPIResponseError(err_msg) from e