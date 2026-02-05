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
    aisummary: Annotated[Optional[str], Field(description="AI-generated investigation summary in MARKDOWN format. Use this for detailed case summaries.")] = None,
    timeline: Annotated[Optional[str], Field(description="Visual timeline in HTML format showing alerts chronologically. Must be valid HTML.")] = None,
) -> str:
    """
    Updates a CASE's status, assignment, severity, or adds resolution comments.

    🏷️ TERMINOLOGY: This tool updates CASES (API name: "incident" for backward compatibility).
    For updating individual ISSUES (API name: "alerts"), use update_issue instead.

    This is for case-level management - assigning cases to analysts, updating investigation
    status, and closing cases with resolution notes.

    IMPORTANT: CASES vs ISSUES
    - CASE (incident): Container for related security events
    - ISSUE (alert): Individual security event within a case
    Use this tool for CASE operations, use update_issue for ISSUE operations.

    CRITICAL - VALID CUSTOM FIELDS:
    Only TWO custom fields are supported. Do NOT invent or use any other field names:
    - aisummary: Markdown format - for AI investigation summaries
    - timeline: HTML format - for visual timeline displays

    Do NOT use fields like 'dynamictimeline', 'customfield', or any other made-up names.
    The API will reject invalid field names.

    Use this tool when:
    - Assigning a case to an analyst (assigned_user_mail)
    - Changing case status (new → under_investigation → resolved_*)
    - Escalating or adjusting case severity
    - Adding resolution comments when closing a case
    - Updating the AI-generated case summary (aisummary field - MARKDOWN)
    - Updating the visual timeline (timeline field - HTML)

    Do NOT use this for:
    - Triaging individual alerts → use update_issue instead
    - Updating alert severity → use update_issue instead
    - Marking alerts as false positive → use update_issue instead

    Args:
        ctx: The FastMCP context.
        incident_id: The case/incident ID to update (e.g., "350").
        status: New status for the case (optional). Options include:
            - new: Newly created case
            - under_investigation: Actively being investigated
            - resolved_threat_handled: Real threat that was mitigated
            - resolved_known_issue: Known non-malicious behavior
            - resolved_duplicate: Duplicate of another case
            - resolved_false_positive: False positive case
            - resolved_other: Resolved for other reasons
            - resolved_auto: Automatically resolved
        assigned_user_mail: Email of the user to assign this case to (optional).
        manual_severity: Override the automatic severity (optional). Values: low, medium, high, critical.
        resolve_comment: Comment explaining the resolution (optional, recommended when resolving).
        unassign_user: Set to true to remove the current assignee (optional).
        aisummary: AI investigation summary in MARKDOWN format (optional).
        timeline: Visual timeline in HTML format (optional).

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

    if timeline is not None:
        payload["request_data"]["update_data"]["timeline"] = timeline

    # Validate that at least one update field is provided
    if not payload["request_data"]["update_data"]:
        return create_response(
            data={"error": "At least one update field must be provided (status, assigned_user_mail, manual_severity, resolve_comment, unassign_user, aisummary, or timeline)"},
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
