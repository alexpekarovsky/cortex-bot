"""
XSOAR Integration Discovery Tool

Discovers available XSOAR integrations, their commands, and active instances.
This is critical for knowing what threat intelligence and automation capabilities
are available in the XSIAM environment.

Uses the War Room API (/entries/insert + /entries/get) to run !GetInstances.
The XSIAM public API does not expose a dedicated endpoint for listing SOAR
integration instances — War Room is the only supported method.

War Room commands require a case_id (incident ID), NOT an alert/issue ID.
If no case_id is provided, the tool automatically finds a recent case.
"""

import asyncio
import json
import logging
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


async def _find_case_id(ctx: Context) -> str:
    """
    Finds a recent case ID suitable for War Room commands.

    Queries the cases API for a recent case. War Room commands require
    a case/incident ID — alert/issue IDs do not work.

    Args:
        ctx: The FastMCP context.

    Returns:
        str: A valid case ID for War Room commands.

    Raises:
        RuntimeError: If unable to find a case.
    """
    fetcher = await get_fetcher(ctx)

    try:
        payload = {
            "request_data": {
                "search_from": 0,
                "search_to": 5,
                "sort": {"field": "creation_time", "keyword": "desc"}
            }
        }

        cases_response = await fetcher.send_request(
            path="case/search/",
            method="POST",
            data=payload
        )

        if isinstance(cases_response, dict):
            reply = cases_response.get("reply", cases_response)
            cases = reply.get("DATA", reply.get("data", []))
            for case in cases:
                candidate_id = case.get("case_id") or case.get("id")
                if candidate_id:
                    case_id = str(candidate_id)
                    logger.info(f"Auto-found case_id for War Room: {case_id}")
                    return case_id

    except Exception as e:
        logger.warning(f"Failed to query cases API: {e}")

    raise RuntimeError(
        "Could not find a case for War Room commands. "
        "Please provide a case_id manually, or create an issue with "
        "MEDIUM+ severity so it gets grouped into a Case."
    )


async def _run_war_room_command(ctx: Context, case_id: str, command: str, timeout_seconds: int = 20) -> dict:
    """
    Executes an XSOAR command via War Room and waits for results.

    Args:
        ctx: The FastMCP context.
        case_id: Case/incident ID with an active War Room.
        command: XSOAR command string (e.g., '!GetInstances instance_status="active"').
        timeout_seconds: Maximum seconds to wait for results.

    Returns:
        dict with 'success' bool and 'results' list, or error info.
    """
    from datetime import datetime

    fetcher = await get_fetcher(ctx)

    # Send command to War Room
    try:
        response = await fetcher.send_request(
            path="/entries/insert",
            method="POST",
            data={"id": case_id, "data": command}
        )
    except Exception as e:
        error_str = str(e)
        if "Could not find investigations" in error_str:
            return {
                "success": False,
                "error": f"Case {case_id} does not have a War Room. "
                         "Try a different case_id, or provide a case that has been investigated."
            }
        return {"success": False, "error": f"War Room command failed: {e}"}

    if not isinstance(response, dict):
        return {"success": False, "error": "Unexpected response from War Room"}

    command_timestamp = response.get("created", "")
    if not command_timestamp:
        return {"success": False, "error": "No timestamp in War Room response"}

    command_time = datetime.fromisoformat(command_timestamp.replace('Z', '+00:00'))
    command_name = command.split()[0].lstrip("!")

    # Poll for results
    start_time = asyncio.get_running_loop().time()
    collected_results = []
    seen_entry_ids = set()

    while (asyncio.get_running_loop().time() - start_time) < timeout_seconds:
        try:
            entries_response = await fetcher.send_request(
                path="/entries/get",
                method="POST",
                data={"id": case_id, "filter": {"pagesize": 25}}
            )

            if isinstance(entries_response, dict) and "data" in entries_response:
                for entry in entries_response["data"]:
                    entry_id = entry.get("id")
                    if entry_id in seen_entry_ids:
                        continue

                    parent_content = entry.get("parentContent", "")
                    content = entry.get("contents", "")

                    # Detect platform panic errors
                    if content and "Panic" in content and "runtime error" in content:
                        seen_entry_ids.add(entry_id)
                        return {
                            "success": False,
                            "error": "XSIAM platform error: War Room command caused a server-side panic. "
                                     "This is a known platform issue. The command cannot be executed via the API at this time.",
                            "platform_error": content,
                        }

                    if (entry.get("category") == "artifact" and
                            parent_content and
                            f"!{command_name}" in parent_content):

                        entry_created = entry.get("created", "")
                        if entry_created:
                            entry_time = datetime.fromisoformat(entry_created.replace('Z', '+00:00'))
                            if entry_time > command_time:
                                if content and len(content) > 5:
                                    seen_entry_ids.add(entry_id)
                                    collected_results.append({
                                        "content": content,
                                        "format": entry.get("format", "text"),
                                    })

            if collected_results:
                if (asyncio.get_running_loop().time() - start_time) < 5:
                    await asyncio.sleep(2)
                else:
                    break

            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"Error polling War Room for {command_name}: {e}")
            await asyncio.sleep(2)

    if collected_results:
        return {"success": True, "results": collected_results}

    return {
        "success": False,
        "timeout": True,
        "error": f"No results within {timeout_seconds}s for {command}. Check War Room manually."
    }


