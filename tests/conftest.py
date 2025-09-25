"""Pytest configuration and fixtures for cortex-mcp tests."""


import tempfile
import shutil
import yaml
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock, Mock
from fastmcp import Context, FastMCP

from src.usecase.fetcher import Fetcher
from src.entities.MCPContext import MCPContext

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def all_usecase_folders() -> list[Path]:
    """Get a sample of usecase folders containing OpenAPI specs."""
    # Get folders that contain openapi.json files
    from pkg.util import BUILTINS_DIR, CUSTOM_DIR, REMOTE_DIR

    return [BUILTINS_DIR, CUSTOM_DIR, REMOTE_DIR]

@pytest.fixture
def individual_openapi_specs(all_usecase_folders):
    """Load individual OpenAPI specs for detailed testing."""
    specs = {}

    for folder in all_usecase_folders:
        if folder.is_dir():
            spec = None
            spec_file = None

            # Look for any .yaml files recursively
            for file_path in folder.rglob('*.yaml'):
                if file_path and file_path.is_file():
                    try:
                        with open(file_path, 'r') as f:
                            spec = yaml.safe_load(f)
                        spec_file = file_path
                        break  # Use the first valid YAML file found
                    except (yaml.YAMLError, IOError, ImportError):
                        continue

            if spec is not None:
                specs[folder.name] = {
                    "path": spec_file,
                    "folder": folder,
                    "spec": spec
                }

    return specs


@pytest.fixture
def mock_api_credentials():
    """Fixture providing mock API credentials."""
    return {
        "url": "https://api.example.com",
        "api_key": "test_api_key",
        "api_key_id": "test_api_key_id"
    }


@pytest.fixture
def fetcher_instance(mock_api_credentials):
    """Fixture providing a Fetcher instance with mock credentials."""
    return Fetcher(
        url=mock_api_credentials["url"],
        api_key=mock_api_credentials["api_key"],
        api_key_id=mock_api_credentials["api_key_id"]
    )


@pytest.fixture
def mock_auth_headers():
    """Fixture providing mock authentication headers."""
    return {
        "Authorization": "Bearer test_token",
        "X-XDR-AUTH-ID": "test_xdr_id"
    }


@pytest.fixture
def mock_lifespan_context_with_auth(mock_auth_headers):
    """Fixture providing a mock MCPContext with authentication headers."""
    mock_lifespan = MagicMock(spec=MCPContext)
    mock_lifespan.auth_headers = mock_auth_headers.copy()
    return mock_lifespan


@pytest.fixture
def mock_lifespan_context_empty():
    """Fixture providing a mock MCPContext with empty authentication headers."""
    mock_lifespan = MagicMock(spec=MCPContext)
    mock_lifespan.auth_headers = {}
    return mock_lifespan


@pytest.fixture
def mock_lifespan_context_partial():
    """Fixture providing a mock MCPContext with partial authentication headers."""
    mock_lifespan = MagicMock(spec=MCPContext)
    mock_lifespan.auth_headers = {
        "Authorization": "Bearer partial_token"
        # Missing X-XDR-AUTH-ID
    }
    return mock_lifespan


@pytest.fixture
def mock_fastmcp_context(mock_lifespan_context_with_auth):
    """Fixture providing a mock FastMCP Context with lifespan context."""
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = mock_lifespan_context_with_auth

    mock_context = MagicMock(spec=Context)
    mock_context.request_context = mock_request_context
    mock_context.set_state = MagicMock()

    return mock_context


@pytest.fixture
def mock_fastmcp_context_empty_auth(mock_lifespan_context_empty):
    """Fixture providing a mock FastMCP Context with empty auth."""
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = mock_lifespan_context_empty

    mock_context = MagicMock(spec=Context)
    mock_context.request_context = mock_request_context
    mock_context.set_state = MagicMock()

    return mock_context


