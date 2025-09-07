import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RESOURCES_DIR = SCRIPT_DIR / "resources"

def create_response(data: dict, is_error: bool = False) -> str:
    """
    Create a JSON response with success status indicator.

    This function takes a dictionary of data and adds a success field to indicate
    whether the operation was successful or resulted in an error. The response
    is returned as a formatted JSON string.

    Args:
        data (dict): The data dictionary to include in the response.
        is_error (bool, optional): Flag indicating if this is an error response.
                                 Defaults to False.

    Returns:
        str: A JSON string containing the data with an added 'success' field.
             The JSON is formatted with 2-space indentation and non-ASCII
             characters are preserved.

    Example:
        >>> data = {"message": "Operation completed", "count": 5}
        >>> create_response(data)
        '{\n  "message": "Operation completed",\n  "count": 5,\n  "success": "true"\n}'

        >>> error_data = {"error": "Invalid input"}
        >>> create_response(error_data, is_error=True)
        '{\n  "error": "Invalid input",\n  "success": "false"\n}'
    """
    success = "true" if not is_error else "false"
    data["success"] = success
    return json.dumps(data, indent=2, ensure_ascii=False)

def read_file(file_path: str) -> str:
    """
    Safely read a file from the resources directory.

    This function reads a file from the predefined resources directory with
    security measures to prevent path traversal attacks. The file path is
    validated to ensure it stays within the resources directory boundary.

    Args:
        file_path (str): Relative path to the file within the resources directory.
                        Must not contain path traversal sequences like '../'.

    Returns:
        str: The contents of the file as a string.

    Raises:
        ValueError: If path traversal is detected in the file path or if the
                   file cannot be decoded as valid Unicode text.
        FileNotFoundError: If the specified file does not exist in the
                          resources directory.
        PermissionError: If access is denied to the specified file due to
                        insufficient permissions.

    Example:
        >>> content = read_file("config.json")
        >>> print(content)
        # Contents of src/pkg/resources/config.json

        >>> read_file("../../../etc/passwd")  # This will raise ValueError
        ValueError: Invalid file path: path traversal detected

    Security:
        - Prevents path traversal attacks by validating the resolved path
        - Only allows access to files within the resources directory
        - Handles encoding errors gracefully
    """
    try:
        full_path = (RESOURCES_DIR / file_path).resolve()
        if not str(full_path).startswith(str(RESOURCES_DIR.resolve())):
            raise ValueError("Invalid file path: path traversal detected")

        with open(full_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Resource file not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Access denied to resource file: {file_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Unable to decode file {file_path}: {e}")
