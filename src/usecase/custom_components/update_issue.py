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
    issue_id: Annotated[int, Field(description="Numeric ID of the issue to update")],
    severity: Annotated[Optional[str], Field(description="New severity. Allowed values: INFO, LOW, MEDIUM, HIGH, CRITICAL")] = None,
    status: Annotated[Optional[str], Field(description="New status. Allowed values: New, Under Investigation, Resolved")] = None,
    status_resolution_reason: Annotated[Optional[str], Field(description="Resolution reason when status is Resolved. Allowed values: RESOLVED_KNOWN_ISSUE, RESOLVED_FALSE_POSITIVE, RESOLVED_DUPLICATE, RESOLVED_OTHER")] = None,
    status_resolution_comment: Annotated[Optional[str], Field(description="Comment explaining the resolution")] = None,
) -> str:
    """
    Updates an existing issue (alert) in the system.

    This tool allows updating issue properties such as severity, status, and resolution details.
    Essential for alert management workflow - triaging alerts, marking false positives,
    and documenting resolution reasons.

    Use this tool after investigating an issue to:
    - Update its severity based on findings
    - Change status as investigation progresses
    - Mark as resolved with appropriate reason and comments
    - Document false positives or known issues

    Args:
        ctx: The FastMCP context.
        issue_id: Numeric ID of the issue to update.
        severity: New severity level (optional). Values: INFO, LOW, MEDIUM, HIGH, CRITICAL.
        status: New status (optional). Values: New, Under Investigation, Resolved.
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
            f"/v1/issue/{issue_id}",
            data=payload,
            omit_papi_prefix=True
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