@pytest.fixture
def mock_fastmcp_context_partial_auth(mock_lifespan_context_partial):
    """Fixture providing a mock FastMCP Context with partial auth."""
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = mock_lifespan_context_partial

    mock_context = MagicMock(spec=Context)
    mock_context.request_context = mock_request_context
    mock_context.set_state = MagicMock()

    return mock_context


@pytest.fixture
def mock_papi_client():
    """Fixture providing a mock PAPIClient."""
    mock_client_instance = AsyncMock()
    mock_client_instance.request = AsyncMock()
    return mock_client_instance


@pytest.fixture
def mock_api_response():
    """Fixture providing a mock API response."""
    return {
        "status": "success",
        "data": {
            "id": 123,
            "message": "Test response"
        }
    }


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration values."""
    return {
        "papi_url_env_key": "PAPI_URL",
        "papi_auth_header_key": "PAPI_AUTH_HEADER",
        "papi_auth_id_key": "PAPI_AUTH_ID"
    }


@pytest.fixture
def environment_variables():
    """Fixture providing environment variable values for testing."""
    return {
        "PAPI_URL": "https://env.api.example.com",
        "PAPI_AUTH_HEADER": "env_api_key",
        "PAPI_AUTH_ID": "env_auth_id"
    }


@pytest.fixture
def api_request_data():
    """Fixture providing sample API request data."""
    return {
        "path": "/test/endpoint",
        "method": "POST",
        "data": {"key": "value", "param": "test"},
        "headers": {"Custom-Header": "custom_value"}
    }


@pytest.fixture
def api_paths():
    """Fixture providing various API path scenarios for testing."""
    return {
        "simple_path": "/test/endpoint",
        "path_without_leading_slash": "test/endpoint",
        "path_with_prefix": "/public_api/v1/already/prefixed",
        "path_with_prefix_slash": "/public_api/v1/already/prefixed",
        "raw_path": "/custom/raw/endpoint"
    }


@pytest.fixture
def expected_prefixed_paths(api_paths):
    """Fixture providing expected paths after prefix processing."""
    return {
        "simple_path": "/public_api/v1/test/endpoint",
        "path_without_leading_slash": "/public_api/v1/test/endpoint",
        "path_with_prefix": "/public_api/v1/already/prefixed",
        "path_with_prefix_slash": "/public_api/v1/already/prefixed",
        "raw_path": "/custom/raw/endpoint"  # When omit_papi_prefix=True
    }


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance"""
    return Mock(spec=FastMCP)


@pytest.fixture
def temp_module_file():
    """Create a temporary Python file with a mock module"""
    content = '''
from fastmcp import FastMCP
from src.usecase.base_module import BaseModule

class TestModule(BaseModule):
    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
        self.register_tools_called = False
        self.register_resources_called = False

    def register_tools(self):
        self.register_tools_called = True

    def register_resources(self):
        self.register_resources_called = True

class NotABaseModule:
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


@pytest.fixture
def temp_directory_with_modules():
    """Create a temporary directory with multiple Python files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a valid module file
        valid_module = temp_path / "valid_module.py"
        valid_module.write_text('''
from fastmcp import FastMCP
from src.usecase.base_module import BaseModule

class ValidModule(BaseModule):
    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)

    def register_tools(self):
        pass

    def register_resources(self):
        pass
''')

        # Create an __init__.py file (should be skipped)
        init_file = temp_path / "__init__.py"
        init_file.write_text("# Init file")

        # Create a file with syntax error
        invalid_module = temp_path / "invalid_module.py"
        invalid_module.write_text("invalid python syntax $$$ !!!")

        # Create a subdirectory with a module
        subdir = temp_path / "subdir"
        subdir.mkdir()
        sub_module = subdir / "sub_module.py"
        sub_module.write_text('''
from fastmcp import FastMCP
from src.usecase.base_module import BaseModule

class SubModule(BaseModule):
    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)

    def register_tools(self):
        pass

    def register_resources(self):
        pass
''')

        yield temp_path


