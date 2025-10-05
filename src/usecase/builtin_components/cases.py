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
from pkg.util import create_response, read_resource
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def get_cases_response() -> str:
    try:
        cases_json = read_resource("cases_response.json")
        return create_response(data={"response": json.loads(cases_json)})
    except FileNotFoundError as e:
        logger.exception(f"Cases response file not found: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON in cases response file: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to read cases responses: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def get_cases(ctx: Context,
                    filters: Annotated[list, Field(description="Filters list to get the cases by. Leave empty go get all cases")],
                    search_from: Annotated[int, Field(description="Marker for pagination starting point", default=0)] = 0,
                    search_to: Annotated[int, Field(description="Marker for pagination ending point", default=30)] = 30,
                    sort: Annotated[Optional[dict], Field(description="Field to sort by. By default the sort is defined as modification_time, desc")] = None,
                    ) -> str:
    """
    Retrieves a list of cases or incidents from the Cortex platform.
    Use this tool to fetch all cases, or a filtered subset of cases, based on various criteria such as time range, status, or specific case IDs.
    This is highly valuable for security monitoring, historical analysis, and reporting on detected cases.
    Use the get_case_info tool to get detailed info about the case or incident and issues or alerts within it.

    Args:
        ctx: The FastMCP context.
        filters: Filters list to get the cases by. Example -
            [{
                        "field": "status",
                        "operator": "in",
                        "value": ["new", "under_investigation"]
            }]
            Leave empty go get all cases.
        search_from: Marker for pagination starting point.
        search_to: Marker for pagination ending point.
        sort: Field to sort by. Example -
            {
                    "field": "modification_time",
                    "keyword": "desc"
            }

    Returns:
        JSON response containing case data.
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
        response_data = await fetcher.send_request("case/search/", data=payload)

        return create_response(data=response_data)
    except (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError, PAPIClientRequestError, PAPIResponseError, PAPIClientError) as e:
        logger.exception(f"PAPI error while getting cases: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get cases: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class CasesModule(BaseModule):
    """
        Module for managing Cortex platform cases and incidents.

        This module provides functionality to retrieve and interact with security cases
        from the Cortex platform. It includes tools for searching and filtering
        cases based on various criteria such as status, time range, and custom filters.

        Tools provided:
            - get_cases: Retrieves cases with filtering, pagination, and sorting options

        Resources provided:
            - cases_response.json: Example API response for cases endpoint
        """
    def register_tools(self):
        self._add_tool(get_cases)

    def register_resources(self):
        self._add_resource(get_cases_response, uri="resources://cases_response.json",
    name="cases_response.json",
    description="Example response from the cases API",
    mime_type="application/json",)

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
