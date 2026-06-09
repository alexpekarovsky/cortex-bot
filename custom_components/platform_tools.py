"""Platform tools — audit logs, distributions, vulnerability scanning."""
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


async def get_audit_management_logs(
    ctx: Context,
    filters: Annotated[Optional[list | str], Field(
        description='Filters for audit logs. Example: [{"field": "type", "operator": "in", "value": ["AUTH"]}]. '
                    'Leave empty for all logs.'
    )] = None,
    search_from: Annotated[int, Field(description="Pagination start offset")] = 0,
    search_to: Annotated[int, Field(description="Pagination end offset")] = 30,
    sort: Annotated[Optional[dict | str], Field(
        description='Sort field. Example: {"field": "TIMESTAMP", "keyword": "desc"}'
    )] = None,
) -> str:
    """Retrieves management audit logs from XSIAM. Shows who did what and when —
    API key usage, configuration changes, user actions, and system events.
    Essential for compliance and security investigations."""
    filters = _parse(filters) if isinstance(filters, str) else filters
    sort = _parse(sort) if isinstance(sort, str) else sort
    try:
        fetcher = await get_fetcher(ctx)
        payload = {"request_data": {"search_from": search_from, "search_to": search_to}}
        if filters:
            payload["request_data"]["filters"] = filters
        if sort:
            payload["request_data"]["sort"] = sort
        response = await fetcher.send_request(
            "/public_api/v1/audits/management_logs", data=payload)
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_audit_management_logs failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_audit_agent_reports(
    ctx: Context,
    filters: Annotated[Optional[list | str], Field(
        description='Filters for agent audit reports. Leave empty for all.'
    )] = None,
    search_from: Annotated[int, Field(description="Pagination start offset")] = 0,
    search_to: Annotated[int, Field(description="Pagination end offset")] = 30,
) -> str:
    """Retrieves agent audit reports — agent installation, upgrade, and status events.
    Shows agent health and deployment history across endpoints."""
    filters = _parse(filters) if isinstance(filters, str) else filters
    try:
        fetcher = await get_fetcher(ctx)
        payload = {"request_data": {"search_from": search_from, "search_to": search_to}}
        if filters:
            payload["request_data"]["filters"] = filters
        response = await fetcher.send_request(
            "/public_api/v1/audits/agents_reports", data=payload)
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_audit_agent_reports failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_distributions(
    ctx: Context,
) -> str:
    """Lists all agent distribution packages (installers) available in XSIAM.
    Shows package ID, name, OS, version, and download status."""
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/v1/distributions/get_distributions",
            data={"request_data": {}})
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_distributions failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def trigger_vulnerability_scan(
    ctx: Context,
    asset_id: Annotated[str, Field(description="Asset ID to scan for vulnerabilities")],
    scanner_type: Annotated[str, Field(
        description="Scanner type: CORTEX_NETWORK_SCANNER, CORTEX_XDR_AGENT, or CORTEX_XDR_AGENTLESS"
    )] = "CORTEX_XDR_AGENT",
) -> str:
    """Triggers a vulnerability scan on a specific asset.
    Requires Cortex Cloud Runtime Security or Posture Management license."""
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/vulnerability-management/v1/scan",
            data={"asset_id": asset_id, "scanner_type": scanner_type},
            omit_papi_prefix=True)
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"trigger_vulnerability_scan failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_endpoint_profiles(
    ctx: Context,
) -> str:
    """Lists endpoint security profiles (prevention policies) configured in XSIAM.
    Use this to review security posture and best practice compliance across endpoint groups."""
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/v1/endpoints/get_profiles/",
            data={"request_data": {"type": "prevention"}})
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_endpoint_profiles failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_triage_presets(
    ctx: Context,
) -> str:
    """Lists forensic triage presets — predefined data collection configurations
    for incident response. Shows preset name, OS, description, and type (Online/Offline).
    Requires Forensics add-on license."""
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            "/public_api/v1/get_triage_presets",
            data={"request_data": {}})
        return create_response(data=response)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"get_triage_presets failed: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class PlatformToolsModule(BaseModule):
    """Platform tools: audit logs, distributions, profiles, triage, vulnerability scanning."""
    def register_tools(self):
        self._add_tool(get_audit_management_logs)
        self._add_tool(get_audit_agent_reports)
        self._add_tool(get_distributions)
        self._add_tool(get_endpoint_profiles)
        self._add_tool(get_triage_presets)
        self._add_tool(trigger_vulnerability_scan)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
