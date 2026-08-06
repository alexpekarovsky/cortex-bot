import asyncio
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
from entities.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def run_xql_query(
    ctx: Context,
    query: Annotated[str, Field(description="The XQL query to execute. XQL is XSIAM's query language for searching and analyzing security data across all data sources.")],
    time_frame: Annotated[Optional[str], Field(description="Relative time frame for the query. Examples: '1 hour', '24 hours', '7 days', '30 days'. If not provided, uses a default time range.")] = None,
    timeout: Annotated[int, Field(description="Maximum time to wait for query results in seconds", default=600)] = 600,
) -> str:
    """
    Executes an XQL (Extended Query Language) query for threat hunting and data analysis.

    XQL is XSIAM's powerful query language that allows you to search, filter, correlate,
    and analyze security data across all your data sources. The query executes asynchronously
    and this tool automatically polls for results until completion or timeout.

    RECOMMENDED WORKFLOW — Build the perfect XQL query:
    1. First call get_datasets to see all available datasets, their size, and event counts
    2. Then discover the schema: run "dataset = <name> | limit 1" to see all field names
    3. Then build your actual query using the correct field names
    4. Use the XQL skill (/xql) for complex query help

    Use this tool when:
    - Threat hunting for specific IOCs or attack patterns
    - Searching historical security events
    - Investigating suspicious activity across your environment
    - Building custom analytics and correlations
    - Validating detection rules
    - Performing forensic analysis
    - Schema discovery: "dataset = <name> | limit 1" to see available fields

    Do NOT use this for:
    - Simple alert listing - use get_issues instead
    - Incident details - use get_incident_extra_data instead
    - Running XSOAR commands - use run_xsoar_automation instead
    - Listing available datasets - use get_datasets instead

    WARNING: XQL queries can return LARGE result sets. Always use LIMIT in your
    queries (e.g., "| limit 100") to control output size. Unbounded queries may
    return thousands of records.

    Example XQL queries:
    - Schema discovery: "dataset = xdr_data | limit 1" (returns all field names)
    - Find all processes: "dataset = xdr_data | filter event_type = ENUM.PROCESS"
    - Hunt for specific IP: "dataset = xdr_data | filter action_remote_ip = '192.168.1.100'"
    - Search for malware: "dataset = xdr_data | filter action_file_name contains 'malware'"
    - User activity: "dataset = xdr_data | filter actor_effective_username = 'john.doe'"
    - Process with parent: "dataset = xdr_data | filter event_type = ENUM.PROCESS and action_process_image_name = 'cmd.exe'"

    Args:
        ctx: The FastMCP context.
        query: The XQL query string to execute. Must start with dataset specification.
        time_frame: Relative time range (e.g., "1 hour", "24 hours", "7 days", "30 days").
                   If not provided, uses default time range.
        timeout: Maximum seconds to wait for query completion (default: 600 = 10 minutes).

    Returns:
        JSON response containing query results with all matching events and data.
    """

    MAX_QUERY_LENGTH = 10000
    if len(query) > MAX_QUERY_LENGTH:
        return create_response(
            data={"error": f"Query exceeds maximum length ({len(query)} > {MAX_QUERY_LENGTH} chars)"},
            is_error=True
        )

    # Start the XQL query execution
    start_payload = {"request_data": {"query": query}}

    if time_frame:
        # Parse time_frame to convert to proper API format
        # API expects time in milliseconds, not a string like "7 days"
        # Format should be {"relativeTime": <milliseconds>}
        try:
            import re
            match = re.match(r'(\d+)\s*(hour|hours|day|days|minute|minutes|second|seconds)', time_frame.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)

                # Convert to milliseconds
                if 'second' in unit:
                    time_ms = value * 1000
                elif 'minute' in unit:
                    time_ms = value * 60 * 1000
                elif 'hour' in unit:
                    time_ms = value * 60 * 60 * 1000
                elif 'day' in unit:
                    time_ms = value * 24 * 60 * 60 * 1000
                else:
                    time_ms = None

                if time_ms:
                    start_payload["request_data"]["timeframe"] = {"relativeTime": time_ms}
            else:
                logger.warning(f"Could not parse time_frame '{time_frame}', using default")
        except Exception as e:
            logger.warning(f"Error parsing time_frame '{time_frame}': {e}, using default")

    try:
        fetcher = await get_fetcher(ctx)

        # Step 1: Start the query
        logger.info(f"Starting XQL query execution: {query[:100]}...")
        logger.debug(f"Start payload: {start_payload}")
        start_response = await fetcher.send_request(
            "/public_api/v1/xql/start_xql_query/",
            data=start_payload
        )

        logger.info(f"Start XQL response: {start_response}")
        logger.debug(f"Response type: {type(start_response)}, keys: {start_response.keys() if isinstance(start_response, dict) else 'not a dict'}")

        if "reply" not in start_response:
            return create_response(
                data={"error": "Failed to start XQL query - no execution_id returned", "response": start_response},
                is_error=True
            )

        # The reply field IS the execution_id (it's a string, not an object)
        execution_id = start_response["reply"]
        if not isinstance(execution_id, str) or not execution_id:
            return create_response(
                data={
                    "error": "XQL query failed to start. The API returned an invalid execution ID.",
                    "details": execution_id,
                    "query": query,
                },
                is_error=True
            )
        logger.info(f"XQL query started with execution_id: {execution_id}")

        # Step 2: Poll for results
        poll_payload = {"request_data": {"query_id": execution_id}}
        poll_interval = 2  # seconds
        elapsed_time = 0
        consecutive_poll_errors = 0
        max_poll_errors = 5  # Bail out after 5 consecutive poll failures

        while elapsed_time < timeout:
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval

            logger.debug(f"Polling XQL query results (elapsed: {elapsed_time}s)")

            try:
                poll_response = await fetcher.send_request(
                    "/public_api/v1/xql/get_query_results/",
                    data=poll_payload
                )
            except Exception as poll_err:
                consecutive_poll_errors += 1
                logger.warning(f"XQL poll error ({consecutive_poll_errors}/{max_poll_errors}): {poll_err}")
                if consecutive_poll_errors >= max_poll_errors:
                    return create_response(
                        data={
                            "error": f"XQL query polling failed {max_poll_errors} times consecutively. Last error: {poll_err}",
                            "execution_id": execution_id,
                            "query": query,
                        },
                        is_error=True
                    )
                continue

            if "reply" not in poll_response:
                consecutive_poll_errors += 1
                logger.warning(
                    f"XQL poll returned no 'reply' key ({consecutive_poll_errors}/{max_poll_errors}). "
                    f"Response: {str(poll_response)[:200]}"
                )
                if consecutive_poll_errors >= max_poll_errors:
                    return create_response(
                        data={
                            "error": f"XQL query failed: {max_poll_errors} consecutive poll responses had no results. "
                                     f"The query may be invalid or the server is not responding.",
                            "execution_id": execution_id,
                            "query": query,
                            "last_response": str(poll_response)[:500],
                        },
                        is_error=True
                    )
                continue

            # Valid response received — reset error counter
            consecutive_poll_errors = 0
            reply = poll_response["reply"]
            if not isinstance(reply, dict):
                logger.warning(f"XQL poll 'reply' is not a dict: {type(reply)} — {str(reply)[:200]}")
                continue
            status = reply.get("status")

            if status == "SUCCESS":
                logger.info(f"XQL query completed successfully after {elapsed_time}s")
                # Add metadata for better LLM formatting
                poll_response["_metadata"] = {
                    "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
                    "execution_time_seconds": elapsed_time,
                    "query": query
                }
                return create_response(data=poll_response)

            elif status in ("FAILED", "FAIL"):
                error_msg = reply.get("error", "Query execution failed")
                logger.error(f"XQL query failed: {error_msg}")
                return create_response(
                    data={
                        "error": f"XQL query failed: {error_msg}",
                        "query": query,
                        "execution_id": execution_id,
                    },
                    is_error=True
                )

            elif status in ["PENDING", "RUNNING"]:
                # Query still executing, continue polling
                logger.debug(f"Query status: {status}, continuing to poll...")
                continue

            else:
                logger.warning(f"Unknown XQL query status: {status}")
                continue

        # Timeout reached — include last known status for debugging
        logger.error(f"XQL query timed out after {timeout} seconds")
        return create_response(
            data={
                "error": f"Query execution timed out after {timeout} seconds. The query may still be running. Execution ID: {execution_id}",
                "execution_id": execution_id,
                "query": query,
            },
            is_error=True
        )

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while executing XQL query: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to execute XQL query: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


