"""Endpoint management tools — migrated from OpenAPI YAML to Python."""
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


async def _endpoint_call(ctx, path, data, tool_name):
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


async def get_endpoints(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description="Filters for endpoint search. Keys: filters (array of {field, operator, value}), "
                    "search_from (int), search_to (int). Fields: endpoint_id, hostname, ip_address, "
                    "endpoint_status, os_type, domain. Operators: in, contains. Empty = all endpoints."
    )] = None,
) -> str:
    """Retrieves detailed information about endpoints in your environment.
    Returns endpoint ID, hostname, OS, IP addresses, agent status, isolation status, and more.
    Use this to identify endpoints for incident response or check agent connectivity."""
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/get_endpoints/",
                                {"request_data": request_data or {}}, "get_endpoints")


async def get_filtered_endpoints(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description="Filter criteria. Keys: filters (array), search_from, search_to, sort. "
                    "Filter fields: endpoint_id_list, dist_name, first_seen, last_seen, ip_list, "
                    "group_name, platform, alias, isolate, hostname, username, public_ip_list, scan_status."
    )] = None,
) -> str:
    """Retrieves a filtered list of endpoints managed by XDR agents based on IDs, status, and platform."""
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/get_endpoint/",
                                {"request_data": request_data or {}}, "get_filtered_endpoints")


async def isolate_endpoint(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Endpoint to isolate. Use {"endpoint_id": "<id>"} for single endpoint, '
                    'or {"filters": [{"field": "endpoint_id_list", "operator": "in", '
                    '"value": ["<id1>", "<id2>"]}]} for multiple. '
                    'Optional: add "incident_id": "<case_id>" to show action in Case Timeline.'
    )] = None,
    confirm_destructive_action: Annotated[bool, Field(
        description="REQUIRED: Must be True. Isolates endpoint from the network."
    )] = False,
) -> str:
    """DESTRUCTIVE: Isolates an endpoint from the network. The endpoint can only communicate
    with the Cortex agent. Reversal: use unisolate_endpoint.
    Include incident_id in request_data to link the action to a case timeline."""
    if not confirm_destructive_action:
        return create_response(
            data={
                "error": "Destructive action not confirmed",
                "message": "This isolates an endpoint from the network. "
                           "Set confirm_destructive_action=True to proceed.",
                "risk_level": "HIGH",
                "reversible": True
            },
            is_error=True
        )
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/isolate/",
                                {"request_data": request_data}, "isolate_endpoint")


async def unisolate_endpoint(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Endpoint to unisolate. Same format as isolate_endpoint. '
                    'Optional: add "incident_id": "<case_id>" for Case Timeline.'
    )] = None,
) -> str:
    """Restores network access to a previously isolated endpoint.
    Include incident_id in request_data to link the action to a case timeline."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/unisolate/",
                                {"request_data": request_data}, "unisolate_endpoint")


async def scan_endpoint(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Endpoint(s) to scan. Use {"filters": [{"field": "endpoint_id_list", '
                    '"operator": "in", "value": ["<id>"]}]} or {"filters": "all"} for all endpoints. '
                    'Optional: add "incident_id": "<case_id>" for Case Timeline.'
    )] = None,
) -> str:
    """Initiates a malware scan on one or more endpoints.
    Include incident_id in request_data to link the action to a case timeline."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/scan",
                                {"request_data": request_data}, "scan_endpoint")


async def abort_scan(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description="Endpoint(s) to abort scan on. Same filter format as scan_endpoint."
    )] = None,
) -> str:
    """Aborts a running malware scan on one or more endpoints."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/abort_scan",
                                {"request_data": request_data}, "abort_scan")


async def terminate_causality(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Endpoint and causality to terminate. '
                    'Use {"filters": [{"field": "endpoint_id_list", "operator": "in", '
                    '"value": ["<id>"]}], "causality_id": "<causality_id>"}.'
    )] = None,
    confirm_destructive_action: Annotated[bool, Field(
        description="REQUIRED: Must be True. Terminates an entire process tree. Not reversible."
    )] = False,
) -> str:
    """DESTRUCTIVE: Terminates an entire process tree (causality chain) on an endpoint. Not reversible."""
    if not confirm_destructive_action:
        return create_response(
            data={
                "error": "Destructive action not confirmed",
                "message": "This terminates an entire process tree on an endpoint. "
                           "Set confirm_destructive_action=True to proceed.",
                "risk_level": "HIGH",
                "reversible": False
            },
            is_error=True
        )
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/endpoints/terminate_causality",
                                {"request_data": request_data}, "terminate_causality")


async def get_action_status(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Action ID to check. Use {"group_action_id": <action_id>} format.'
    )] = None,
) -> str:
    """Retrieves the status of a previously initiated action (scan, isolate, etc.)."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _endpoint_call(ctx, "/public_api/v1/actions/get_action_status/",
                                {"request_data": request_data}, "get_action_status")


class EndpointToolsModule(BaseModule):
    """Endpoint management: get, isolate, unisolate, scan, abort, terminate, action status."""
    def register_tools(self):
        self._add_tool(get_endpoints)
        self._add_tool(get_filtered_endpoints)
        self._add_tool(isolate_endpoint)
        self._add_tool(unisolate_endpoint)
        self._add_tool(scan_endpoint)
        self._add_tool(abort_scan)
        self._add_tool(terminate_causality)
        self._add_tool(get_action_status)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
