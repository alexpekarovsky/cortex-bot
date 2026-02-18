"""
XSOAR Automation Command Wrapper

Generic wrapper that can execute ANY XSOAR automation command in the War Room
and automatically retrieve results. This provides unlimited extensibility for
running any XSOAR integration command without creating dedicated wrappers.
"""

import asyncio
import logging
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def _wait_for_automation_results(
    ctx: Context,
    investigation_id: str,
    command_timestamp: str,
    command_name: str,
    timeout_seconds: int = 20
) -> dict:
    """
    Waits for XSOAR automation command results to appear in the War Room.

    Polls War Room entries to collect ALL responses for the specific command.
    Handles parallel commands by matching results to the command name.

    Args:
        ctx: The FastMCP context.
        investigation_id: Case or alert ID.
        command_timestamp: ISO timestamp when command was created.
        command_name: The command name (e.g., "GetInstances", "ip", "file").
        timeout_seconds: Maximum seconds to wait (default: 20).

    Returns:
        dict: All automation results or timeout message.
    """
    from datetime import datetime

    fetcher = await get_fetcher(ctx)
    start_time = asyncio.get_event_loop().time()
    command_time = datetime.fromisoformat(command_timestamp.replace('Z', '+00:00'))

    collected_results = []
    seen_entry_ids = set()

    # Poll for results
    while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
        try:
            entries_response = await fetcher.send_request(
                path="/entries/get",
                method="POST",
                data={"id": investigation_id, "filter": {"pagesize": 25}}
            )

            if isinstance(entries_response, dict) and "data" in entries_response:
                entries = entries_response["data"]

                # Look for ALL artifact entries that came AFTER our command
                for entry in entries:
                    entry_id = entry.get("id")

                    # Skip if already processed
                    if entry_id in seen_entry_ids:
                        continue

                    # Check if this is a response to our command (artifact category)
                    parent_content = entry.get("parentContent", "")
                    if (entry.get("category") == "artifact" and
                        parent_content and
                        f"!{command_name}" in parent_content):

                        # Parse entry timestamp
                        entry_created = entry.get("created", "")
                        if entry_created:
                            entry_time = datetime.fromisoformat(entry_created.replace('Z', '+00:00'))

                            # Only consider entries created AFTER our command
                            if entry_time > command_time:
                                content = entry.get("contents", "")

                                # Collect all non-empty responses
                                if content and len(content) > 5:
                                    seen_entry_ids.add(entry_id)

                                    result_entry = {
                                        "entry_id": entry_id,
                                        "created": entry_created,
                                        "content": content,
                                        "format": entry.get("format", "text"),
                                        "is_error": "Error" in content or "error" in content.lower(),
                                        "parent_command": parent_content
                                    }
                                    collected_results.append(result_entry)

            # If we have results, wait a bit more to catch additional responses
            if collected_results:
                if (asyncio.get_event_loop().time() - start_time) < 5:
                    await asyncio.sleep(2)
                else:
                    # Enough time passed, return results
                    break

            # Wait before next poll
            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"Error polling for automation results: {e}")
            await asyncio.sleep(2)

    # Return collected results
    if collected_results:
        errors = [r for r in collected_results if r["is_error"]]
        successes = [r for r in collected_results if not r["is_error"]]

        return {
            "success": len(successes) > 0,
            "total_results": len(collected_results),
            "results": collected_results,
            "successful_results": successes,
            "errors": errors,
            "summary": f"Collected {len(collected_results)} automation results ({len(successes)} successful, {len(errors)} errors)"
        }

    # Timeout reached with no results
    return {
        "success": False,
        "timeout": True,
        "message": f"No automation results found within {timeout_seconds} seconds for command !{command_name}. Check War Room manually."
    }