async def discover_dataset_schema(
    ctx: Context,
    dataset: Annotated[str, Field(description="Dataset name to discover schema for (e.g., 'xdr_data', 'host_inventory', 'alerts')")],
) -> str:
    """Discovers the schema (field names and sample values) of an XSIAM dataset.

    Runs 'dataset = <name> | limit 1' and returns a clean list of field names with
    their types and sample values. Use this BEFORE writing XQL queries to know
    the exact field names available.

    WORKFLOW:
    1. get_datasets — see what datasets exist and have data
    2. discover_dataset_schema — see what fields each dataset has
    3. run_xql_query — write your query with correct field names
    """
    import json as _json

    query = f"dataset = {dataset} | limit 1"
    try:
        # Execute a minimal XQL query to get one row
        fetcher = await get_fetcher(ctx)
        start_resp = await fetcher.send_request(
            "/public_api/v1/xql/start_xql_query/",
            data={"request_data": {"query": query, "timeframe": {"relativeTime": 2592000000}}}
        )
        exec_id = start_resp.get("reply", "")

        # Poll for results
        import time as _time
        for _ in range(12):
            await asyncio.sleep(5)
            results_resp = await fetcher.send_request(
                "/public_api/v1/xql/get_query_results/",
                data={"request_data": {"query_id": exec_id, "pending_result": True}}
            )
            reply = results_resp.get("reply", {})
            status = reply.get("status", "")
            if status == "SUCCESS":
                break
            if status in ("FAIL", "CANCELED"):
                return create_response(data={"dataset": dataset, "error": f"Query {status}"}, is_error=True)

        data = reply.get("results", {}).get("data", [])

        if not data:
            return create_response(data={
                "dataset": dataset,
                "fields": [],
                "message": f"Dataset '{dataset}' exists but has no data. Try a different time_frame.",
            })

        row = data[0]
        fields = []
        for key, value in sorted(row.items()):
            fields.append({
                "field": key,
                "type": type(value).__name__ if value is not None else "null",
                "sample": str(value)[:100] if value is not None else None,
            })

        return create_response(data={
            "dataset": dataset,
            "field_count": len(fields),
            "fields": fields,
        })

    except Exception as e:
        return create_response(data={
            "dataset": dataset,
            "error": str(e),
            "hint": "Check dataset name with get_datasets first.",
        }, is_error=True)


class XQLQueryModule(BaseModule):
    """XQL query execution + schema discovery.

    Tools provided:
        - run_xql_query: Execute XQL queries with automatic result polling
        - discover_dataset_schema: Discover field names and types in a dataset
    """

    def register_tools(self):
        self._add_tool(run_xql_query)
        self._add_tool(discover_dataset_schema)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
