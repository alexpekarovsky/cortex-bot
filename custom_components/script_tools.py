"""Script execution tools — migrated from OpenAPI YAML to Python."""
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
from usecase.custom_components.destructive_gate import register_destructive
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


async def _script_call(ctx, path, data, tool_name):
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


async def run_script(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Script execution parameters. Use {"script_uid": "<uid>", '
                    '"timeout": 600, "filters": [{"field": "endpoint_id_list", '
                    '"operator": "in", "value": ["<endpoint_id>"]}], '
                    '"parameters_values": {}} format.'
    )] = None,
) -> str:
    """DESTRUCTIVE: Runs a script on one or more endpoints. Use get_scripts to find script UIDs."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/run_script/",
                              {"request_data": request_data}, "run_script")


async def run_snippet_code_script(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Snippet code to run. Use {"filters": [{"field": "endpoint_id_list", '
                    '"operator": "in", "value": ["<endpoint_id>"]}], '
                    '"snippet_code": "<python_code>"} format.'
    )] = None,
) -> str:
    """DESTRUCTIVE: Runs a Python code snippet directly on endpoints."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/run_snippet_code_script",
                              {"request_data": request_data}, "run_snippet_code_script")


async def get_scripts(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Filters for scripts. Use {"filters": [{"field": "name", '
                    '"operator": "contains", "value": "<search>"}]} or empty for all.'
    )] = None,
) -> str:
    """Lists available scripts that can be run on endpoints."""
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/get_scripts",
                              {"request_data": request_data or {}}, "get_scripts")


async def get_script_metadata(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Script to get metadata for. Use {"script_uid": "<uid>"} format.'
    )] = None,
) -> str:
    """Gets detailed metadata for a specific script including parameters."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/get_script_metadata",
                              {"request_data": request_data}, "get_script_metadata")


async def get_script_execution_status(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Action ID to check. Use {"action_id": "<id>"} format.'
    )] = None,
) -> str:
    """Gets the execution status of a previously run script."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/get_script_execution_status",
                              {"request_data": request_data}, "get_script_execution_status")


async def get_script_execution_results(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Action ID to get results for. Use {"action_id": "<id>"} format.'
    )] = None,
) -> str:
    """Gets the results of a completed script execution."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _script_call(ctx, "/public_api/v1/scripts/get_script_execution_results",
                              {"request_data": request_data}, "get_script_execution_results")


class ScriptToolsModule(BaseModule):
    """Script execution: run, snippet, list, metadata, status, results."""
    def register_tools(self):
        register_destructive(self, run_script, run_snippet_code_script)
        self._add_tool(get_scripts)
        self._add_tool(get_script_metadata)
        self._add_tool(get_script_execution_status)
        self._add_tool(get_script_execution_results)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
