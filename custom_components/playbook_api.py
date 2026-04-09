"""
XSOAR Playbook API Tools

Direct REST API tools for managing playbooks (get, insert, delete).
These use the REST API instead of the SDK for better performance and simplicity.
"""

import base64
import io
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


def _parse(data):
    if data is None:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return data


async def get_playbook(
    ctx: Context,
    filter: Annotated[Optional[dict | str], Field(description='Filter object with "field" (name or id) and "value"')] = None
) -> str:
    """
    Get a playbook by filtering based on its name or ID. The playbook's YAML is returned in a ZIP file.

    Use this to:
    - Download existing playbooks for backup
    - Export playbooks for version control
    - Retrieve playbook YAML for modification
    - Get playbook content for analysis

    You must have Instance Administrator permissions to run this endpoint.

    **WARNING:** This tool can return LARGE responses with detailed event data.
    For cases with many events, responses may be very large. Consider filtering
    by specific alert IDs rather than broad criteria to manage response size.

    Args:
        ctx: The FastMCP context.
        filter: Filter object with field ("name" or "id") and value.

    Returns:
        JSON response with playbook YAML content and metadata.
    """
    import requests

    filter = _parse(filter)
    if not filter:
        return create_response(data={"error": "filter is required. Example: {\"field\": \"name\", \"value\": \"My Playbook\"}"}, is_error=True)

    fetcher = await get_fetcher(ctx)

    request_data = {"request_data": {"filter": filter}}

    # Use requests library directly for binary ZIP response
    url = f"{fetcher.url}/public_api/v1/playbooks/get"
    headers = {
        "Authorization": fetcher.api_key,
        "x-xdr-auth-id": fetcher.api_key_id,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=request_data, headers=headers, verify=False)

        if response.status_code != 200:
            return create_response(
                data={
                    "error": f"API request failed: {response.status_code} - {response.text}",
                    "filter": filter
                },
                is_error=True
            )

        # Response is binary ZIP file
        zip_content = response.content
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # List files in ZIP
            file_list = zip_file.namelist()

            if not file_list:
                return create_response(
                    data={"error": "ZIP file is empty"},
                    is_error=True
                )

            # Find the YAML file (not metadata.json)
            yaml_files = [f for f in file_list if f.endswith(('.yml', '.yaml'))]
            yaml_filename = yaml_files[0] if yaml_files else file_list[0]
            yaml_content = zip_file.read(yaml_filename).decode('utf-8')

            return create_response(data={
                "playbook_name": filter.get("value"),
                "filter_field": filter.get("field"),
                "yaml_filename": yaml_filename,
                "yaml_content": yaml_content,
                "file_list": file_list,
                "size_bytes": len(zip_content),
                "success": True
            })

    except zipfile.BadZipFile:
        return create_response(
            data={
                "error": "Response is not a valid ZIP file",
                "filter": filter,
                "response_size": len(response)
            },
            is_error=True
        )
    except Exception as e:
        return create_response(
            data={
                "error": f"Failed to process playbook: {str(e)}",
                "filter": filter
            },
            is_error=True
        )


