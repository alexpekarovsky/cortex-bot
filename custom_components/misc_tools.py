"""Miscellaneous tools — migrated from OpenAPI YAML to Python.
Covers: widgets, indicators, alert events."""
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


async def _api_call(ctx, path, data, tool_name):
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


# --- Alert Events ---

async def get_alert_multi_events(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Alert to get events for. Use {"alert_id": "<alert_id>", '
                    '"filter_alert_fields": false} format.'
    )] = None,
) -> str:
    """Retrieves the raw events that triggered a specific alert.
    Use this for deep forensic investigation of what happened."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v2/alerts/get_alerts_multi_events",
                           {"request_data": request_data}, "get_alert_multi_events")


# --- Widgets ---

async def get_widgets(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Filters for widgets. Use {"filters": [{"field": "widget_key", '
                    '"operator": "in", "value": ["<key>"]}]} or empty for all.'
    )] = None,
) -> str:
    """Lists XQL dashboard widgets."""
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/widgets/get",
                           {"request_data": request_data or {}}, "get_widgets")


async def insert_widgets(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Widget(s) to create. Use {"widgets": [{"tab_id": "<id>", '
                    '"widget_key": "<key>", "title": "<title>", "creation_time": <epoch_ms>, '
                    '"description": "<desc>", "widget_type": "<type>", '
                    '"params": {"xql_query": "<query>", "time_frame": "<frame>"}}]} format.'
    )] = None,
) -> str:
    """Creates XQL dashboard widgets."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/widgets/insert",
                           {"request_data": request_data}, "insert_widgets")


async def delete_widgets(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='Widget(s) to delete. Use {"widget_keys": ["<key1>", "<key2>"]} format.'
    )] = None,
) -> str:
    """Deletes XQL dashboard widgets by key."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/widgets/delete",
                           {"request_data": request_data}, "delete_widgets")


# --- Indicators ---

async def insert_indicators_json(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='IOCs to insert in JSON format. Use {"indicators": [{"indicator": "<value>", '
                    '"type": "<ip/domain/hash>", "reputation": "GOOD/SUSPICIOUS/BAD", '
                    '"comment": "<note>"}]} format.'
    )] = None,
) -> str:
    """Inserts threat indicators (IOCs) in JSON format."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/indicators/insert_jsons",
                           {"request_data": request_data}, "insert_indicators_json")


async def insert_indicators_csv(
    ctx: Context,
    request_data: Annotated[Optional[dict | str], Field(
        description='IOCs to insert in CSV format. Use {"csv_data": "indicator,type,reputation\\n'
                    '1.2.3.4,ip,BAD"} format.'
    )] = None,
) -> str:
    """Inserts threat indicators (IOCs) in CSV format."""
    if not request_data:
        return create_response(data={"error": "request_data is required"}, is_error=True)
    request_data = _parse(request_data)
    return await _api_call(ctx, "/public_api/v1/indicators/insert_csv",
                           {"request_data": request_data}, "insert_indicators_csv")


class MiscToolsModule(BaseModule):
    """Alert events, widgets, indicators."""
    def register_tools(self):
        self._add_tool(get_alert_multi_events)
        self._add_tool(get_widgets)
        self._add_tool(insert_widgets)
        self._add_tool(delete_widgets)
        self._add_tool(insert_indicators_json)
        self._add_tool(insert_indicators_csv)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
