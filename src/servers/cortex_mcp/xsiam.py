import json
import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from core.fetcher import get_fetcher
from servers.cortex_mcp.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from servers.util import create_response_and_report, read_file

logger = logging.getLogger("XSIAM MCP")

xsiam_mcp = FastMCP(name="Cortex MCP Service")

@xsiam_mcp.tool()
async def get_issues(ctx: Context,
                    filters: Annotated[list, Field(description="Filters list to get the issues by. Leave empty go get all issues")],
                    search_from: Annotated[int, Field(description="Marker for pagination starting point", default=0)] = 0,
                    search_to: Annotated[int, Field(description="Marker for pagination ending point", default=30)] = 30,
                    sort: Annotated[Optional[dict], Field(description="Field to sort by. By default the sort is defined as creation_time, desc.", default={})] = None,
                    ) -> str:
    """
    Retrieves a list of issues or alerts from the Cortex XSIAM platform.
    Use this tool to fetch all issues, or a filtered subset of issues, or one issue, based on various criteria such as time range, severity, status, or specific alert IDs.
    This is highly valuable for security monitoring, threat hunting, and reporting on detected security events.

    Args:
        ctx: The FastMCP context.
        filters: Filters list to get the issues by. Example -
            [{
                        "field": "status",
                        "operator": "in",
                        "value": ["new", "under_investigation"]
            }]
            Leave empty go get all issues.
        search_from: Marker for pagination starting point.
        search_to: Marker for pagination ending point.
        sort: Field to sort by. Example -
            {
                    "field": "modification_time",
                    "keyword": "desc"
            }
            By default the sort is defined as creation_time, desc.
    Returns:
        JSON response containing issue data.
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
        response_data = fetcher.send_request("/v1/issue/search/", data=payload, omit_papi_prefix=True)
        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }

        return create_response_and_report(data=response_data)
    except Exception as e:
        logger.error(f"Failed to get issues: {e}")
        return create_response_and_report(data={"error": str(e)}, is_error=True)

@xsiam_mcp.resource(
    uri="resources://issues_response.json",
    name="issues_responses.json",
    description="Example response from the issues API",
    mime_type="application/json",
)
async def get_issues_response() -> str:
    try:
        issues_json = read_file("issues_response.json")
    except Exception as e:
        logger.exception(f"Failed to read issues responses: {e}")
        return create_response_and_report(data={"error": str(e)}, is_error=True)

    return create_response_and_report(data={"response": json.loads(issues_json)})


@xsiam_mcp.resource(
    uri="resources://cases_response.json",
    name="cases_responses.json",
    description="Example response from the cases API",
    mime_type="application/json",
)
async def get_cases_response() -> str:
    try:
        cases_json = read_file("cases_response.json")
    except Exception as e:
        logger.exception(f"Failed to read issues responses: {e}")
        return create_response_and_report(data={"error": str(e)}, is_error=True)

    return create_response_and_report(data={"response": json.loads(cases_json)})

@xsiam_mcp.tool()
async def get_cases(ctx: Context,
                    filters: Annotated[list, Field(description="Filters list to get the cases by. Leave empty go get all cases")],
                    search_from: Annotated[int, Field(description="Marker for pagination starting point", default=0)] = 0,
                    search_to: Annotated[int, Field(description="Marker for pagination ending point", default=30)] = 30,
                    sort: Annotated[Optional[dict], Field(description="Field to sort by. By default the sort is defined as modification_time, desc")] = None,
                    ) -> str:
    """
    Retrieves a list of cases or incidents from the Cortex XSIAM platform.
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
        response_data = fetcher.send_request("case/search/", data=payload)

        return create_response_and_report(data=response_data)
    except Exception as e:
        logger.error(f"Failed to get cases: {e}")
        return create_response_and_report(data={"error": str(e)}, is_error=True)