async def insert_playbook(
    ctx: Context,
    file: Annotated[str, Field(description="Path to ZIP file containing playbook YAML")]
) -> str:
    """
    Add or update a playbook by uploading the YAML in a ZIP file.

    Use this to:
    - Upload new playbooks to XSIAM
    - Update existing playbooks
    - Deploy playbooks from development to production
    - Restore playbooks from backup

    You must have Instance Administrator permissions to run this endpoint.

    **IMPORTANT - File Format:**
    - The playbook YAML must be inside a ZIP file
    - The ZIP file should contain the playbook YAML file
    - File name format: {PlaybookID}.yml (e.g., My_Playbook.yml)

    **Workflow:**
    1. Create or modify playbook YAML file
    2. Zip the YAML file: `zip playbook.zip My_Playbook.yml`
    3. Use this tool to upload the ZIP file
    4. Check response for success or errors

    **Note:** This tool uploads via multipart/form-data. The file parameter
    should be the path to the ZIP file on the local filesystem.

    Args:
        ctx: The FastMCP context.
        file: Path to ZIP file containing the playbook YAML.

    Returns:
        JSON response with upload status and any errors.
    """
    import aiohttp

    fetcher = await get_fetcher(ctx)

    # Validate file path - must be under home directory or /tmp
    allowed_bases = [Path.home(), Path("/tmp")]
    resolved = Path(file).resolve()
    if not any(str(resolved).startswith(str(base)) for base in allowed_bases):
        return create_response(
            data={"error": f"File path must be under home directory or /tmp: {file}"},
            is_error=True
        )

    # Read the ZIP file
    try:
        with open(file, 'rb') as f:
            zip_data = f.read()
    except FileNotFoundError:
        return create_response(
            data={"error": f"File not found: {file}"},
            is_error=True
        )
    except Exception as e:
        return create_response(
            data={"error": f"Failed to read file: {str(e)}"},
            is_error=True
        )

    # Upload via multipart/form-data using aiohttp directly
    url = f"{fetcher.url}/public_api/v1/playbooks/insert"
    headers = {
        "Authorization": fetcher.api_key,
        "x-xdr-auth-id": fetcher.api_key_id
    }

    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('file', zip_data, filename='playbook.zip', content_type='application/zip')

            async with session.post(url, data=form, headers=headers, ssl=False) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return create_response(
                        data={"error": f"Upload failed: {resp.status} - {error_text}"},
                        is_error=True
                    )

                # Try JSON first, fall back to text
                try:
                    response = await resp.json()
                except:
                    response_text = await resp.text()
                    # API might return plain "success" text
                    if "success" in response_text.lower():
                        return create_response(data={
                            "success": True,
                            "message": "Playbook uploaded successfully",
                            "response": response_text
                        })
                    else:
                        return create_response(
                            data={"error": f"Unexpected response: {response_text[:500]}"},
                            is_error=True
                        )

                # If we got a dict response, check for failures
                if isinstance(response, dict):
                    failures = response.get("objects", {}).get("failures_items", [])
                else:
                    # String response - treat as success if it says "success"
                    if "success" in str(response).lower():
                        return create_response(data={
                            "success": True,
                            "message": "Playbook uploaded successfully",
                            "response": response
                        })
                    failures = []

                if failures:
                    return create_response(
                        data={
                            "success": False,
                            "objects_count": response.get("objects_count"),
                            "failures": failures,
                            "error": "Some playbooks failed to upload"
                        },
                        is_error=True
                    )

                return create_response(data={
                    "success": True,
                    "objects_count": response.get("objects_count"),
                    "message": f"Successfully uploaded {response.get('objects_count')} playbook(s)"
                })

    except Exception as e:
        return create_response(
            data={"error": f"Upload failed: {str(e)}"},
            is_error=True
        )


async def delete_playbook(
    ctx: Context,
    filter: Annotated[Optional[dict | str], Field(description='Filter object with "field" (name or id) and "value"')] = None
) -> str:
    """
    Delete a playbook by filtering based on its name or ID.

    Use this to:
    - Remove obsolete playbooks
    - Clean up test playbooks
    - Manage playbook inventory

    You must have Instance Administrator permissions to run this endpoint.

    **WARNING:** This is a destructive operation. Deleted playbooks cannot be recovered
    unless you have a backup. Consider using get_playbook to download a backup first.

    Args:
        ctx: The FastMCP context.
        filter: Filter object with field ("name" or "id") and value.

    Returns:
        JSON response with deletion status.
    """
    filter = _parse(filter)
    if not filter:
        return create_response(data={"error": "filter is required. Example: {\"field\": \"name\", \"value\": \"My Playbook\"}"}, is_error=True)

    fetcher = await get_fetcher(ctx)

    request_data = {"request_data": {"filter": filter}}

    response = await fetcher.send_request(
        path="/public_api/v1/playbooks/delete",
        method="POST",
        data=request_data
    )

    return create_response(data={
        "success": True,
        "filter": filter,
        "message": f"Playbook deleted successfully",
        "response": response
    })


class PlaybookAPIModule(BaseModule):
    """
    MCP module for managing XSOAR playbooks via REST API.

    Provides tools to:
    - Download playbooks (get)
    - Upload/update playbooks (insert)
    - Delete playbooks (delete)

    Uses REST API directly (preferred over SDK for playbook operations).
    """

    def register_tools(self):
        self._add_tool(get_playbook)
        self._add_tool(insert_playbook)
        self._add_tool(delete_playbook)

    def register_resources(self):
        """Playbook API module doesn't register resources."""
        pass
