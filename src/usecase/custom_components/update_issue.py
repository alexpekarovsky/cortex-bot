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


async def update_issue(
    ctx: Context,
    issue_id: Annotated[int, Field(description="Numeric issue/alert ID as INTEGER (e.g., 6142, NOT '6142')")],
    severity: Annotated[Optional[str], Field(description="New severity. Allowed values: INFO, LOW, MEDIUM, HIGH, CRITICAL")] = None,
    status: Annotated[Optional[str], Field(description="New status. Allowed values: New, In Progress, Resolved")] = None,
    status_resolution_reason: Annotated[Optional[str], Field(description="Resolution reason when status is Resolved. Allowed values: RESOLVED_KNOWN_ISSUE, RESOLVED_FALSE_POSITIVE, RESOLVED_DUPLICATE, RESOLVED_OTHER")] = None,
    status_resolution_comment: Annotated[Optional[str], Field(description="Comment explaining the resolution")] = None,
) -> str:
    """
    Updates an individual ALERT/ISSUE's severity, status, and resolution details.
    This is for triaging individual alerts - marking false positives, updating severity,
    and documenting resolution reasons.

    IMPORTANT: This tool updates individual ALERTS/ISSUES. For updating CASES (incidents),
    use update_incident instead. Status values are DIFFERENT between the two tools!

    Use this tool when:
    - Triaging individual alerts within a case
    - Marking an alert as false positive or known issue
    - Updating alert severity based on investigation findings
    - Changing alert status as investigation progresses
    - Adding resolution comments to individual alerts

    Do NOT use this for:
    - Case-level status updates → use update_incident instead
    - Assigning cases to analysts → use update_incident instead
    - Case resolution comments → use update_incident instead

    CRITICAL: Status values for this tool are DIFFERENT from update_incident:
    - This tool: "New", "In Progress", "Resolved" (Title Case!)
    - update_incident: "new", "under_investigation", "resolved_*" (lowercase!)

    Args:
        ctx: The FastMCP context.
        issue_id: Numeric issue/alert ID as INTEGER (e.g., 6142, NOT a string).
        severity: New severity level (optional). Values: INFO, LOW, MEDIUM, HIGH, CRITICAL.
        status: New status (optional). Values: New, In Progress, Resolved (Title Case!).
        status_resolution_reason: Resolution reason when closing (optional). Values:
            - RESOLVED_KNOWN_ISSUE: Known non-malicious behavior
            - RESOLVED_FALSE_POSITIVE: False positive alert
            - RESOLVED_DUPLICATE: Duplicate of another issue
            - RESOLVED_OTHER: Resolved for other reasons
        status_resolution_comment: Comment explaining resolution (optional, recommended when resolving).

    Returns:
        JSON response indicating success or failure of the update operation.
    """

    # Build the update payload - only include fields that are provided
    update_data = {}

    if severity is not None:
        update_data["severity"] = severity

    if status is not None:
        update_data["status"] = status

    if status_resolution_reason is not None:
        update_data["status_resolution_reason"] = status_resolution_reason

    if status_resolution_comment is not None:
        update_data["status_resolution_comment"] = status_resolution_comment

    # Validate that at least one update field is provided
    if not update_data:
        return create_response(
            data={"error": "At least one update field must be provided (severity, status, status_resolution_reason, or status_resolution_comment)"},
            is_error=True
        )

    payload = {
        "request_data": {
            "update_data": update_data
        }
    }

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            f"/issue/{issue_id}",
            method="POST",
            data=payload
        )

        return create_response(data=response_data)
    except PAPIResponseError as e:
        # API returns 204 No Content on success, which causes JSON parse error
        # Check if error message indicates empty response (successful update)
        if "Invalid JSON response" in str(e) and "column 1" in str(e):
            return create_response(data={
                "success": True,
                "issue_id": issue_id,
                "message": f"Issue {issue_id} updated successfully",
                "updates_applied": update_data
            })
        logger.exception(f"PAPI response error while updating issue: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while updating issue: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to update issue: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class UpdateIssueModule(BaseModule):
    """
    Module for updating issue (alert) properties in the Cortex platform.

    This module provides functionality to update issue severity, status,
    and resolution details. Essential for alert triage and management workflow.

    Tools provided:
        - update_issue: Update issue severity, status, or resolution details
    """

    def register_tools(self):
        self._add_tool(update_issue)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