def _parse_instances_to_integrations(raw_content: str, only_enabled: bool = True) -> dict:
    """
    Parse !GetInstances War Room output into a structured integration list.

    The War Room returns instance data as JSON or markdown table. This function
    normalizes it into a structured format.
    """
    integrations_by_brand = {}

    # Try parsing as JSON first
    try:
        if isinstance(raw_content, str):
            data = json.loads(raw_content)
        else:
            data = raw_content

        if isinstance(data, list):
            instances = data
        elif isinstance(data, dict):
            instances = [data]
        else:
            instances = []

        for instance in instances:
            brand = instance.get("brand", instance.get("name", "Unknown"))
            enabled = instance.get("enabled", "true")
            if isinstance(enabled, str):
                enabled = enabled.lower() == "true"

            if only_enabled and not enabled:
                continue

            if brand not in integrations_by_brand:
                integrations_by_brand[brand] = {
                    "name": brand,
                    "display_name": brand,
                    "category": instance.get("category", "Unknown"),
                    "description": instance.get("description", ""),
                    "instances": [],
                }

            integrations_by_brand[brand]["instances"].append({
                "name": instance.get("name", brand),
                "enabled": enabled,
                "brand": brand,
            })

        if integrations_by_brand:
            result_list = list(integrations_by_brand.values())
            return {
                "total_count": len(result_list),
                "integrations": result_list,
            }

    except (json.JSONDecodeError, TypeError):
        pass

    # If JSON parsing failed, return the raw content
    return {
        "total_count": 0,
        "integrations": [],
        "raw_output": raw_content if isinstance(raw_content, str) else str(raw_content),
        "note": "Could not parse structured data. Raw War Room output included."
    }


