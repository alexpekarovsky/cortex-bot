from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from fastmcp import FastMCP
from src.usecase.module_util import (
    discover_and_register_modules,
)
from tests.mock_modules.module1 import MockModule
from tests.mock_modules.module2 import AnotherMockModule


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance for testing"""
    return Mock(spec=FastMCP)


class TestDiscoverAndRegisterModules:
    """Test cases for discover_and_register_modules function"""

    @patch('src.usecase.module_util.BUILTINS_DIR')
    @patch('src.usecase.module_util.CUSTOM_DIR')
    @patch('src.usecase.module_util.REMOTE_DIR')
    def test_discover_and_register_modules(
            self, mock_remote_dir, mock_custom_dir, mock_builtins_dir, mock_mcp
    ):
        """Test discovery when all directories exist"""
        mock_dir = Path(__file__).parent / "mock_modules"

        # Setup mocks
        mock_builtins_dir.exists.return_value = True
        mock_custom_dir.exists.return_value = True
        mock_remote_dir.exists.return_value = True
        mock_builtins_dir.rglob.return_value = mock_dir.rglob("*.py")

        mock_module1 = MockModule(mock_mcp)
        mock_module2 = AnotherMockModule(mock_mcp)

        # Execute
        result = discover_and_register_modules(mock_mcp)

        # Verify
        assert len(result) == 2
        module_names = [type(module).__name__ for module in result]
        assert type(mock_module1).__name__ in module_names
        assert type(mock_module2).__name__ in module_names

        module = result[0]
        assert module.register_tools_called is True
        assert module.register_resources_called is True

    @patch('src.usecase.module_util.BUILTINS_DIR')
    @patch('src.usecase.module_util.CUSTOM_DIR')
    @patch('src.usecase.module_util.REMOTE_DIR')
    def test_discover_and_register_modules_empty_directories(self, mock_remote_dir, mock_custom_dir, mock_builtins_dir, mock_mcp):
        """Test discovery when all directories exist but are empty"""

        mock_builtins_dir.exists.return_value = True
        mock_custom_dir.exists.return_value = True
        mock_remote_dir.exists.return_value = True

        with patch('src.usecase.module_util._discover_modules_in_directory') as mock_discover:
            mock_discover.return_value = []

            result = discover_and_register_modules(mock_mcp)

            assert len(result) == 0
            assert mock_discover.call_count == 3


class TestModuleRegistration:
    """Enhanced tests for module registration behavior"""

    def test_modules_registration_state_tracking(self, mock_mcp):
        """Test detailed registration state tracking"""
        module1 = MockModule(mock_mcp)
        module2 = AnotherMockModule(mock_mcp)

        # Test initial state
        assert not module1.register_tools_called
        assert not module1.register_resources_called
        assert not module2.register_tools_called
        assert not module2.register_resources_called

        # Test partial registration
        module1.register_tools()
        assert module1.register_tools_called
        assert not module1.register_resources_called

        # Test full registration
        module1.register_resources()
        module2.register_tools()
        module2.register_resources()

        assert module1.register_tools_called
        assert module1.register_resources_called
        assert module2.register_tools_called
        assert module2.register_resources_called

    def test_modules_mcp_instance_consistency(self, mock_mcp):
        """Test that all modules maintain consistent MCP reference"""
        modules = [
            MockModule(mock_mcp),
            AnotherMockModule(mock_mcp)
        ]

        for module in modules:
            assert module.mcp is mock_mcp
            # Test that mcp reference doesn't change
            original_mcp = module.mcp
            module.register_tools()
            assert module.mcp is original_mcp
