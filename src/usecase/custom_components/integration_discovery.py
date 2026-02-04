"""
XSOAR Integration Discovery Tool

Discovers available XSOAR integrations, their commands, and active instances.
This is critical for knowing what threat intelligence and automation capabilities
are available in the XSIAM environment.
"""

from typing import Optional

from fastmcp import Context

from usecase.base_module import BaseModule


async def list_integrations(
    ctx: Context,
    integration_filter: Optional[str] = None,
    only_enabled: bool = True
) -> dict:
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

    The response includes for each integration:
    - Integration name and display name
    - Category (Data Enrichment & Threat Intelligence, Endpoint, etc.)
    - Available commands with descriptions
    - Configuration status (enabled/disabled)
    - Integration instance details

    Args:
        ctx: The FastMCP context.
        integration_filter: Optional filter to search for specific integrations by name.
        only_enabled: If True, only return enabled integrations (default: True).

    Returns:
        JSON response containing list of integrations with their commands and capabilities.
    """
    from usecase.fetcher import get_fetcher

    # Call the /settings/integration-search endpoint
    endpoint = "/settings/integration-search"
    request_data = {}

    if integration_filter:
        request_data["query"] = integration_filter

    fetcher = await get_fetcher(ctx)
    response = await fetcher.send_request(
        path=endpoint,
        method="POST",
        data=request_data
    )

    # Parse and filter the response
    if isinstance(response, dict) and "integrations" in response:
        integrations = response["integrations"]

        # Filter by enabled status if requested
        if only_enabled:
            integrations = [
                integration for integration in integrations
                if integration.get("enabled", False) or
                   any(instance.get("enabled", False) for instance in integration.get("instances", []))
            ]

        # Extract useful information
        result = {
            "total_count": len(integrations),
            "integrations": []
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

            # Extract commands
            commands = integration.get("script", {}).get("commands", [])
            for cmd in commands:
                integration_info["commands"].append({
                    "name": cmd.get("name"),
                    "description": cmd.get("description"),
                    "deprecated": cmd.get("deprecated", False)
                })

            # Extract instance info
            instances = integration.get("instances", [])
            for instance in instances:
                integration_info["instances"].append({
                    "name": instance.get("name"),
                    "enabled": instance.get("enabled", False),
                    "brand": instance.get("brand")
                })

            result["integrations"].append(integration_info)

        return result

    return response


async def get_integration_commands(
    ctx: Context,
    integration_name: str
) -> dict:
    """
    Retrieves detailed command information for a specific XSOAR integration.

    Use this to understand what commands an integration provides and how to use them
    in War Room for investigations. Essential before running enrichment or automation
    commands.

    The response includes:
    - Command names (e.g., "ip", "file", "vt-get-file-report")
    - Detailed descriptions
    - Input parameters and types
    - Output context paths
    - Usage examples

    Use this to:
    - Learn what commands VirusTotal integration provides
    - Understand parameter requirements for enrichment commands
    - Find available automation commands for incident response
    - Discover integration capabilities before using them

    Args:
        ctx: The FastMCP context.
        integration_name: Name of the integration to get commands for (e.g., "VirusTotal",
                         "Google Threat Intelligence", "ActiveDirectory").

    Returns:
        JSON response with detailed command information for the integration.
    """
    fetcher = await get_fetcher(ctx)

    # First get all integrations
    endpoint = "/settings/integration-search"
    response = await fetcher.send_request(
        path=endpoint,
        method="POST",
        data={"query": integration_name}
    )

    if isinstance(response, dict) and "integrations" in response:
        integrations = response["integrations"]

        # Find matching integration
        matching = None
        for integration in integrations:
            if (integration.get("name", "").lower() == integration_name.lower() or
                integration.get("display", "").lower() == integration_name.lower()):
                matching = integration
                break

        if matching:
            commands = matching.get("script", {}).get("commands", [])

            return {
                "integration_name": matching.get("display"),
                "category": matching.get("category"),
                "description": matching.get("description"),
                "total_commands": len(commands),
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
            }
        else:
            return {
                "error": f"Integration '{integration_name}' not found",
                "available_integrations": [i.get("display") for i in integrations[:20]]
            }

    return response


class IntegrationDiscoveryModule(BaseModule):
    """
    MCP module for discovering XSOAR integrations and their capabilities.

    Provides tools to discover what threat intelligence sources, automation integrations,
    and security tools are configured in the XSIAM instance.

    Essential for:
    - Understanding available enrichment capabilities
    - Finding automation commands for investigations
    - Discovering what integrations are enabled
    - Learning command syntax and parameters

    Tools provided:
        - list_integrations: List all available XSOAR integrations
        - get_integration_commands: Get detailed command info for specific integration
    """

    def register_tools(self):
        self._add_tool(list_integrations)
        self._add_tool(get_integration_commands)

    def register_resources(self):
        """Integration discovery module doesn't register resources."""
        pass
