"""
XSOAR Integration Discovery Tool

Discovers available XSOAR integrations, their commands, and active instances.
This is critical for knowing what threat intelligence and automation capabilities
are available in the XSIAM environment.

Approach priority:
1. XSOAR internal API (/xsoar/public/v1/settings/integration/search) — direct query
2. War Room (!GetInstances via /entries/insert + /entries/get) — fallback
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

# XSOAR internal API paths to try for listing integration instances
XSOAR_INTEGRATION_PATHS = [
    "/xsoar/public/v1/settings/integration/search",
    "/xsoar/public/v1/settings/integration-search",
]


async def _query_integrations_via_xsoar_api(ctx: Context, integration_filter: Optional[str] = None) -> Optional[dict]:
    """
    Try to query integrations via XSOAR internal API endpoints.

    XSIAM exposes XSOAR APIs at /xsoar/public/v1/. This function tries
    known XSOAR endpoints for listing integration instances.

    Returns parsed integration data or None if no endpoint works.
    """
    fetcher = await get_fetcher(ctx)

    # Build search payload
    payload = {}
    if integration_filter:
        payload = {"name": integration_filter}

    for path in XSOAR_INTEGRATION_PATHS:
        try:
            logger.info(f"Trying XSOAR API path: {path}")
            response = await fetcher.send_request(
                path=path,
                method="POST",
                data=payload,
                omit_papi_prefix=True
            )

            if isinstance(response, dict):
                # XSOAR returns integration instances directly
                instances = response.get("instances", response.get("configurations", []))
                if isinstance(response, list):
                    instances = response

                logger.info(f"XSOAR API {path} returned {len(instances) if isinstance(instances, list) else 'dict'} result(s)")
                return {"source": "xsoar_api", "path": path, "data": response}

        except Exception as e:
            error_str = str(e)
            logger.info(f"XSOAR API path {path} failed: {error_str[:200]}")
            # 303 redirect means the path exists but redirects — try next
            # 400/404 means invalid — try next
            # 401/403 means auth issue — try next but log warning
            if "401" in error_str or "403" in error_str:
                logger.warning(f"Auth error on {path} — API key may lack SOAR permissions")
            continue

    return None


async def _find_alert_id(ctx: Context) -> str:
    """
    Finds a recent alert/issue ID suitable for War Room commands.

    Queries the issues API for a recent issue. War Room commands must target
    alert/issue IDs — case IDs cause a server-side panic via the public API.
    """
    fetcher = await get_fetcher(ctx)

    try:
        payload = {
            "request_data": {
                "search_from": 0,
                "search_to": 5,
                "sort": {"field": "observation_time", "keyword": "desc"}
            }
        }

        issues_response = await fetcher.send_request(
            path="/issue/search/",
            method="POST",
            data=payload
        )

        if isinstance(issues_response, dict):
            reply = issues_response.get("reply", issues_response)
            issues = reply.get("DATA", reply.get("data", []))
            for issue in issues:
                candidate_id = issue.get("id") or issue.get("alert_id")
                if candidate_id:
                    alert_id = str(candidate_id)
                    logger.info(f"Auto-found alert_id for War Room: {alert_id}")
                    return alert_id

    except Exception as e:
        logger.warning(f"Failed to query issues API: {e}")

    raise RuntimeError(
        "Could not find an alert/issue for War Room commands. "
        "Please provide an alert_id manually, or create an issue with "
        "create_issue first."
    )


async def _run_war_room_command(ctx: Context, alert_id: str, command: str, timeout_seconds: int = 20) -> dict:
    """
    Executes an XSOAR command via War Room and waits for results.

    IMPORTANT: Use alert/issue IDs, NOT case IDs. Case IDs cause a
    server-side panic via the public API. Alert/issue IDs work correctly.
    """
    from datetime import datetime

    fetcher = await get_fetcher(ctx)

    # Send command to War Room — must use alert/issue ID, not case ID
    request_data = {"id": alert_id, "data": command}

    try:
        response = await fetcher.send_request(
            path="/entries/insert",
            method="POST",
            data=request_data
        )
    except Exception as e:
        error_str = str(e)
        if "Could not find investigations" in error_str:
            return {
                "success": False,
                "error": f"Alert {alert_id} does not have a War Room. "
                         "Try a different alert_id, or create an issue with create_issue first."
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
                data={"id": alert_id, "filter": {"pagesize": 25}}
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


def _parse_instances_response(data, only_enabled: bool = True) -> dict:
    """
    Parse integration instances from either XSOAR API response or War Room output
    into a structured integration list.
    """
    integrations_by_brand = {}
    instances = []

    # Handle various response formats
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return {
                "total_count": 0,
                "integrations": [],
                "raw_output": data,
                "note": "Could not parse structured data. Raw output included."
            }

    if isinstance(data, list):
        instances = data
    elif isinstance(data, dict):
        # XSOAR API may return instances under various keys
        instances = (data.get("instances", None)
                     or data.get("configurations", None)
                     or data.get("reply", None)
                     or [data])
        if isinstance(instances, dict):
            instances = [instances]

    for instance in instances:
        if not isinstance(instance, dict):
            continue

        brand = instance.get("brand", instance.get("name", "Unknown"))
        enabled = instance.get("enabled", instance.get("isActive", "true"))
        if isinstance(enabled, str):
            enabled = enabled.lower() in ("true", "active")

        if only_enabled and not enabled:
            continue

        if brand not in integrations_by_brand:
            integrations_by_brand[brand] = {
                "name": brand,
                "display_name": instance.get("displayName", brand),
                "category": instance.get("category", "Unknown"),
                "description": instance.get("description", ""),
                "instances": [],
            }

        integrations_by_brand[brand]["instances"].append({
            "name": instance.get("name", brand),
            "enabled": enabled,
            "brand": brand,
        })

    result_list = list(integrations_by_brand.values())
    return {
        "total_count": len(result_list),
        "integrations": result_list,
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
        description="Alert/issue ID for War Room execution (fallback method). "
                    "Must be an alert/issue ID, NOT a case ID. "
                    "If not provided, one will be found automatically."
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

    The tool first tries the XSOAR internal API for listing integrations directly.
    If that fails, it falls back to running !GetInstances via the War Room API.

    Args:
        ctx: The FastMCP context.
        integration_filter: Optional filter to search for specific integrations by name.
        only_enabled: If True, only return enabled integrations (default: True).
        alert_id: Alert/issue ID for War Room fallback. Auto-detected if not provided.

    Returns:
        JSON response containing list of integrations with their instances.
    """
    # Approach 1: Try XSOAR internal API
    xsoar_result = await _query_integrations_via_xsoar_api(ctx, integration_filter)
    if xsoar_result is not None:
        parsed = _parse_instances_response(xsoar_result["data"], only_enabled)
        parsed["source"] = xsoar_result["source"]
        parsed["api_path"] = xsoar_result["path"]
        return create_response(data=parsed)

    # Approach 2: Fall back to War Room
    logger.info("XSOAR API paths unavailable, falling back to War Room")

    if not alert_id:
        try:
            alert_id = await _find_alert_id(ctx)
        except RuntimeError as e:
            return create_response(
                data={
                    "error": str(e),
                    "hint": "Provide an alert_id parameter (issue/alert ID, NOT case ID)."
                },
                is_error=True
            )

    status_filter = "active" if only_enabled else "both"
    command = f'!GetInstances instance_status="{status_filter}"'
    if integration_filter:
        command += f' brand="{integration_filter}"'

    war_room_result = await _run_war_room_command(ctx, alert_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_response(raw_content, only_enabled)
        parsed["source"] = "war_room"
        parsed["alert_id_used"] = alert_id
        return create_response(data=parsed)

    error_msg = war_room_result.get("error", "Unknown error")
    result = {
        "error": f"Failed to retrieve integrations: {error_msg}",
        "alert_id_used": alert_id,
        "methods_tried": ["xsoar_api", "war_room"],
        "hint": "Check API key permissions. The key may need an 'Instance Administrator' or similar role "
                "that includes SOAR integration access."
    }
    if war_room_result.get("platform_error"):
        result["platform_error"] = war_room_result["platform_error"]
    return create_response(data=result, is_error=True)


async def get_integration_commands(
    ctx: Context,
    integration_name: Annotated[str, Field(
        description="Name of the integration to get commands for (e.g., 'VirusTotal', 'ActiveDirectory')"
    )],
    alert_id: Annotated[Optional[str], Field(
        description="Alert/issue ID for War Room execution (fallback method). "
                    "Must be an alert/issue ID, NOT a case ID. "
                    "If not provided, one will be found automatically."
    )] = None,
) -> str:
    """
    Retrieves instance information for a specific XSOAR integration.

    First tries the XSOAR internal API filtered by integration name.
    Falls back to !GetInstances via War Room if the API is unavailable.

    Args:
        ctx: The FastMCP context.
        integration_name: Name of the integration (e.g., 'VirusTotal', 'ActiveDirectory').
        alert_id: Alert/issue ID for War Room fallback. Auto-detected if not provided.

    Returns:
        JSON response with integration instance information.
    """
    # Approach 1: Try XSOAR internal API
    xsoar_result = await _query_integrations_via_xsoar_api(ctx, integration_name)
    if xsoar_result is not None:
        parsed = _parse_instances_response(xsoar_result["data"], only_enabled=False)
        return create_response(data={
            "integration_name": integration_name,
            "source": xsoar_result["source"],
            "api_path": xsoar_result["path"],
            **parsed,
        })

    # Approach 2: Fall back to War Room
    logger.info("XSOAR API paths unavailable, falling back to War Room")

    if not alert_id:
        try:
            alert_id = await _find_alert_id(ctx)
        except RuntimeError as e:
            return create_response(
                data={
                    "error": str(e),
                    "hint": "Provide an alert_id parameter (issue/alert ID, NOT case ID)."
                },
                is_error=True
            )

    command = f'!GetInstances brand="{integration_name}"'
    war_room_result = await _run_war_room_command(ctx, alert_id, command)

    if war_room_result.get("success") and war_room_result.get("results"):
        raw_content = war_room_result["results"][0].get("content", "")
        parsed = _parse_instances_response(raw_content, only_enabled=False)

        return create_response(data={
            "integration_name": integration_name,
            "source": "war_room",
            "alert_id_used": alert_id,
            **parsed,
        })

    error_msg = war_room_result.get("error", "Unknown error")
    result = {
        "error": f"Failed to retrieve integration '{integration_name}': {error_msg}",
        "alert_id_used": alert_id,
        "methods_tried": ["xsoar_api", "war_room"],
        "hint": "Check API key permissions or try a different integration name."
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
