import json
import os

import pytest

from tests.e2e.base import CortexMCPE2ETestBase


class TestCortexMCPE2E(CortexMCPE2ETestBase):
    """Concrete e2e test class for Cortex MCP functionality."""

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test that MCP server exposes expected tools."""
        async with mcp_client:
            tools = await mcp_client.list_tools()

            expected_tools = [
                "get_issues",
                "get_cases",
                "get_assets",
            ]

            tool_names = [tool.name for tool in tools]

            for tool in expected_tools:
                assert tool in tool_names, f"Expected tool {tool} not found in {tools}"

    @pytest.mark.asyncio
    async def test_get_cases(self, mcp_client, mock_papi_request):
        """Test getting cases via MCP."""
        async with mock_papi_request:
            async with mcp_client:
                result = await mcp_client.call_tool("get_cases", arguments={"filters": []})

            assert result.is_error is False
            cases = json.loads(result.data)["reply"]

            assert len(cases) == 2
            for case in cases:
                self.assert_case_structure(case)

            # Verify mock was called
            self.assert_request_called_with(mock_papi_request, "POST", "/public_api/v1/case/search/")

    @pytest.mark.asyncio
    async def test_get_cases_error(self, mcp_client, mock_papi_request):
        """Test getting cases via MCP with error."""
        async with mock_papi_request:
            async with mcp_client:
                result = await mcp_client.call_tool("get_cases", arguments={"filters": [{"error": True}]})

            assert result.is_error is False
            res = json.loads(result.data)

            assert res["success"] == "false"
            assert res["error"] == "test"

    @pytest.mark.asyncio
    async def test_get_issues(self, mcp_client, mock_papi_request):
        """Test getting issues via MCP."""
        async with mock_papi_request:
            async with mcp_client:
                result = await mcp_client.call_tool("get_issues", arguments={"filters": []})

            assert result.is_error is False
            issues = json.loads(result.data)["reply"]

            assert len(issues) == 2
            for case in issues:
                self.assert_issue_structure(case)

            # Verify mock was called
            self.assert_request_called_with(mock_papi_request, "POST", "/public_api/v1/issue/search/")

    def test_environment_variables_loaded(self):
        """Test that mock environment variables are properly loaded."""
        assert os.getenv("CORTEX_MCP_PAPI_AUTH_HEADER") == "test-api-key-12345"
        assert os.getenv("CORTEX_MCP_PAPI_AUTH_ID") == "test-key-id-67890"
        assert os.getenv("CORTEX_MCP_PAPI_URL") == "test-cortex.example.com"
