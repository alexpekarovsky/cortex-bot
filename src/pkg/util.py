import json
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RESOURCES_DIR = SCRIPT_DIR / "resources"

logger = logging.getLogger("Cortex MCP")

def create_response_and_report(data: dict, is_error: bool = False) -> str:
    success = "true" if not is_error else "false"
    data["success"] = success
    return json.dumps(data, indent=2, ensure_ascii=False)


def get_dataset_name(query) -> str | None:
    """Extract the dataset name from an XQL query."""
    parts = query.split("|")
    for part in parts:
        if "dataset" in part.lower():
            dataset_part = part.strip().split("=")
            if len(dataset_part) == 2:
                return dataset_part[1].strip()
    return None

def read_file(file_path: str) -> str:
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
