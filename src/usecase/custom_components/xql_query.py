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
    and analyze security data across all your data sources. Use this for:
    - Threat hunting across your environment
    - Searching for indicators of compromise (IOCs)
    - Custom investigations and analytics
    - Historical analysis of security events
    - Correlating data from multiple sources

    The query executes asynchronously and this tool automatically polls for results
    until completion or timeout.

    Example XQL queries:
    - Find all processes: "dataset = xdr_data | filter event_type = ENUM.PROCESS"
    - Hunt for specific IP: "dataset = xdr_data | filter action_remote_ip = '192.168.1.100'"
    - Search for malware: "dataset = xdr_data | filter action_file_name contains 'malware'"
    - User activity: "dataset = xdr_data | filter actor_effective_username = 'john.doe'"

    Args:
        ctx: The FastMCP context.
        query: The XQL query string to execute.
        time_frame: Relative time range (e.g., "1 hour", "24 hours", "7 days").
                   If not provided, uses default time range.
        timeout: Maximum seconds to wait for query completion (default: 600 = 10 minutes).

    Returns:
        JSON response containing query results with all matching events and data.
    """

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
        logger.info(f"XQL query started with execution_id: {execution_id}")

        # Step 2: Poll for results
        poll_payload = {"request_data": {"query_id": execution_id}}
        poll_interval = 2  # seconds
        elapsed_time = 0

        while elapsed_time < timeout:
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval

            logger.debug(f"Polling XQL query results (elapsed: {elapsed_time}s)")
            poll_response = await fetcher.send_request(
                "/public_api/v1/xql/get_query_results/",
                data=poll_payload
            )

            if "reply" not in poll_response:
                continue

            reply = poll_response["reply"]
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

            elif status == "FAILED":
                error_msg = reply.get("error", "Query execution failed")
                logger.error(f"XQL query failed: {error_msg}")
                return create_response(
                    data={"error": f"Query execution failed: {error_msg}"},
                    is_error=True
                )

            elif status in ["PENDING", "RUNNING"]:
                # Query still executing, continue polling
                logger.debug(f"Query status: {status}, continuing to poll...")
                continue

            else:
                logger.warning(f"Unknown query status: {status}")
                continue

        # Timeout reached
        logger.error(f"XQL query timed out after {timeout} seconds")
        return create_response(
            data={
                "error": f"Query execution timed out after {timeout} seconds. The query may still be running. Execution ID: {execution_id}",
                "execution_id": execution_id
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


class XQLQueryModule(BaseModule):
    """
    Module for executing XQL (Extended Query Language) queries in XSIAM.

    This module provides powerful threat hunting and data analysis capabilities
    through XSIAM's XQL query language. Enables custom investigations, IOC searches,
    historical analysis, and cross-source data correlation.

    Tools provided:
        - run_xql_query: Execute XQL queries with automatic result polling
    """

    def register_tools(self):
        self._add_tool(run_xql_query)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
