"""
XSOAR Threat Intelligence Enrichment Tools

Wrapper tools that simplify threat intelligence enrichment by constructing
proper XSOAR War Room commands and executing them via the War Room API.
"""

from mcp.server.fastmcp import FastMCP
from typing import Optional

mcp = FastMCP("Cortex XSIAM Threat Intel Enrichment")


@mcp.tool()
async def enrich_file_hash(
    ctx,
    file_hash: str,
    case_id: Optional[str] = None,
    alert_id: Optional[str] = None
) -> dict:
    """
    Enriches a file hash (MD5, SHA1, SHA256) using XSOAR threat intelligence integrations.

    Runs the !file command in the War Room to gather reputation and context from configured
    threat intelligence sources (VirusTotal, Google Threat Intelligence, etc.).

    The enrichment will:
    - Check file reputation across multiple AV engines
    - Show detection verdicts and malware family names
    - Display relationships to other IOCs (if premium API)
    - Update indicator context with reputation scores
    - Add DBot message to War Room with results

    Use this to investigate suspicious file hashes from:
    - Malware alerts
    - Process execution events
    - File download/creation activity
    - Threat hunting queries

    Args:
        ctx: The FastMCP context.
        file_hash: File hash to enrich (MD5, SHA1, or SHA256).
        case_id: Case ID to add enrichment to (optional, use "CASE-{id}" or just numeric ID).
        alert_id: Alert ID to add enrichment to (optional, alternative to case_id).

    Returns:
        JSON response with War Room entry ID and command execution status.
    """
    from src.pkg.openapi_client import call_openapi_endpoint

    if not case_id and not alert_id:
        return {"error": "Either case_id or alert_id must be provided"}

    investigation_id = case_id if case_id else alert_id

    # Construct XSOAR !file command
    command = f"!file {file_hash}"

    # Add to War Room
    request_data = {
        "id": investigation_id,
        "data": command
    }

    response = await call_openapi_endpoint(
        ctx=ctx,
        endpoint="/public_api/v1/entries/insert",
        method="POST",
        request_data=request_data
    )

    if isinstance(response, dict):
        return {
            "entry_id": response.get("id"),
            "investigation_id": response.get("investigationId"),
            "command_executed": command,
            "created": response.get("created"),
            "status": "Enrichment command executed - check War Room for results"
        }

    return response


@mcp.tool()
async def enrich_ip(
    ctx,
    ip_address: str,
    case_id: Optional[str] = None,
    alert_id: Optional[str] = None
) -> dict:
    """
    Enriches an IP address using XSOAR threat intelligence integrations.

    Runs the !ip command in the War Room to gather reputation and context from configured
    threat intelligence sources.

    The enrichment will:
    - Check IP reputation across threat feeds
    - Show geolocation and ASN information
    - Display associated malware/campaigns
    - Identify if IP is in blocklists
    - Show passive DNS history (if available)
    - Update indicator context with reputation scores

    Use this to investigate suspicious IPs from:
    - Network connection alerts
    - C2 communication indicators
    - Lateral movement activity
    - External threat intelligence reports

    Args:
        ctx: The FastMCP context.
        ip_address: IP address to enrich (IPv4 or IPv6).
        case_id: Case ID to add enrichment to (optional).
        alert_id: Alert ID to add enrichment to (optional, alternative to case_id).

    Returns:
        JSON response with War Room entry ID and command execution status.
    """
    from src.pkg.openapi_client import call_openapi_endpoint

    if not case_id and not alert_id:
        return {"error": "Either case_id or alert_id must be provided"}

    investigation_id = case_id if case_id else alert_id

    # Construct XSOAR !ip command
    command = f"!ip {ip_address}"

    # Add to War Room
    request_data = {
        "id": investigation_id,
        "data": command
    }

    response = await call_openapi_endpoint(
        ctx=ctx,
        endpoint="/public_api/v1/entries/insert",
        method="POST",
        request_data=request_data
    )

    if isinstance(response, dict):
        return {
            "entry_id": response.get("id"),
            "investigation_id": response.get("investigationId"),
            "command_executed": command,
            "created": response.get("created"),
            "status": "Enrichment command executed - check War Room for results"
        }

    return response


