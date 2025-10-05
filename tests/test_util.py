"""Tests for utility functions in cortex-mcp."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import ValidationError

from src.pkg.util import (
    RESOURCES_DIR,
    create_response,
    get_papi_auth_headers,
    get_papi_url,
    read_file,
    read_resource,
)


def _validate_bundled_openapi_spec(spec):
    """Validate that a given spec conforms to OpenAPI 3.0+ requirements."""
    # Basic structure validation
    assert isinstance(spec, dict), "OpenAPI spec must be a dictionary"
    assert "openapi" in spec, "OpenAPI spec must have openapi version field"
    assert spec["openapi"].startswith("3."), f"Must be OpenAPI 3.x, got {spec.get('openapi')}"
    assert "info" in spec, "OpenAPI spec must have info section"
    assert "paths" in spec, "OpenAPI spec must have paths section"

    # Info section validation
    info = spec["info"]
    assert isinstance(info, dict), "Info must be a dictionary"
    assert "title" in info, "Info section must have title"
    assert "version" in info, "Info section must have version"
    assert isinstance(info["title"], str), "Title must be a string"
    assert isinstance(info["version"], str), "Version must be a string"

    # Paths validation
    paths = spec["paths"]
    assert isinstance(paths, dict), "Paths must be a dictionary"

    # Each path should start with / (when not empty)
    for path_key in paths.keys():
        if path_key:  # Skip empty keys
            assert isinstance(path_key, str), f"Path key must be string, got {type(path_key)}"
            assert path_key.startswith("/"), f"Path {path_key} must start with /"

def _validate_single_openapi_spec(spec):
    """Validate that a given single spec conforms to OpenAPI 3.0+ requirements."""
    # Basic structure validation
    assert isinstance(spec, dict), "OpenAPI spec must be a dictionary"
    assert "openapi" in spec, "OpenAPI spec must have openapi version field"
    assert spec["openapi"].startswith("3."), f"Must be OpenAPI 3.x, got {spec.get('openapi')}"
    assert "paths" in spec, "OpenAPI spec must have paths section"

    # Paths validation
    paths = spec["paths"]
    assert isinstance(paths, dict), "Paths must be a dictionary"

    # Each path should start with / (when not empty)
    for path_key in paths.keys():
        if path_key:  # Skip empty keys
            assert isinstance(path_key, str), f"Path key must be string, got {type(path_key)}"
            assert path_key.startswith("/"), f"Path {path_key} must start with /"


class TestOpenAPIBundling:
    """Test cases for OpenAPI bundling functionality."""

    def test_usecase_directory_exists_and_has_specs(self, all_usecase_folders, individual_openapi_specs):
        """Test that usecase directory exists and contains OpenAPI specs."""
        for usecase_dir in all_usecase_folders:
            assert usecase_dir.exists(), "usecase directory should exist"
            assert usecase_dir.is_dir(), "usecase should be a directory"

        assert len(individual_openapi_specs) > 0, "Should find at least one OpenAPI spec"

        print(f"Found {len(individual_openapi_specs)} OpenAPI specs in usecase directory")

        # List some examples
        spec_names = list(individual_openapi_specs.keys())[:5]
        print(f"Example specs: {spec_names}")

    def test_bundle_openapi_from_folders_with_usecase_specs(self, all_usecase_folders):
        """Test bundle_openapi_from_folders with real usecase OpenAPI specs."""
        # Try to import the real function first
        from src.pkg.util import bundle_openapi_from_folders
        # Test with real usecase folders
        result = bundle_openapi_from_folders()

        # Verify the result is a valid OpenAPI spec
        _validate_bundled_openapi_spec(result)

        # Basic structure checks
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

        # Verify OpenAPI version
        assert result["openapi"].startswith("3.")

        print(f"Successfully bundled {len(all_usecase_folders)} OpenAPI specs")
        print(f"Resulting spec has {len(result.get('paths', {}))} paths")

    def test_bundle_openapi_preserves_individual_spec_validity(self, individual_openapi_specs):
        """Test that individual specs from usecase directory are valid before bundling."""
        valid_specs = 0
        invalid_specs = []

        for name, spec_data in individual_openapi_specs.items():
            try:
                _validate_single_openapi_spec(spec_data["spec"])
                valid_specs += 1
            except (ValidationError, AssertionError) as e:
                invalid_specs.append((name, str(e)))

        # Report findings
        print(f"Valid specs: {valid_specs}")
        print(f"Invalid specs: {len(invalid_specs)}")

        if invalid_specs:
            print("Invalid specs found:")
            for name, error in invalid_specs[:5]:  # Show first 5
                print(f"  {name}: {error}")

        # Most specs should be valid
        total_specs = len(individual_openapi_specs)
        if total_specs > 0:
            valid_ratio = valid_specs / total_specs
            assert valid_ratio > 0.7, f"At least 70% of specs should be valid, got {valid_ratio:.2%}"

    def test_bundle_openapi_empty_folder_list(self):
        """Test bundling with empty folder list."""
        from src.pkg.util import bundle_openapi_files
        result = bundle_openapi_files()

        _validate_bundled_openapi_spec(result)

        # Should create a minimal valid spec
        assert result["paths"] == {}
        assert result["info"]["title"]
        assert result["info"]["version"]


class TestCreateResponse:
    """Test cases for create_response function."""

    def test_create_response_success(self):
        """Test creating a successful response."""
        data = {"message": "Operation completed", "count": 5}
        result = create_response(data)

        parsed_result = json.loads(result)
        assert parsed_result["message"] == "Operation completed"
        assert parsed_result["count"] == 5
        assert parsed_result["success"] == "true"

    def test_create_response_error(self):
        """Test creating an error response."""
        data = {"error": "Invalid input", "code": 400}
        result = create_response(data, is_error=True)

        parsed_result = json.loads(result)
        assert parsed_result["error"] == "Invalid input"
        assert parsed_result["code"] == 400
        assert parsed_result["success"] == "false"

    def test_create_response_empty_data(self):
        """Test creating response with empty data."""
        data = {}
        result = create_response(data)

        parsed_result = json.loads(result)
        assert parsed_result["success"] == "true"
        assert len(parsed_result) == 1

    def test_create_response_unicode_characters(self):
        """Test creating response with unicode characters."""
        data = {"message": "操作完成", "emoji": "✅"}
        result = create_response(data)

        parsed_result = json.loads(result)
        assert parsed_result["message"] == "操作完成"
        assert parsed_result["emoji"] == "✅"
        assert parsed_result["success"] == "true"

    def test_create_response_formatting(self):
        """Test that response is properly formatted with indentation."""
        data = {"key": "value"}
        result = create_response(data)

        # Check that the result contains proper indentation
        assert "{\n" in result
        assert "  " in result  # 2-space indentation
        assert result.endswith("\n}")


class TestReadFile:
    """Test cases for read_file function."""

    def test_read_file_success(self):
        """Test successfully reading a file."""
        content = "Hello, World!"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text(content)

            result = read_file("test.txt", temp_path)
            assert result == content

    def test_read_file_subdirectory(self):
        """Test reading a file from a subdirectory."""
        content = "Subdirectory content"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            test_file = sub_dir / "test.txt"
            test_file.write_text(content)

            result = read_file("subdir/test.txt", temp_path)
            assert result == content

    def test_read_file_path_traversal_attack(self):
        """Test that path traversal attacks are prevented."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(ValueError, match="Invalid file path: path traversal detected"):
                read_file("../../../etc/passwd", temp_path)

    def test_read_file_path_traversal_with_dots(self):
        """Test various path traversal patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            traversal_patterns = [
                "../outside.txt",
                "../../outside.txt",
                "subdir/../../../outside.txt",
                "subdir/../../outside.txt"
            ]

            for pattern in traversal_patterns:
                with pytest.raises(ValueError, match="Invalid file path: path traversal detected"):
                    read_file(pattern, temp_path)

    def test_read_file_not_found(self):
        """Test handling of non-existent files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(FileNotFoundError, match="Resource file not found: nonexistent.txt"):
                read_file("nonexistent.txt", temp_path)

    def test_read_file_permission_error(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("content")

            # Mock the file opening to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(PermissionError, match="Access denied to resource file: test.txt"):
                    read_file("test.txt", temp_path)

    def test_read_file_unicode_decode_error(self):
        """Test handling of unicode decode errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "binary.txt"

            # Write binary content that can't be decoded as UTF-8
            with open(test_file, "wb") as f:
                f.write(b'\x80\x81\x82\x83')

            with pytest.raises(ValueError, match="Unable to decode file binary.txt"):
                read_file("binary.txt", temp_path)


class TestReadResource:
    """Test cases for read_resource function."""

    @patch('src.pkg.util.read_file')
    def test_read_resource_calls_read_file(self, mock_read_file):
        """Test that read_resource calls read_file with correct arguments."""
        mock_read_file.return_value = "mocked content"

        result = read_resource("test.txt")

        mock_read_file.assert_called_once_with("test.txt", RESOURCES_DIR)
        assert result == "mocked content"

    @patch('src.pkg.util.read_file')
    def test_read_resource_propagates_exceptions(self, mock_read_file):
        """Test that read_resource propagates exceptions from read_file."""
        mock_read_file.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError, match="File not found"):
            read_resource("nonexistent.txt")


class TestGetPapiAuthHeaders:
    """Test cases for get_papi_auth_headers function."""

    def test_get_papi_auth_headers_success(self):
        """Test generating authentication headers."""
        api_key = "test-api-key-123"
        api_key_id = "test-key-id-456"

        result = get_papi_auth_headers(api_key, api_key_id)

        expected = {
            "Authorization": api_key,
            "X-XDR-AUTH-ID": api_key_id,
        }
        assert result == expected

    def test_get_papi_auth_headers_empty_values(self):
        """Test generating headers with empty values."""
        result = get_papi_auth_headers("", "")

        expected = {
            "Authorization": "",
            "X-XDR-AUTH-ID": "",
        }
        assert result == expected

    def test_get_papi_auth_headers_special_characters(self):
        """Test generating headers with special characters."""
        api_key = "key-with-special-chars!@#$%"
        api_key_id = "id-with-dashes-and_underscores"

        result = get_papi_auth_headers(api_key, api_key_id)

        expected = {
            "Authorization": api_key,
            "X-XDR-AUTH-ID": api_key_id,
        }
        assert result == expected


class TestGetPapiUrl:
    """Test cases for get_papi_url function."""

    def test_get_papi_url_with_https(self):
        """Test URL construction with existing HTTPS."""
        url = "https://example.com"
        result = get_papi_url(url)
        assert result == "https://api-example.com"

    def test_get_papi_url_with_http(self):
        """Test URL construction with HTTP (should convert to HTTPS)."""
        url = "http://example.com"
        result = get_papi_url(url)
        assert result == "https://api-example.com"

    def test_get_papi_url_without_protocol(self):
        """Test URL construction without protocol."""
        url = "example.com"
        result = get_papi_url(url)
        assert result == "https://api-example.com"

    def test_get_papi_url_with_existing_api_prefix(self):
        """Test URL that already has api- prefix."""
        url = "https://api-example.com"
        result = get_papi_url(url)
        assert result == "https://api-example.com"

    def test_get_papi_url_with_subdomain(self):
        """Test URL with existing subdomain."""
        url = "https://subdomain.example.com"
        result = get_papi_url(url)
        assert result == "https://api-subdomain.example.com"

    def test_get_papi_url_empty_value(self):
        """Test URL construction with empty value."""
        with pytest.raises(ValueError, match="No public API URL provided"):
            get_papi_url("")

    def test_get_papi_url_none_value(self):
        """Test URL construction with None value."""
        with pytest.raises(ValueError, match="No public API URL provided"):
            get_papi_url(None)

    def test_get_papi_url_with_path(self):
        """Test URL construction with path."""
        url = "https://example.com/some/path"
        result = get_papi_url(url)
        assert result == "https://api-example.com/some/path"

    def test_get_papi_url_with_port(self):
        """Test URL construction with port."""
        url = "https://example.com:8080"
        result = get_papi_url(url)
        assert result == "https://api-example.com:8080"

    def test_get_papi_url_complex_case(self):
        """Test URL construction with complex case."""
        url = "http://subdomain.example.com:8080/api/v1"
        result = get_papi_url(url)
        assert result == "https://api-subdomain.example.com:8080/api/v1"
