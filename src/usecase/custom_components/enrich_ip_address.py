"""
XSOAR IP Address Enrichment Wrapper

Simple wrapper that constructs !ip commands for threat intelligence enrichment
via the War Room API and automatically retrieves the results.
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


async def _wait_for_enrichment_results(
    ctx: Context,
    investigation_id: str,
    command_entry_id: str,
    command_timestamp: str,
    ip_address: str,
    timeout_seconds: int = 20
) -> dict:
    """
    Waits for XSOAR enrichment results to appear in the War Room.

    Polls the War Room entries for up to timeout_seconds to collect ALL enrichment
    responses for the specific IP address. This handles parallel enrichment commands
    by matching results to the specific IP queried.

    Args:
        ctx: The FastMCP context.
        investigation_id: Case or alert ID.
        command_entry_id: The entry ID of the command that was sent.
        command_timestamp: ISO timestamp when command was created (to filter old results).
        ip_address: The specific IP address being enriched (to match results).
        timeout_seconds: Maximum seconds to wait for results (default: 20).

    Returns:
        dict: All enrichment results for this specific IP or timeout message.
    """
    from datetime import datetime, timezone

    fetcher = await get_fetcher(ctx)
    start_time = asyncio.get_event_loop().time()

    # Parse command timestamp to filter results
    command_time = datetime.fromisoformat(command_timestamp.replace('Z', '+00:00'))

    collected_results = []
    seen_entry_ids = set()

    # Poll for results
    while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
        try:
            # Get recent War Room entries
            entries_response = await fetcher.send_request(
                path="/entries/get",
                method="POST",
                data={"id": investigation_id, "filter": {"pagesize": 20}}
            )

            if isinstance(entries_response, dict) and "data" in entries_response:
                entries = entries_response["data"]

                # Look for ALL artifact entries that came AFTER our command
                for entry in entries:
                    entry_id = entry.get("id")

                    # Skip if we've already processed this entry
                    if entry_id in seen_entry_ids:
                        continue

                    # Check if this is a response to an !ip command (artifact category)
                    if (entry.get("category") == "artifact" and
                        entry.get("parentContent") and
                        "!ip" in entry.get("parentContent", "") and
                        ip_address in entry.get("parentContent", "")):

                        # Parse entry timestamp
                        entry_created = entry.get("created", "")
                        if entry_created:
                            entry_time = datetime.fromisoformat(entry_created.replace('Z', '+00:00'))

                            # Only consider entries created AFTER our command
                            if entry_time > command_time:
                                content = entry.get("contents", "")

                                # Skip empty/metric messages
                                if content and len(content) > 10:
                                    seen_entry_ids.add(entry_id)

                                    result_entry = {
                                        "entry_id": entry_id,
                                        "created": entry_created,
                                        "content": content,
                                        "is_error": "Error" in content or "error" in content.lower()
                                    }
                                    collected_results.append(result_entry)

            # If we have results, check if we should keep waiting
            if collected_results:
                # Wait a bit more to catch any additional results (2 more seconds)
                if (asyncio.get_event_loop().time() - start_time) < 5:
                    await asyncio.sleep(2)
                else:
                    # We have results and enough time has passed
                    break

            # Wait 2 seconds before next poll
            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"Error polling for enrichment results: {e}")
            await asyncio.sleep(2)

    # Return collected results
    if collected_results:
        # Check if any are errors
        errors = [r for r in collected_results if r["is_error"]]
        successes = [r for r in collected_results if not r["is_error"]]

        return {
            "success": len(successes) > 0,
            "total_results": len(collected_results),
            "successful_enrichments": successes,
            "errors": errors,
            "summary": f"Collected {len(collected_results)} enrichment results ({len(successes)} successful, {len(errors)} errors)"
        }

    # Timeout reached with no results
    return {
        "success": False,
        "timeout": True,
        "message": f"No enrichment results found within {timeout_seconds} seconds for IP {ip_address}. Check War Room manually."
    }


async def enrich_ip_address(
    ctx: Context,
    ip_address: Annotated[str, Field(description="IP address to enrich (IPv4 or IPv6)")],
    alert_id: Annotated[Optional[str], Field(description="Alert ID to add enrichment to (e.g., '6126')")] = None,
    case_id: Annotated[Optional[str], Field(description="Case ID to add enrichment to (e.g., '350' or 'CASE-350')")] = None,
) -> str:
    """
    Enriches an IP address using XSOAR threat intelligence integrations.

    This is a convenience wrapper around the XSOAR !ip command. For advanced options
    or integration-specific commands, use run_xsoar_automation instead.

    IMPORTANT: Requires alert_id OR case_id to specify which investigation War Room
    to run the enrichment in. Prefer using alert_id for alert-specific enrichment.

    The enrichment will:
    - Check IP reputation across threat feeds
    - Show geolocation and ASN information
    - Display associated malware/campaigns
    - Identify if IP is in blocklists
    - Show passive DNS history (if available)
    - Update indicator context with reputation scores

    Use this when:
    - Investigating suspicious IPs from alerts
    - Enriching C2 communication indicators
    - Checking reputation of external connections
    - Adding threat intel context to investigations

    For advanced enrichment:
    - Use run_xsoar_automation with integration-specific commands
    - Example: !vt-ip-report ip=8.8.8.8 (for VirusTotal-specific options)

    Args:
        ctx: The FastMCP context.
        ip_address: IP address to enrich (IPv4 or IPv6).
        alert_id: Alert ID to run enrichment in (e.g., "6126") - PREFERRED.
        case_id: Case ID alternative (e.g., "350") - use alert_id when possible.

    Returns:
        JSON response with enrichment results and War Room entry ID.
    """
    # Validate that at least one ID is provided
    if not case_id and not alert_id:
        return create_response(
            data={"error": "Either case_id or alert_id must be provided"},
            is_error=True
        )

    # Use whichever ID was provided
    investigation_id = case_id if case_id else alert_id

    # Construct XSOAR !ip command with named parameter
    command = f"!ip ip={ip_address}"

    logger.info(f"Enriching IP {ip_address} in investigation {investigation_id}")

    try:
        # Get fetcher from context
        fetcher = await get_fetcher(ctx)

        # Add command to War Room
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

            # Wait for enrichment results (XSOAR typically responds in 2-15 seconds)
            logger.info(f"Waiting for enrichment results for IP {ip_address}...")
            enrichment_result = await _wait_for_enrichment_results(
                ctx=ctx,
                investigation_id=investigation_id,
                command_entry_id=entry_id,
                command_timestamp=command_timestamp,
                ip_address=ip_address,
                timeout_seconds=20
            )

            result = {
                "entry_id": entry_id,
                "investigation_id": response.get("investigationId"),
                "command_executed": command,
                "created": response.get("created"),
                "enrichment_data": enrichment_result,
                "status": "Enrichment completed" if enrichment_result.get("success") else "Enrichment command executed - check War Room for results"
            }
            return create_response(data=result)

        return create_response(data=response)

    except Exception as e:
        logger.exception(f"Failed to enrich IP {ip_address}: {e}")
        return create_response(
            data={"error": f"Failed to execute enrichment: {str(e)}"},
            is_error=True
        )


class EnrichIPModule(BaseModule):
    """Module for IP address threat intelligence enrichment via XSOAR War Room"""

    def register_tools(self):
        self._add_tool(enrich_ip_address)

    def register_resources(self):
        pass
