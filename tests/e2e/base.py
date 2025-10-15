from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastmcp import Client

from main import initialize_mcp_server


class MockCortexServer:
    """Mock Cortex server for testing MCP interactions."""

    def __init__(self):
        self.cases = [
            {
                "case_id": "1",
                "severity": "high",
                "status": "active",
                "description": "Test security incident",
                "created_time": "2024-01-01T10:00:00Z",
                "issues_count": 5
            },
            {
                "case_id": "2",
                "severity": "medium",
                "status": "resolved",
                "description": "Another test incident",
                "created_time": "2024-01-01T09:00:00Z",
                "issues_count": 2
            }
        ]

        self.issues = [
            {
                "id": "1",
                "case_id": "1",
                "severity": "high",
                "source": "endpoint",
                "description": "Malicious file detected",
                "timestamp": "2024-01-01T10:05:00Z"
            },
            {
                "id": "2",
                "case_id": "2",
                "severity": "medium",
                "source": "network",
                "description": "Suspicious network activity",
                "timestamp": "2024-01-01T10:10:00Z"
            }
        ]
        self.assets = [
            {
                "issues_breakdown": {
                    "critical": 0,
                    "high": 0,
                    "low": 0,
                    "medium": 0
                },
                "xdm.asset.first_observed": 1747834085000,
                "xdm.asset.cloud.region": None,
                "xdm.asset.last_observed": 1748399709000,
                "issues_critical": 0,
                "xdm.asset.strong_id": "172.16.33.51",
                "xdm.asset.type.category": "Device",
                "xdm.asset.name": None,
                "xdm.asset.type.name": "Generic Device",
                "cases_breakdown": {
                    "critical": 0,
                    "high": 0,
                    "low": 0,
                    "medium": 0
                },
                "xdm.asset.provider": "ON_PREM",
                "xdm.asset.type.class": "Compute",
                "xdm.asset.id": "fffd007cff1c15f3a0d152ae630df9630ce00e39bc66811a9fa9b6457a788afc",
                "xdm.asset.type.id": "GENERIC_DEVICE",
                "cases_critical": 0,
                "xdm.asset.group_ids": [],
                "xdm.asset.realm": "Other",
                "xdm.host.ipv4_addresses": [
                    "172.16.33.51"
                ]
            }
        ]

    def route_request(self, method: str, url: str, **kwargs) -> dict:
        """Route mocked requests to appropriate handlers based on method and URL."""

        method = method.upper()

        if method == 'GET':
            raise ValueError("Method not supported")
        if method == 'PUT':
            raise ValueError("Method not supported")
        if method == 'POST':
            if '/case' in url:
                if kwargs["json"]["request_data"].get("filters", []) == [{"error": True}]:
                    raise ValueError("test")
                # POST /cases - list cases
                return {"reply": self.cases}
            elif '/issue/' in url:
                # POST /issues - list issues
                return {"reply": self.issues}

        # Default fallback for unmatched endpoints
        raise ValueError(f"Mock endpoint not implemented: {method} {url}")

class CortexMCPE2ETestBase:
    """Base class for Cortex MCP end-to-end tests."""

    @pytest.fixture(autouse=True)
    def setup_mock_environment(self, monkeypatch):
        """Set up mock environment variables for testing."""
        mock_env_vars = {
            "CORTEX_MCP_PAPI_AUTH_HEADER": "test-api-key-12345",
            "CORTEX_MCP_PAPI_AUTH_ID": "test-key-id-67890",
            "CORTEX_MCP_PAPI_URL": "test-cortex.example.com",
        }

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        # Store for test access
        self.mock_env_vars = mock_env_vars

        # Patch config functions if they exist
        with patch('usecase.fetcher.get_papi_url', return_value=mock_env_vars["CORTEX_MCP_PAPI_URL"]):
            yield

    @pytest.fixture
    def mock_cortex_server(self):
        """Fixture providing a mock Cortex server instance."""
        return MockCortexServer()

    @pytest_asyncio.fixture
    async def mock_papi_request(self, mock_cortex_server):
        """Fixture that patches PAPIClient.request method."""

        async def mock_request_handler(method: str, url: str, **kwargs):
            """Mock request handler that preserves all original parameters."""
            try:
                # Route the request to the mock server
                result = mock_cortex_server.route_request(method, url, **kwargs)
                return result
            except Exception as e:
                # Re-raise the exception to simulate real API error behavior
                raise e

        # Create an AsyncMock that captures all call arguments
        mock_request = AsyncMock(side_effect=mock_request_handler)

        with patch('pkg.client.PAPIClient.request', mock_request) as patched_request:
            yield patched_request

    @pytest_asyncio.fixture
    async def mcp_client(self):
        """Fixture providing an MCP client session connected to the test server."""

        # Patch the Cortex client to use our mock
        server = await initialize_mcp_server(self.mock_env_vars["CORTEX_MCP_PAPI_AUTH_HEADER"], self.mock_env_vars["CORTEX_MCP_PAPI_AUTH_ID"], self.mock_env_vars["CORTEX_MCP_PAPI_URL"])
        return Client(server)

    def assert_case_structure(self, case: dict[str, Any]):
        """Assert that case has expected structure."""
        required_fields = ["case_id", "severity", "status", "description", "created_time"]
        for field in required_fields:
            assert field in case, f"Missing required field: {field}"

    def assert_issue_structure(self, issue: dict[str, Any]):
        """Assert that issue has expected structure."""
        required_fields = ["id", "severity", "source", "description", "timestamp"]
        for field in required_fields:
            assert field in issue, f"Missing required field: {field}"

    def assert_assets_structure(self, asset: dict[str, Any]):
        """Assert that asset has expected structure."""
        required_fields = ["xdm.asset.id", "xdm.asset.type.id", "cases_critical", "xdm.asset.strong_id", "xdm.asset.first_observed"]
        for field in required_fields:
            assert field in asset, f"Missing required field: {field}"

    def assert_request_called_with(self, mock_request, expected_method: str,
                                   expected_url_pattern: str, **expected_kwargs):
        """Assert that the request method was called with expected parameters."""
        # Check if any call matches our expectations
        found_matching_call = False

        for call in mock_request.call_args_list:
            args, kwargs = call

            # args[0] is method, args[1] is url
            if len(args) >= 2:
                method, url = args[0], args[1]

                if method.upper() == expected_method.upper() and expected_url_pattern in url:
                    found_matching_call = True

                    # Check additional keyword arguments if provided
                    assert 'json' in kwargs

                    for key, expected_value in expected_kwargs.items():
                        if key in kwargs:
                            assert kwargs[key] == expected_value, \
                                f"Parameter {key}: expected {expected_value}, got {kwargs[key]}"
                    break

        assert found_matching_call, \
            f"No matching call found for {expected_method} with URL pattern '{expected_url_pattern}'"
