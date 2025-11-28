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


async def get_contributing_events(
    ctx: Context,
    alert_id: Annotated[str, Field(description="The alert ID to get contributing events for (must be a correlation alert)")],
) -> str:
    """
    Retrieves the individual events that contributed to a CORRELATION alert.

    WARNING: This tool ONLY works with CORRELATION alerts! If you use it with a
    non-correlation alert, it will return an error. For non-correlation alerts,
    use get_alert_multi_events instead.

    Correlation alerts are created when XSIAM's analytics engine detects multiple
    related events that together indicate a security threat or attack pattern.
    This tool shows you the complete attack chain - all the individual events that
    were correlated together to trigger the alert.

    Use this tool when:
    - Investigating a CORRELATION alert (check alert type first!)
    - You need to see all events that triggered the correlation
    - Understanding the timeline and sequence of a multi-stage attack
    - Breaking down a complex alert into its component events

    Do NOT use this for:
    - Non-correlation alerts → use get_alert_multi_events instead
    - Getting detailed event data for any alert type → use get_alert_multi_events
    - If unsure about alert type → use get_alert_multi_events (works on all alerts)

    Example use cases:
    - "Show me all the events that led to this lateral movement alert"
    - "What individual activities triggered this multi-stage attack detection?"
    - "Break down this correlation alert into its component events"

    Args:
        ctx: The FastMCP context.
        alert_id: The ID of the correlation alert (e.g., "6126").

    Returns:
        JSON response containing all individual events that contributed to the
        correlation alert, including event details, timestamps, and relationships.
    """

    payload = {
        "request_data": {
            "alert_id": alert_id
        }
    }

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/alerts/get_contributing_event/",
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
        logger.exception(f"PAPI error while getting contributing events: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get contributing events: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class ContributingEventsModule(BaseModule):
    """
    Module for retrieving contributing events for correlation alerts.

    This module provides the ability to break down correlation alerts into their
    individual contributing events, showing the complete attack chain and event
    timeline that triggered the correlation.

    Tools provided:
        - get_contributing_events: Get all events that contributed to a correlation alert
    """

    def register_tools(self):
        self._add_tool(get_contributing_events)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