async def run_xsoar_automation(
    ctx: Context,
    command: Annotated[str, Field(description="XSOAR command to execute (e.g., '!GetInstances instance_status=\"both\"' or '!ip ip=1.1.1.1')")],
    alert_id: Annotated[Optional[str], Field(description="Alert ID to run command in (e.g., '6126')")] = None,
    case_id: Annotated[Optional[str], Field(description="Case ID to run command in (e.g., '350')")] = None,
    wait_for_results: Annotated[bool, Field(description="Wait for and return automation results (default: True)", default=True)] = True,
    timeout_seconds: Annotated[int, Field(description="Seconds to wait for results (default: 20)", default=20)] = 20,
) -> str:
    """
    Executes ANY XSOAR automation command in the War Room and retrieves results.

    This is a universal wrapper that can run any XSOAR integration command, automation
    script, or enrichment command. It automatically waits for and retrieves results
    from XSOAR integrations.

    =====================================================================
    CHOOSING THE RIGHT CONTEXT FOR AUTOMATION COMMANDS
    =====================================================================

    **OPTION 1: GENERAL COMMANDS** (recommended for ad-hoc automation)
    ─────────────────────────────────────────────────────────────────
    When running commands not tied to a specific investigation:

    1. Create a workspace: workspace = create_issue()
    2. Use the returned alert_id: run_xsoar_automation(command="!GetInstances", alert_id=workspace["alert_id"])

    This keeps general automation separate from real investigations.

    **OPTION 2: CASE-SPECIFIC AUTOMATION** (for active incidents)
    ─────────────────────────────────────────────────────────────────
    When running commands in context of a specific alert/case:

    1. Get case details: case_data = get_incident_extra_data(incident_id="100")
    2. Find an alert_id from the case's issues (e.g., "12345")
    3. Run command: run_xsoar_automation(command="!ip ip=8.8.8.8", alert_id="12345")

    Results appear in the specific issue's War Room, documenting your investigation.

    KEY CONCEPTS:
    - CASE (incident): Container for related security events
    - ISSUE (alert): Individual security event INSIDE a Case
    - War Room: Investigation workspace attached to an ISSUE
    - War Room commands run on ISSUES, not Cases directly
    =====================================================================

    Use this tool when:
    - Running discovery commands (!GetInstances, !GetIntegrations)
    - Executing enrichment commands (!ip, !file, !domain, !url, !email)
    - Running automation scripts (!Print, !SetIncident, !AssignToMe)
    - Querying integrations (!vt-get-file-report, !qradar-search, !ad-get-user)
    - Executing ANY custom XSOAR command available in your instance
    - Testing integration availability

    Do NOT use this for:
    - IP enrichment - use enrich_ip_address instead (simpler)
    - File hash enrichment - use enrich_file_hash instead (simpler)
    - Domain enrichment - use enrich_domain instead (simpler)
    - URL enrichment - use enrich_url instead (simpler)

    Examples:
    - Discovery: !GetInstances instance_status="both"
    - Enrichment: !ip ip=8.8.8.8
    - VirusTotal: !vt-get-file-report file=abc123def456
    - QRadar: !qradar-search query="SELECT * FROM events LIMIT 10"
    - Active Directory: !ad-get-user username=john.doe

    Args:
        ctx: The FastMCP context.
        command: Full XSOAR command starting with ! (e.g., "!GetInstances instance_status=\"both\"").
        alert_id: Alert ID to run command in (e.g., "12345").
        case_id: Case ID to run command in (e.g., "100").
        wait_for_results: If True, wait for automation results (default: True).
        timeout_seconds: Maximum seconds to wait for results (default: 20).

    Returns:
        JSON response with command execution status and automation results (if wait_for_results=True).
    """
    if not case_id and not alert_id:
        return create_response(
            data={"error": "Either case_id or alert_id must be provided"},
            is_error=True
        )

    # Validate command starts with !
    if not command.startswith("!"):
        return create_response(
            data={"error": "XSOAR commands must start with ! (e.g., '!GetInstances')"},
            is_error=True
        )

    investigation_id = case_id if case_id else alert_id

    # Extract command name (first word after !)
    command_name = command.split()[0][1:]  # Remove ! and get command name

    logger.info(f"Running XSOAR automation command: {command} in investigation {investigation_id}")

    try:
        fetcher = await get_fetcher(ctx)

        # Send command to War Room
        request_data = {
            "id": investigation_id,
            "data": command
        }

        response = await fetcher.send_request(
            path="/entries/insert",
            method="POST",
            data=request_data
        )

        if isinstance(response, dict):
            entry_id = response.get("id")
            command_timestamp = response.get("created")

            result = {
                "entry_id": entry_id,
                "investigation_id": response.get("investigationId"),
                "command_executed": command,
                "command_name": command_name,
                "created": command_timestamp,
            }

            # Optionally wait for results
            if wait_for_results:
                logger.info(f"Waiting for automation results for command {command_name}...")
                automation_result = await _wait_for_automation_results(
                    ctx=ctx,
                    investigation_id=investigation_id,
                    command_timestamp=command_timestamp,
                    command_name=command_name,
                    timeout_seconds=timeout_seconds
                )

                result["automation_results"] = automation_result
                result["status"] = "Automation completed" if automation_result.get("success") else "Automation command executed - check War Room for results"
            else:
                result["status"] = "Command sent to War Room - results not retrieved"

            return create_response(data=result)

        return create_response(data=response)

    except Exception as e:
        logger.exception(f"Failed to execute XSOAR automation command: {e}")
        return create_response(
            data={"error": f"Failed to execute automation: {str(e)}"},
            is_error=True
        )


class RunXSOARAutomationModule(BaseModule):
    """Module for running generic XSOAR automation commands via War Room"""

    def register_tools(self):
        self._add_tool(run_xsoar_automation)

    def register_resources(self):
        pass
