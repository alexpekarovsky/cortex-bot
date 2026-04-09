"""IOC and BIOC management tools — get, search, filter indicators and behavioral IOCs."""
import json
import logging
from typing import Annotated, Optional

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


async def get_indicators(
    ctx: Context,
    filters: Annotated[Optional[list | str], Field(
        description='Filters for IOCs. Example: [{"field": "type", "operator": "IN", "value": ["DOMAIN"]}]. '
                    'Filter fields: rule_id, indicator, type, severity. Leave empty for all.'
    )] = None,
    search_from: Annotated[int, Field(description="Pagination start")] = 0,
    search_to: Annotated[int, Field(description="Pagination end")] = 50,
) -> str:
    """Retrieves IOC (Indicator of Compromise) rules from XSIAM.
    Shows indicator value, type (IP/DOMAIN/HASH/FILENAME), severity, and expiration.
    Use this to review existing threat indicators before adding new ones."""
    filters = _parse(filters)
    try:
        fetcher = await get_fetcher(ctx)
        payload = {"request_data": {"search_from": search_from, "search_to": search_to}}
        if filters:
            payload["request_data"]["filters"] = filters
        response = await fetcher.send_request("/public_api/v1/indicators/get", data=payload)
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_indicators failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_biocs(
    ctx: Context,
    filters: Annotated[Optional[list | str], Field(
        description='Filters for BIOCs. Example: [{"field": "type", "operator": "IN", "value": ["EXECUTION"]}]. '
                    'Leave empty for all.'
    )] = None,
    search_from: Annotated[int, Field(description="Pagination start")] = 0,
    search_to: Annotated[int, Field(description="Pagination end")] = 50,
) -> str:
    """Retrieves Behavioral IOC (BIOC) rules from XSIAM.
    BIOCs detect suspicious behavioral patterns (process execution, file events, network activity).
    Shows rule name, type, severity, status, MITRE mapping, and indicator logic."""
    filters = _parse(filters)
    try:
        fetcher = await get_fetcher(ctx)
        payload = {"request_data": {"search_from": search_from, "search_to": search_to}}
        if filters:
            payload["request_data"]["filters"] = filters
        response = await fetcher.send_request("/public_api/v1/bioc/get", data=payload)
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_biocs failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def insert_bioc(
    ctx: Context,
    request_data: Annotated[Optional[list | str], Field(
        description='List of BIOC objects to insert/update. Required fields: name, type '
                    '(OTHER/EXECUTION/PERSISTENCE/EVASION/LATERAL_MOVEMENT/PRIVILEGE_ESCALATION/CREDENTIAL_ACCESS/'
                    'COLLECTION/EXFILTRATION/RECONNAISSANCE/DISCOVERY/etc.), severity (SEV_010_INFO to SEV_040_HIGH), '
                    'status (enabled/disabled), is_xql (bool), indicator (object — use {} for empty), '
                    'comment (string), mitre_tactic_id_and_name (list, e.g. ["TA0002 - Execution"]), '
                    'mitre_technique_id_and_name (list, e.g. ["T1059 - Command and Scripting Interpreter"]). '
                    'IMPORTANT: Omit rule_id for NEW BIOCs. Only provide rule_id to UPDATE an existing one. '
                    'Example: [{"name": "My BIOC", "type": "OTHER", "severity": "SEV_030_MEDIUM", '
                    '"status": "disabled", "is_xql": false, "comment": "test", "indicator": {}, '
                    '"mitre_tactic_id_and_name": ["TA0002 - Execution"], '
                    '"mitre_technique_id_and_name": ["T1059 - Command and Scripting Interpreter"]}]'
    )] = None,
) -> str:
    """Insert or update Behavioral IOC (BIOC) rules.
    BIOCs define behavioral detection patterns for endpoint activity.
    Omit rule_id to create new BIOCs. Provide rule_id only to update existing ones.
    Note: rule_id is tenant-specific and cannot be used across tenants."""
    request_data = _parse(request_data)
    if not request_data:
        return create_response(data={"error": "request_data is required — provide list of BIOC objects"}, is_error=True)
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/v1/bioc/insert",
            data={"request_data": request_data})
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"insert_bioc failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_datasets(
    ctx: Context,
) -> str:
    """Lists all datasets available for XQL queries in XSIAM.
    Shows dataset name, type (SYSTEM/USER/RAW/LOOKUP), log update type, size, event count, and last updated time.

    RECOMMENDED WORKFLOW for XQL queries:
    1. Call get_datasets to see what's available and which have data
    2. Run schema discovery: run_xql_query(query="dataset = <name> | limit 1") to see field names
    3. Build your query using the discovered fields
    4. Use the XQL skill (/xql) for complex query construction

    Note: Datasets with no data show null for size/events. Focus on datasets with actual events."""
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/v1/xql/get_datasets", data={"request_data": {}})
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_datasets failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class IOCBIOCToolsModule(BaseModule):
    """IOC/BIOC management + dataset listing."""
    def register_tools(self):
        self._add_tool(get_indicators)
        self._add_tool(get_biocs)
        self._add_tool(insert_bioc)
        self._add_tool(get_datasets)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