async def list_integrations(
    ctx: Context,
    integration_filter: Annotated[Optional[str], Field(
        description="Optional filter to search for specific integrations by name"
    )] = None,
    only_enabled: Annotated[bool, Field(
        description="If True, only return enabled integrations (default: True)"
    )] = True,
    case_id: Annotated[Optional[str], Field(
        description="Case/incident ID for War Room execution. If not provided, "
                    "one will be found automatically from recent cases."
    )] = None,
) -> str:
    """
    Retrieves list of all XSOAR integrations and automation capabilities available in XSIAM.

    This tool discovers what threat intelligence sources, automation tools, and security
    integrations are configured in your XSIAM instance.

    Use this to:
    - Discover available threat intelligence integrations (VirusTotal, Google TI, etc.)
    - Find enrichment commands for indicators (!ip, !file, !domain, !url)
    - List automation and remediation integrations
    - Identify SIEM, SOAR, and ticketing system connections

    The tool runs !GetInstances via the War Room API. If no case_id is provided,
    it automatically finds a recent case to use as a workspace.

    NOTE: War Room commands require a case_id (incident ID), not an alert/issue ID.

    Args:
        ctx: The FastMCP context.
        integration_filter: Optional filter to search for specific integrations by name.
        only_enabled: If True, only return enabled integrations (default: True).
        case_id: Case/incident ID for War Room. Auto-detected if not provided.

    Returns:
        JSON response containing list of integrations with their instances.
    """
    if not case_id:
        try:
            case_id = await _find_case_id(ctx)
        except RuntimeError as e:
            return create_response(
                data={
                    "error": str(e),
                    "hint": "Provide a case_id parameter (incident ID, not alert ID)."
                },
                is_error=True
            )

    status_filter = "active" if only_enabled else "both"
    command = f'!GetInstances instance_status="{status_filter}"'
    if integration_filter:
        command += f' brand="{integration_filter}"'

    war_room_result = await _run_war_room_command(ctx, case_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_to_integrations(raw_content, only_enabled)
        parsed["case_id_used"] = case_id
        return create_response(data=parsed)

    error_msg = war_room_result.get("error", "Unknown error")
    result = {
        "error": f"Failed to retrieve integrations via War Room: {error_msg}",
        "case_id_used": case_id,
        "hint": "The case may not have an active War Room. Try providing a different case_id."
    }
    if war_room_result.get("platform_error"):
        result["platform_error"] = war_room_result["platform_error"]
    return create_response(data=result, is_error=True)


async def get_integration_commands(
    ctx: Context,
    integration_name: Annotated[str, Field(
        description="Name of the integration to get commands for (e.g., 'VirusTotal', 'ActiveDirectory')"
    )],
    case_id: Annotated[Optional[str], Field(
        description="Case/incident ID for War Room execution. If not provided, "
                    "one will be found automatically from recent cases."
    )] = None,
) -> str:
    """
    Retrieves instance information for a specific XSOAR integration.

    Runs !GetInstances via War Room filtered by the integration brand name.
    Returns instance details including enabled status and configuration.

    Note: Full command-level details (arguments, outputs) are not available
    through the War Room API. For command discovery, use run_xsoar_automation
    with commands like '!integration_name-help' in the War Room.

    NOTE: War Room commands require a case_id (incident ID), not an alert/issue ID.

    Args:
        ctx: The FastMCP context.
        integration_name: Name of the integration (e.g., 'VirusTotal', 'ActiveDirectory').
        case_id: Case/incident ID for War Room. Auto-detected if not provided.

    Returns:
        JSON response with integration instance information.
    """
    if not case_id:
        try:
            case_id = await _find_case_id(ctx)
        except RuntimeError as e:
            return create_response(
                data={
                    "error": str(e),
                    "hint": "Provide a case_id parameter (incident ID, not alert ID)."
                },
                is_error=True
            )

    command = f'!GetInstances brand="{integration_name}"'
    war_room_result = await _run_war_room_command(ctx, case_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_to_integrations(raw_content, only_enabled=False)

        return create_response(data={
            "integration_name": integration_name,
            "case_id_used": case_id,
            "note": "Instance details retrieved via War Room. For full command details, "
                    "use run_xsoar_automation with '!<command>-help' in the War Room.",
            **parsed,
        })

    error_msg = war_room_result.get("error", "Unknown error")
    result = {
        "error": f"Failed to retrieve integration '{integration_name}' via War Room: {error_msg}",
        "case_id_used": case_id,
        "hint": "The case may not have an active War Room, or the integration name may be incorrect."
    }
    if war_room_result.get("platform_error"):
        result["platform_error"] = war_room_result["platform_error"]
    return create_response(data=result, is_error=True)


class IntegrationDiscoveryModule(BaseModule):
    """
    MCP module for discovering XSOAR integrations and their capabilities.

    Tools provided:
        - list_integrations: List all available XSOAR integrations
        - get_integration_commands: Get instance info for specific integration
    """

    def register_tools(self):
        self._add_tool(list_integrations)
        self._add_tool(get_integration_commands)

    def register_resources(self):
        pass
