import logging
from typing import Annotated, Optional

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
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def update_incident(
    ctx: Context,
    incident_id: Annotated[str, Field(description="The incident ID to update")],
    status: Annotated[Optional[str], Field(description="New incident status. Allowed values: new, under_investigation, resolved_threat_handled, resolved_known_issue, resolved_duplicate, resolved_false_positive, resolved_other, resolved_auto")] = None,
    assigned_user_mail: Annotated[Optional[str], Field(description="Email address of the user to assign the incident to")] = None,
    manual_severity: Annotated[Optional[str], Field(description="Manual severity override. Allowed values: low, medium, high, critical")] = None,
    resolve_comment: Annotated[Optional[str], Field(description="Comment to add when resolving the incident")] = None,
    unassign_user: Annotated[Optional[bool], Field(description="Set to true to unassign the incident")] = False,
    aisummary: Annotated[Optional[str], Field(description="AI-generated investigation summary in markdown format")] = None,
) -> str:
    """
    Updates an incident's status, assignment, severity, or adds resolution comments.
    This is critical for incident management workflow - assigning incidents to analysts,
    updating status as investigation progresses, and closing incidents with resolution notes.

    Use this tool after investigating an incident to update its properties, assign it to a team member,
    escalate severity, or mark it as resolved with appropriate comments.

    Args:
        ctx: The FastMCP context.
        incident_id: The ID of the incident to update.
        status: New status for the incident (optional). Options include:
            - new: Newly created incident
            - under_investigation: Actively being investigated
            - resolved_threat_handled: Real threat that was mitigated
            - resolved_known_issue: Known non-malicious behavior
            - resolved_duplicate: Duplicate of another incident
            - resolved_false_positive: False positive alert
            - resolved_other: Resolved for other reasons
            - resolved_auto: Automatically resolved
        assigned_user_mail: Email of the user to assign this incident to (optional).
        manual_severity: Override the automatic severity (optional). Values: low, medium, high, critical.
        resolve_comment: Comment explaining the resolution (optional, recommended when resolving).
        unassign_user: Set to true to remove the current assignee (optional).

    Returns:
        JSON response indicating success or failure of the update operation.
    """

    # Build the update payload - only include fields that are provided
    payload = {"request_data": {"incident_id": incident_id, "update_data": {}}}

    if status is not None:
        payload["request_data"]["update_data"]["status"] = status

    if assigned_user_mail is not None:
        payload["request_data"]["update_data"]["assigned_user_mail"] = assigned_user_mail

    if manual_severity is not None:
        payload["request_data"]["update_data"]["manual_severity"] = manual_severity

    if resolve_comment is not None:
        payload["request_data"]["update_data"]["resolve_comment"] = resolve_comment

    if unassign_user:
        payload["request_data"]["update_data"]["unassign_user"] = "true"

    if aisummary is not None:
        payload["request_data"]["update_data"]["aisummary"] = aisummary

    # Validate that at least one update field is provided
    if not payload["request_data"]["update_data"]:
        return create_response(
            data={"error": "At least one update field must be provided (status, assigned_user_mail, manual_severity, resolve_comment, unassign_user, or aisummary)"},
            is_error=True
        )

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            "/public_api/v1/incidents/update_incident/",
            data=payload
        )

        return create_response(data=response_data)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while updating incident: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to update incident: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class UpdateIncidentModule(BaseModule):
    """
    Module for updating incident properties in the Cortex platform.

    This module provides functionality to update incident status, assignments,
    severity, and resolution comments. Essential for incident response workflow
    and case management.

    Tools provided:
        - update_incident: Update incident status, assignment, severity, or add comments
    """

    def register_tools(self):
        self._add_tool(update_incident)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
