import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError,
    PAPIClientError,
    PAPIClientRequestError,
    PAPIConnectionError,
    PAPIResponseError,
    PAPIServerError,
)
from entities.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def get_incident_extra_data(
    ctx: Context,
    incident_id: Annotated[str, Field(description="The incident ID to get detailed information for")],
    alerts_limit: Annotated[int, Field(description="Maximum number of alerts to return in the incident", default=1000)] = 1000,
) -> str:
    """
    Retrieves comprehensive detailed information about a specific incident.

    This tool provides the complete incident context including all related alerts,
    affected users, involved hosts, file artifacts, network connections, and a full
    timeline of events. This is essential for deep-dive incident investigation.

    Use this tool when you need the full story of an incident - all the alerts it contains,
    what users and endpoints are involved, what files were touched, network connections made,
    and the complete sequence of events.

    The response includes:
    - Full incident metadata (severity, status, creation time, etc.)
    - All alerts within the incident (up to alerts_limit)
    - User and host information for entities involved
    - File artifacts and hashes
    - Network activity (IPs, domains, URLs)
    - Complete event timeline
    - MITRE ATT&CK techniques
    - Rule information that triggered the alerts

    Args:
        ctx: The FastMCP context.
        incident_id: The ID of the incident to retrieve detailed information for.
        alerts_limit: Maximum number of alerts to include (default: 1000, max: 1000).

    Returns:
        JSON response containing comprehensive incident data including all alerts,
        affected entities, artifacts, and timeline information.
    """

    payload = {
        "request_data": {
            "incident_id": incident_id,
            "alerts_limit": alerts_limit
        }
    }

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/incidents/get_incident_extra_data/",
            data=payload
        )

        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while getting incident extra data: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get incident extra data: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class IncidentDetailsModule(BaseModule):
    """
    Module for retrieving detailed incident information from the Cortex platform.

    This module provides deep-dive incident investigation capabilities by fetching
    comprehensive data about specific incidents including all related alerts,
    affected entities, artifacts, network activity, and complete event timelines.

    Tools provided:
        - get_incident_extra_data: Retrieve full incident details with all context
    """

    def register_tools(self):
        self._add_tool(get_incident_extra_data)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
