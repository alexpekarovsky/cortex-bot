import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Context

from src.entities.MCPContext import MCPContext
from src.usecase.fetcher import Fetcher, get_fetcher


class TestFetcher:
    """Test cases for the Fetcher class."""

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_url')
    @patch.dict(os.environ, {}, clear=True)
    async def test_get_fetcher_from_lifespan_context(self, mock_get_papi_url):
        """Test get_fetcher when credentials are available in lifespan context."""
        # Setup
        mock_url = "https://api.example.com"
        mock_get_papi_url.return_value = mock_url

        # Create mock context with lifespan context
        mock_lifespan = MagicMock(spec=MCPContext)
        mock_lifespan.auth_headers = {
            "Authorization": "Bearer lifespan_token",
            "X-XDR-AUTH-ID": "lifespan_id"
        }

        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = mock_lifespan

        mock_context = MagicMock(spec=Context)
        mock_context.request_context = mock_request_context
        mock_context.set_state = MagicMock()

        # Execute
        with patch('src.usecase.fetcher.get_config') as mock_config:
            mock_config.papi_url_env_key = "PAPI_URL"
            result = await get_fetcher(mock_context)

        # Verify
        assert isinstance(result, Fetcher)
        assert result.url == mock_url
        assert result.api_key == "Bearer lifespan_token"
        assert result.api_key_id == "lifespan_id"
        mock_context.set_state.assert_called_once_with("fetcher", result)

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_url')
    @patch.dict(os.environ, {
        "PAPI_AUTH_HEADER": "env_api_key",
        "PAPI_AUTH_ID": "env_auth_id"
    })
    async def test_get_fetcher_from_environment_vars(self, mock_get_papi_url):
        """Test get_fetcher when credentials are not in lifespan but available in env vars."""
        # Setup
        mock_url = "https://api.example.com"
        mock_get_papi_url.return_value = mock_url

        # Create mock context with empty lifespan context
        mock_lifespan = MagicMock(spec=MCPContext)
        mock_lifespan.auth_headers = {}  # Empty auth headers

        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = mock_lifespan

        mock_context = MagicMock(spec=Context)
        mock_context.request_context = mock_request_context
        mock_context.set_state = MagicMock()

        # Execute
        with patch('src.usecase.fetcher.get_config') as mock_config:
            mock_config().papi_url_env_key = "PAPI_URL"
            mock_config().papi_auth_header_key = "PAPI_AUTH_HEADER"
            mock_config().papi_auth_id_key = "PAPI_AUTH_ID"
            result = await get_fetcher(mock_context)

        # Verify
        assert isinstance(result, Fetcher)
        assert result.url == mock_url
        assert result.api_key == "PAPI_AUTH_HEADER"
        assert result.api_key_id == "PAPI_AUTH_ID"
        mock_context.set_state.assert_called_once_with("fetcher", result)

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_url')
    @patch.dict(os.environ, {
        "PAPI_AUTH_HEADER": "env_api_key",
        "PAPI_AUTH_ID": "env_auth_id"
    })
    async def test_get_fetcher_partial_lifespan_auth_fallback(self, mock_get_papi_url):
        """Test get_fetcher falls back to env vars when lifespan has partial auth."""
        # Setup
        mock_url = "https://api.example.com"
        mock_get_papi_url.return_value = mock_url

        # Create mock context with partial lifespan auth (missing X-XDR-AUTH-ID)
        mock_lifespan = MagicMock(spec=MCPContext)
        mock_lifespan.auth_headers = {
            "Authorization": "Bearer partial_token"
            # Missing X-XDR-AUTH-ID
        }

        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = mock_lifespan

        mock_context = MagicMock(spec=Context)
        mock_context.request_context = mock_request_context
        mock_context.set_state = MagicMock()

        # Execute
        with patch('src.usecase.fetcher.get_config') as mock_config:
            mock_config().papi_url_env_key = "PAPI_URL"
            mock_config().papi_auth_header_key = "PAPI_AUTH_HEADER"
            mock_config().papi_auth_id_key = "PAPI_AUTH_ID"
            result = await get_fetcher(mock_context)

        # Verify - should use env vars since lifespan auth is incomplete
        assert isinstance(result, Fetcher)
        assert result.url == mock_url
        assert result.api_key == "PAPI_AUTH_HEADER"
        assert result.api_key_id == "PAPI_AUTH_ID"

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_default_params(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request with default parameters."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success", "data": {"id": 123}}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute
        path = "/test/endpoint"
        result = await fetcher_instance.send_request(path)

        # Verify
        mock_get_papi_auth_headers.assert_called_once_with(fetcher_instance.api_key, fetcher_instance.api_key_id)
        mock_papi_client.assert_called_once_with(fetcher_instance.url, mock_headers)
        mock_client_instance.request.assert_called_once_with(
            "POST",
            "/public_api/v1/test/endpoint",
            data=None,
            headers=mock_headers
        )
        assert result == mock_response

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_with_custom_params(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request with custom parameters."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success"}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute
        path = "/custom/endpoint"
        method = "GET"
        data = {"key": "value"}
        custom_headers = {"Custom-Header": "value"}

        result = await fetcher_instance.send_request(
            path=path,
            method=method,
            data=data,
            headers=custom_headers
        )

        # Verify
        mock_get_papi_auth_headers.assert_called_once_with(fetcher_instance.api_key, fetcher_instance.api_key_id)
        mock_papi_client.assert_called_once_with(fetcher_instance.url, mock_headers)
        mock_client_instance.request.assert_called_once_with(
            method,
            "/public_api/v1/custom/endpoint",
            data=data,
            headers=mock_headers
        )
        assert result == mock_response

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_omit_papi_prefix(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request with omit_papi_prefix=True."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success"}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute
        path = "/custom/raw/endpoint"
        result = await fetcher_instance.send_request(path, omit_papi_prefix=True)

        # Verify
        mock_client_instance.request.assert_called_once_with(
            "POST",
            "/custom/raw/endpoint",  # No prefix added
            data=None,
            headers=mock_headers
        )
        assert result == mock_response

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_path_already_has_prefix(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request when path already contains public_api/v1 prefix."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success"}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute
        path = "/public_api/v1/already/prefixed"
        result = await fetcher_instance.send_request(path)

        # Verify - should not double-add the prefix
        mock_client_instance.request.assert_called_once_with(
            "POST",
            "/public_api/v1/already/prefixed",
            data=None,
            headers=mock_headers
        )
        assert result == mock_response

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_path_with_trailing_slash_prefix(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request when path already contains public_api/v1/ prefix with trailing slash."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success"}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute
        path = "/public_api/v1/already/prefixed"
        result = await fetcher_instance.send_request(path)

        # Verify - should not double-add the prefix
        mock_client_instance.request.assert_called_once_with(
            "POST",
            "/public_api/v1/already/prefixed",
            data=None,
            headers=mock_headers
        )
        assert result == mock_response

    @pytest.mark.asyncio
    @patch('src.usecase.fetcher.get_papi_auth_headers')
    @patch('src.usecase.fetcher.PAPIClient')
    async def test_send_request_path_leading_slash_handling(self, mock_papi_client, mock_get_papi_auth_headers, fetcher_instance):
        """Test send_request properly handles paths with and without leading slashes."""
        # Setup mocks
        mock_headers = {"Authorization": "Bearer token", "X-XDR-AUTH-ID": "test_id"}
        mock_get_papi_auth_headers.return_value = mock_headers

        mock_client_instance = AsyncMock()
        mock_response = {"status": "success"}
        mock_client_instance.request.return_value = mock_response
        mock_papi_client.return_value.__aenter__.return_value = mock_client_instance

        # Execute with path without leading slash
        path = "test/endpoint"
        result = await fetcher_instance.send_request(path)

        # Verify - should properly join the path
        mock_client_instance.request.assert_called_once_with(
            "POST",
            "/public_api/v1/test/endpoint",
            data=None,
            headers=mock_headers
        )
        assert result == mock_response
