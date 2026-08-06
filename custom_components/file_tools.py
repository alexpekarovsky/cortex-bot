"""File operations tools — migrated from OpenAPI YAML to Python."""
import json
import logging
from typing import Annotated, Optional, Union

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError, PAPIClientError, PAPIClientRequestError,
    PAPIConnectionError, PAPIResponseError, PAPIServerError,
)
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)

PAPI_ERRORS = (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
               PAPIClientRequestError, PAPIResponseError, PAPIClientError)


def _parse(data):
    if data is None:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return data


async def _file_call(ctx, path, data, tool_name):
    try:
        fetcher = await get_fetcher(ctx)
        omit = "/public_api/" in path
        resp = await fetcher.send_request(path=path, method="POST", data=data, omit_papi_prefix=omit)
        return create_response(data=resp)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"{tool_name} failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def quarantine_files(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Files to quarantine. Use {"filters": [{"field": "endpoint_id_list", '
                    '"operator": "in", "value": ["<endpoint_id>"]}], '
                    '"file_path": "<path>", "file_hash": "<sha256>"} format.'
    )] = None,
    confirm_destructive_action: Annotated[bool, Field(
        description="REQUIRED: Must be True. Quarantines files on endpoints."
    )] = False,
) -> str:
    """DESTRUCTIVE: Quarantines files on endpoints. Reversible with restore_file."""
    if not confirm_destructive_action:
        return create_response(
            data={
                "error": "Destructive action not confirmed",
                "message": "This quarantines files on endpoints. "
                           "Set confirm_destructive_action=True to proceed.",
                "risk_level": "HIGH",
                "reversible": True
            },
            is_error=True
        )
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _file_call(ctx, "/public_api/v1/endpoints/quarantine/",
                            {"request_data": request_data}, "quarantine_files")


async def retrieve_files(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Files to retrieve. Use {"filters": [{"field": "endpoint_id_list", '
                    '"operator": "in", "value": ["<endpoint_id>"]}], '
                    '"files": {"<os_type>": ["<file_path>"]}} format. '
                    'os_type: windows, linux, macos.'
    )] = None,
) -> str:
    """Retrieves files from endpoints for forensic analysis."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _file_call(ctx, "/public_api/v1/endpoints/file_retrieval/",
                            {"request_data": request_data}, "retrieve_files")


async def get_file_retrieval_details(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Action ID from a file retrieval. Use {"group_action_id": <action_id>} format.'
    )] = None,
) -> str:
    """Gets details of a file retrieval action including download link."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _file_call(ctx, "/public_api/v1/actions/file_retrieval_details",
                            {"request_data": request_data}, "get_file_retrieval_details")


async def get_quarantine_status(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Query quarantine status. Use {"files": [{"endpoint_id": "<id>", '
                    '"file_path": "<path>", "file_hash": "<sha256>"}]} format.'
    )] = None,
) -> str:
    """Gets the quarantine status of files on endpoints."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _file_call(ctx, "/public_api/v1/quarantine/status",
                            {"request_data": request_data}, "get_quarantine_status")


class FileToolsModule(BaseModule):
    """File operations: quarantine, retrieve, status, retrieval details."""
    def register_tools(self):
        self._add_tool(quarantine_files)
        self._add_tool(retrieve_files)
        self._add_tool(get_file_retrieval_details)
        self._add_tool(get_quarantine_status)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