@mcp.tool()
async def enrich_domain(
    ctx,
    domain: str,
    case_id: Optional[str] = None,
    alert_id: Optional[str] = None
) -> dict:
    """
    Enriches a domain name using XSOAR threat intelligence integrations.

    Runs the !domain command in the War Room to gather reputation and context from configured
    threat intelligence sources.

    The enrichment will:
    - Check domain reputation across threat feeds
    - Show WHOIS registration information
    - Display passive DNS records
    - Identify malicious/phishing categorization
    - Show associated malware families
    - Reveal domain age and registrar details
    - Update indicator context with reputation scores

    Use this to investigate suspicious domains from:
    - Phishing/malware URLs
    - C2 infrastructure
    - DNS queries in network logs
    - Email sender domains

    Args:
        ctx: The FastMCP context.
        domain: Domain name to enrich.
        case_id: Case ID to add enrichment to (optional).
        alert_id: Alert ID to add enrichment to (optional, alternative to case_id).

    Returns:
        JSON response with War Room entry ID and command execution status.
    """
    from src.pkg.openapi_client import call_openapi_endpoint

    if not case_id and not alert_id:
        return {"error": "Either case_id or alert_id must be provided"}

    investigation_id = case_id if case_id else alert_id

    # Construct XSOAR !domain command
    command = f"!domain {domain}"

    # Add to War Room
    request_data = {
        "id": investigation_id,
        "data": command
    }

    response = await call_openapi_endpoint(
        ctx=ctx,
        endpoint="/public_api/v1/entries/insert",
        method="POST",
        request_data=request_data
    )

    if isinstance(response, dict):
        return {
            "entry_id": response.get("id"),
            "investigation_id": response.get("investigationId"),
            "command_executed": command,
            "created": response.get("created"),
            "status": "Enrichment command executed - check War Room for results"
        }

    return response


@mcp.tool()
async def enrich_url(
    ctx,
    url: str,
    case_id: Optional[str] = None,
    alert_id: Optional[str] = None
) -> dict:
    """
    Enriches a URL using XSOAR threat intelligence integrations.

    Runs the !url command in the War Room to gather reputation and context from configured
    threat intelligence sources.

    The enrichment will:
    - Check URL reputation across threat feeds
    - Show URL categorization (malware, phishing, etc.)
    - Display associated malware downloads
    - Identify detection by URL scanners
    - Show redirect chains
    - Reveal hosting IP and ASN
    - Update indicator context with reputation scores

    Use this to investigate suspicious URLs from:
    - Phishing emails
    - Malware download locations
    - C2 check-in URLs
    - Web traffic logs
    - User-reported suspicious links

    Args:
        ctx: The FastMCP context.
        url: URL to enrich (must include protocol http:// or https://).
        case_id: Case ID to add enrichment to (optional).
        alert_id: Alert ID to add enrichment to (optional, alternative to case_id).

    Returns:
        JSON response with War Room entry ID and command execution status.
    """
    from src.pkg.openapi_client import call_openapi_endpoint

    if not case_id and not alert_id:
        return {"error": "Either case_id or alert_id must be provided"}

    investigation_id = case_id if case_id else alert_id

    # Construct XSOAR !url command
    command = f"!url {url}"

    # Add to War Room
    request_data = {
        "id": investigation_id,
        "data": command
    }

    response = await call_openapi_endpoint(
        ctx=ctx,
        endpoint="/public_api/v1/entries/insert",
        method="POST",
        request_data=request_data
    )

    if isinstance(response, dict):
        return {
            "entry_id": response.get("id"),
            "investigation_id": response.get("investigationId"),
            "command_executed": command,
            "created": response.get("created"),
            "status": "Enrichment command executed - check War Room for results"
        }

    return response
