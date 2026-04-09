import json
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


async def add_war_room_entry(
    ctx: Context,
    id: Annotated[str, Field(description='Case or alert ID. For cases: "CASE-{id}" (e.g., "CASE-100"). For alerts: use alert ID directly (e.g., "3890").')],
    data: Annotated[str, Field(description='The data to add or command to run. Plain text for notes, commands start with ! (e.g., "!Print value=test").')],
) -> str:
    """
    Add an entry to the cases or alert War Room, including data or commands.

    The War Room is the collaborative investigation workspace in Cortex XSIAM where
    analysts can add notes, run commands, and document their investigation.

    IMPORTANT: Requires an alert ID from an alert that is PART OF A CASE. The alert must have
    an associated investigation (War Room). To find valid alert IDs:
    1. Use get_incident_extra_data to get alerts from a case, OR
    2. Use get_issues to find alerts that have a case_id field, OR
    3. Ask the user for an alert ID from a case they are investigating.

    Use this to:
    - Document investigation findings
    - Add analyst notes to incidents
    - Run War Room automation commands
    - Collaborate with team members
    - Create audit trail of investigation steps

    ID Format:
    - For cases: Prepend "CASE-" (e.g., "CASE-100")
    - For alerts/issues: Use alert ID directly (e.g., "3890")

    You can add plain text notes or run War Room commands (starting with !)
    """
    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            path="/public_api/v1/entries/insert",
            method="POST",
            data={"id": id, "data": data}
        )
        return create_response(data=response)
    except (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
            PAPIClientRequestError, PAPIResponseError, PAPIClientError) as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to add war room entry: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_war_room_entries(
    ctx: Context,
    id: Annotated[str, Field(description='Case or alert ID. For cases: "CASE-{id}" (e.g., "CASE-100"). For alerts: use alert ID directly (e.g., "3890").')],
    filter: Annotated[Optional[dict], Field(description="Optional filters: categories (array), pagesize (int), fromTime (RFC3339), firstID/lastID (string), tags (array)")] = None,
) -> str:
    """
    Get the War Room entries for a specific case or alert.

    You can filter by:
    - Timestamp (fromTime)
    - ID range (firstID, lastID)
    - Entry categories (notes, chat, attachments, etc.)
    - Tags

    Entry Categories:
    - tags: Tags added to the investigation
    - chats: Team communication messages
    - notes: Entries marked as notes
    - attachments: Files uploaded to War Room
    - incidentInfo: Case history
    - commandAndResults: Commands and their results
    - playbookTaskResult: Playbook task results
    - playbookTaskStartAndDone: Task execution records
    - playbookErrors: Playbook error entries

    Use this to:
    - Review investigation history
    - Extract analyst notes
    - Download War Room attachments
    - Audit investigation activities
    """
    try:
        fetcher = await get_fetcher(ctx)
        request_data = {"id": id}
        if filter:
            request_data["filter"] = filter

        response = await fetcher.send_request(
            path="/public_api/v1/entries/get",
            method="POST",
            data=request_data
        )
        return create_response(data=response)
    except (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
            PAPIClientRequestError, PAPIResponseError, PAPIClientError) as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get war room entries: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class WarRoomModule(BaseModule):
    """War Room tools for adding entries and retrieving investigation history."""

    def register_tools(self):
        self._add_tool(add_war_room_entry)
        self._add_tool(get_war_room_entries)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
