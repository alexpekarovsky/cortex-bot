"""
XSOAR Integration Discovery Tool

Discovers available XSOAR integrations, their commands, and active instances.
This is critical for knowing what threat intelligence and automation capabilities
are available in the XSIAM environment.

Uses the /settings/integration-search API when available, falling back to
!GetInstances via War Room when the API endpoint returns errors (BUG-001).
"""

import asyncio
import logging
from typing import Annotated, Optional

from fastmcp import Context
from pydantic import Field

from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)


async def _run_war_room_command(ctx, investigation_id: str, command: str, timeout_seconds: int = 20) -> dict:
    """
    Executes an XSOAR command via War Room and waits for results.

    Args:
        ctx: The FastMCP context.
        investigation_id: Alert or case ID to run the command in.
        command: XSOAR command string (e.g., '!GetInstances instance_status="active"').
        timeout_seconds: Maximum seconds to wait for results.

    Returns:
        dict with 'success' bool and 'results' list, or error info.
    """
    from datetime import datetime

    from usecase.fetcher import get_fetcher

    fetcher = await get_fetcher(ctx)

    # Send command to War Room
    response = await fetcher.send_request(
        path="/entries/insert",
        method="POST",
        data={"id": investigation_id, "data": command}
    )

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
                data={"id": investigation_id, "filter": {"pagesize": 25}}
            )

            if isinstance(entries_response, dict) and "data" in entries_response:
                for entry in entries_response["data"]:
                    entry_id = entry.get("id")
                    if entry_id in seen_entry_ids:
                        continue

                    parent_content = entry.get("parentContent", "")
                    if (entry.get("category") == "artifact" and
                            parent_content and
                            f"!{command_name}" in parent_content):

                        entry_created = entry.get("created", "")
                        if entry_created:
                            entry_time = datetime.fromisoformat(entry_created.replace('Z', '+00:00'))
                            if entry_time > command_time:
                                content = entry.get("contents", "")
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

    The War Room returns instance data as a markdown table or JSON. This function
    normalizes it into the same shape as the API response.
    """
    import json

    integrations_by_brand = {}

    # Try parsing as JSON first (some XSOAR versions return JSON)
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
                "source": "war_room_fallback",
                "note": "Retrieved via !GetInstances. Command-level details are not available through this method."
            }

    except (json.JSONDecodeError, TypeError):
        pass

    # If JSON parsing failed, return the raw content
    return {
        "total_count": 0,
        "integrations": [],
        "raw_output": raw_content if isinstance(raw_content, str) else str(raw_content),
        "source": "war_room_fallback",
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
    alert_id: Annotated[Optional[str], Field(
        description="Alert ID for War Room fallback. If the API endpoint fails, this is used to run !GetInstances via War Room."
    )] = None,
    case_id: Annotated[Optional[str], Field(
        description="Case ID for War Room fallback (alternative to alert_id)."
    )] = None,
) -> str:
    """
    Retrieves list of all XSOAR integrations and automation capabilities available in XSIAM.

    This tool discovers what threat intelligence sources, automation tools, and security
    integrations are configured in your XSIAM instance. Essential for understanding what
    enrichment commands and automation capabilities are available for investigations.

    Use this to:
    - Discover available threat intelligence integrations (VirusTotal, Google TI, etc.)
    - Find enrichment commands for indicators (!ip, !file, !domain, !url)
    - List automation and remediation integrations
    - Identify SIEM, SOAR, and ticketing system connections
    - Understand what War Room commands are available

    The tool first tries the XSIAM API. If that fails (some tenants return 500 on
    /settings/integration-search), it falls back to running !GetInstances via War Room,
    which requires an alert_id or case_id.

    Args:
        ctx: The FastMCP context.
        integration_filter: Optional filter to search for specific integrations by name.
        only_enabled: If True, only return enabled integrations (default: True).
        alert_id: Alert ID for War Room fallback (e.g., '12345').
        case_id: Case ID for War Room fallback (e.g., '100').

    Returns:
        JSON response containing list of integrations with their commands and capabilities.
    """
    from usecase.fetcher import get_fetcher

    fetcher = await get_fetcher(ctx)

    # Try the API endpoint first
    try:
        endpoint = "/settings/integration-search"
        request_data = {}
        if integration_filter:
            request_data["query"] = integration_filter

        response = await fetcher.send_request(
            path=endpoint,
            method="POST",
            data=request_data
        )

        # Check if the response is valid (not an error)
        if isinstance(response, dict) and "integrations" in response:
            integrations = response["integrations"]

            if only_enabled:
                integrations = [
                    integration for integration in integrations
                    if integration.get("enabled", False) or
                       any(instance.get("enabled", False) for instance in integration.get("instances", []))
                ]

            result = {
                "total_count": len(integrations),
                "integrations": [],
                "source": "api",
            }

            for integration in integrations:
                integration_info = {
                    "name": integration.get("name"),
                    "display_name": integration.get("display"),
                    "category": integration.get("category"),
                    "description": integration.get("description"),
                    "commands": [],
                    "instances": []
                }

                commands = integration.get("script", {}).get("commands", [])
                for cmd in commands:
                    integration_info["commands"].append({
                        "name": cmd.get("name"),
                        "description": cmd.get("description"),
                        "deprecated": cmd.get("deprecated", False)
                    })

                instances = integration.get("instances", [])
                for instance in instances:
                    integration_info["instances"].append({
                        "name": instance.get("name"),
                        "enabled": instance.get("enabled", False),
                        "brand": instance.get("brand")
                    })

                result["integrations"].append(integration_info)

            return create_response(data=result)

    except Exception as e:
        logger.warning(f"API endpoint /settings/integration-search failed: {e}")

    # API failed — fall back to War Room !GetInstances
    logger.info("Falling back to War Room !GetInstances")
    investigation_id = alert_id or case_id
    if not investigation_id:
        return create_response(
            data={
                "error": "The /settings/integration-search API endpoint returned an error. "
                         "To use the War Room fallback, provide an alert_id or case_id parameter. "
                         "You can create a workspace with create_issue() first.",
                "workaround": 'run_xsoar_automation(command=\'!GetInstances instance_status="active"\', alert_id="<your_alert_id>")'
            },
            is_error=True
        )

    status_filter = "active" if only_enabled else "both"
    command = f'!GetInstances instance_status="{status_filter}"'
    if integration_filter:
        command += f' brand="{integration_filter}"'

    war_room_result = await _run_war_room_command(ctx, investigation_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        # Parse the first result
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_to_integrations(raw_content, only_enabled)
        return create_response(data=parsed)

    return create_response(
        data={
            "error": "Both API and War Room fallback failed to retrieve integrations.",
            "api_error": "500 Internal Server Error on /settings/integration-search",
            "war_room_error": war_room_result.get("error", "Unknown error"),
        },
        is_error=True
    )


async def get_integration_commands(
    ctx: Context,
    integration_name: Annotated[str, Field(
        description="Name of the integration to get commands for (e.g., 'VirusTotal', 'ActiveDirectory')"
    )],
    alert_id: Annotated[Optional[str], Field(
        description="Alert ID for War Room fallback. If the API endpoint fails, this is used to query via War Room."
    )] = None,
    case_id: Annotated[Optional[str], Field(
        description="Case ID for War Room fallback (alternative to alert_id)."
    )] = None,
) -> str:
    """
    Retrieves detailed command information for a specific XSOAR integration.

    Use this to understand what commands an integration provides and how to use them
    in War Room for investigations. Essential before running enrichment or automation
    commands.

    The response includes:
    - Command names (e.g., 'ip', 'file', 'vt-get-file-report')
    - Detailed descriptions
    - Input parameters and types
    - Output context paths

    The tool first tries the XSIAM API. If that fails (some tenants return 500 on
    /settings/integration-search), it falls back to running !GetInstances via War Room,
    which provides instance info but not full command details.

    Args:
        ctx: The FastMCP context.
        integration_name: Name of the integration (e.g., 'VirusTotal', 'ActiveDirectory').
        alert_id: Alert ID for War Room fallback (e.g., '12345').
        case_id: Case ID for War Room fallback (e.g., '100').

    Returns:
        JSON response with detailed command information for the integration.
    """
    from usecase.fetcher import get_fetcher

    fetcher = await get_fetcher(ctx)

    # Try the API endpoint first
    try:
        endpoint = "/settings/integration-search"
        response = await fetcher.send_request(
            path=endpoint,
            method="POST",
            data={"query": integration_name}
        )

        if isinstance(response, dict) and "integrations" in response:
            integrations = response["integrations"]

            matching = None
            for integration in integrations:
                if (integration.get("name", "").lower() == integration_name.lower() or
                        integration.get("display", "").lower() == integration_name.lower()):
                    matching = integration
                    break

            if matching:
                commands = matching.get("script", {}).get("commands", [])
                return create_response(data={
                    "integration_name": matching.get("display"),
                    "category": matching.get("category"),
                    "description": matching.get("description"),
                    "total_commands": len(commands),
                    "source": "api",
                    "commands": [
                        {
                            "name": cmd.get("name"),
                            "description": cmd.get("description"),
                            "deprecated": cmd.get("deprecated", False),
                            "arguments": cmd.get("arguments", []),
                            "outputs": cmd.get("outputs", [])
                        }
                        for cmd in commands
                    ]
                })
            else:
                return create_response(data={
                    "error": f"Integration '{integration_name}' not found",
                    "available_integrations": [i.get("display") for i in integrations[:20]]
                })

    except Exception as e:
        logger.warning(f"API endpoint /settings/integration-search failed: {e}")

    # API failed — fall back to War Room
    logger.info(f"Falling back to War Room for integration '{integration_name}'")
    investigation_id = alert_id or case_id
    if not investigation_id:
        return create_response(
            data={
                "error": "The /settings/integration-search API endpoint returned an error. "
                         "To use the War Room fallback, provide an alert_id or case_id parameter. "
                         "You can create a workspace with create_issue() first.",
                "workaround": f'run_xsoar_automation(command=\'!GetInstances brand="{integration_name}"\', alert_id="<your_alert_id>")'
            },
            is_error=True
        )

    command = f'!GetInstances brand="{integration_name}"'
    war_room_result = await _run_war_room_command(ctx, investigation_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_to_integrations(raw_content, only_enabled=False)

        return create_response(data={
            "integration_name": integration_name,
            "source": "war_room_fallback",
            "note": "Retrieved via !GetInstances. Full command details are only available when the API endpoint works.",
            "instances": parsed.get("integrations", []),
            "raw_output": parsed.get("raw_output"),
        })

    return create_response(
        data={
            "error": f"Both API and War Room fallback failed for integration '{integration_name}'.",
            "api_error": "500 Internal Server Error on /settings/integration-search",
            "war_room_error": war_room_result.get("error", "Unknown error"),
        },
        is_error=True
    )


class IntegrationDiscoveryModule(BaseModule):
    """
    MCP module for discovering XSOAR integrations and their capabilities.

    Provides tools to discover what threat intelligence sources, automation integrations,
    and security tools are configured in the XSIAM instance.

    Tools provided:
        - list_integrations: List all available XSOAR integrations
        - get_integration_commands: Get detailed command info for specific integration
    """

    def register_tools(self):
        self._add_tool(list_integrations)
        self._add_tool(get_integration_commands)

    def register_resources(self):
        pass
