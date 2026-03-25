"""Override broken PANW builtin get_issues — fixes wrong API path."""
import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError, PAPIClientError, PAPIClientRequestError,
    PAPIConnectionError, PAPIResponseError, PAPIServerError,
)
from entities.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)

PAPI_ERRORS = (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
               PAPIClientRequestError, PAPIResponseError, PAPIClientError)


async def get_issues(
    ctx: Context,
    filters: Annotated[list, Field(description="Filters list to get the issues by. Leave empty to get all issues")],
    search_from: Annotated[int, Field(description="Marker for pagination starting point", default=0)] = 0,
    search_to: Annotated[int, Field(description="Marker for pagination ending point", default=30)] = 30,
    sort: Annotated[Optional[dict], Field(
        description="Dictionary of field and keyword to sort by. By default the sort is defined as creation_time, desc"
    )] = None,
) -> str:
    """Retrieves a list of issues or alerts from the Cortex platform.
    Use this tool to fetch all issues, or a filtered subset of issues, or one issue,
    based on various criteria such as time range, severity, status, or specific alert IDs.

    Args:
        filters: Filters list. Example: [{"field": "status", "operator": "in", "value": ["new", "under_investigation"]}]
            Allowed fields: issue_id, external_id, detection_method, domain, severity, _insert_time, status
        search_from: Pagination start offset.
        search_to: Pagination end offset.
        sort: Sort field. Example: {"field": "modification_time", "keyword": "desc"}
    """
    payload = {
        "request_data": {
            "search_from": search_from,
            "search_to": search_to,
        }
    }
    if filters:
        payload["request_data"]["filters"] = filters
    if sort:
        payload["request_data"]["sort"] = sort

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            path="/public_api/v1/issue/search/",
            method="POST",
            data=payload
        )
        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }
        return create_response(data=response_data)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get issues: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class GetIssuesFixModule(BaseModule):
    """Overrides broken PANW get_issues with correct API path."""
    def register_tools(self):
        self._add_tool(get_issues)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
