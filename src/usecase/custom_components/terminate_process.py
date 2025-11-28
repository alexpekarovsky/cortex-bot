"""
Terminate Process Wrapper

Terminates processes by name on endpoints using the built-in process_kill_name script.
This is a wrapper around run_script that provides a simpler interface for process termination.
"""

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

# Script UID for process_kill_name (built-in Palo Alto Networks script)
PROCESS_KILL_SCRIPT_UID = "fd0a544a99a9421222b4f57a11839481"


async def terminate_process(
    ctx: Context,
    endpoint_id: Annotated[str, Field(description="The endpoint ID where the process should be terminated")],
    process_name: Annotated[str, Field(description="Name of the process to terminate (e.g., 'malware.exe', 'powershell.exe')")],
    timeout: Annotated[Optional[int], Field(description="Script execution timeout in seconds (default: 600)")] = 600,
) -> str:
    """
    Terminates a process by name on a specific endpoint.

    This tool uses the built-in 'process_kill_name' script to terminate all processes
    matching the specified name on the target endpoint. It's useful for stopping
    malicious processes during incident response.

    WARNING: This terminates ALL processes matching the name. Use with caution.
    For terminating an entire process tree (parent + children), use terminate_causality instead.

    Use this when:
    - You need to stop a specific process by name (e.g., 'malware.exe')
    - You want to kill all instances of a process (e.g., all 'powershell.exe')
    - Quick remediation of known malicious process names
    - The process name is known but you don't have the causality ID

    Use terminate_causality instead when:
    - You have the causality ID from an alert
    - You need to kill the entire process tree (parent and children)
    - More surgical precision is needed

    Args:
        ctx: The FastMCP context.
        endpoint_id: The endpoint ID where the process is running.
        process_name: Name of the process to terminate (e.g., 'malware.exe').
        timeout: Script execution timeout in seconds (default: 600).

    Returns:
        JSON response with action_id for tracking the termination.
    """
    try:
        logger.info(f"Terminating process '{process_name}' on endpoint {endpoint_id}")

        fetcher = await get_fetcher(ctx)

        # Build the run_script request
        payload = {
            "request_data": {
                "script_uid": PROCESS_KILL_SCRIPT_UID,
                "timeout": timeout,
                "filters": [
                    {
                        "field": "endpoint_id_list",
                        "operator": "in",
                        "value": [endpoint_id]
                    }
                ],
                "parameters_values": {
                    "process_name": process_name
                }
            }
        }

        response = await fetcher.send_request(
            "/public_api/v1/scripts/run_script/",
            data=payload
        )

        # Add context to the response
        result = {
            "endpoint_id": endpoint_id,
            "process_name": process_name,
            "script_used": "process_kill_name",
            "script_uid": PROCESS_KILL_SCRIPT_UID,
            "response": response,
            "status": "Process termination initiated - use get_action_status to monitor progress"
        }

        if response.get("reply", {}).get("action_id"):
            result["action_id"] = response["reply"]["action_id"]

        return create_response(data=result)

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while terminating process: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to terminate process: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class TerminateProcessModule(BaseModule):
    """
    Module for terminating processes by name on endpoints.

    This module wraps the built-in 'process_kill_name' script to provide
    a simple interface for process termination during incident response.

    Tools provided:
        - terminate_process: Kill processes by name on an endpoint
    """

    def register_tools(self):
        self._add_tool(terminate_process)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
