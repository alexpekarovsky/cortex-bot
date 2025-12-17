"""
XSOAR URL Enrichment Wrapper

Wrapper that constructs !url commands for threat intelligence enrichment
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


async def _wait_for_url_enrichment_results(
    ctx: Context,
    investigation_id: str,
    command_timestamp: str,
    url: str,
    timeout_seconds: int = 20
) -> dict:
    """Wait for XSOAR URL enrichment results, collecting ALL responses for the specific URL."""
    from datetime import datetime

    fetcher = await get_fetcher(ctx)
    start_time = asyncio.get_event_loop().time()
    command_time = datetime.fromisoformat(command_timestamp.replace('Z', '+00:00'))

    collected_results = []
    seen_entry_ids = set()

    # URL might be URL-encoded in responses, so normalize for comparison
    normalized_url = url.lower()

    while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
        try:
            entries_response = await fetcher.send_request(
                path="/entries/get",
                method="POST",
                data={"id": investigation_id, "filter": {"pagesize": 20}}
            )

            if isinstance(entries_response, dict) and "data" in entries_response:
                entries = entries_response["data"]

                for entry in entries:
                    entry_id = entry.get("id")
                    if entry_id in seen_entry_ids:
                        continue

                    parent_content = entry.get("parentContent", "").lower()
                    if (entry.get("category") == "artifact" and
                        parent_content and
                        "!url" in parent_content and
                        (normalized_url in parent_content or url.replace("://", "%3A//") in parent_content)):

                        entry_created = entry.get("created", "")
                        if entry_created:
                            entry_time = datetime.fromisoformat(entry_created.replace('Z', '+00:00'))

                            if entry_time > command_time:
                                content = entry.get("contents", "")
                                if content and len(content) > 10:
                                    seen_entry_ids.add(entry_id)
                                    collected_results.append({
                                        "entry_id": entry_id,
                                        "created": entry_created,
                                        "content": content,
                                        "is_error": "Error" in content or "error" in content.lower()
                                    })

            if collected_results and (asyncio.get_event_loop().time() - start_time) >= 5:
                break

            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"Error polling for URL enrichment results: {e}")
            await asyncio.sleep(2)

    if collected_results:
        errors = [r for r in collected_results if r["is_error"]]
        successes = [r for r in collected_results if not r["is_error"]]

        return {
            "success": len(successes) > 0,
            "total_results": len(collected_results),
            "successful_enrichments": successes,
            "errors": errors,
            "summary": f"Collected {len(collected_results)} results ({len(successes)} successful, {len(errors)} errors)"
        }

    return {
        "success": False,
        "timeout": True,
        "message": f"No enrichment results found within {timeout_seconds} seconds for URL {url}. Check War Room manually."
    }


async def enrich_url(
    ctx: Context,
    url: Annotated[str, Field(description="URL to enrich (must include protocol http:// or https://)")],
    alert_id: Annotated[Optional[str], Field(description="Alert ID to add enrichment to (e.g., '6126')")] = None,
    case_id: Annotated[Optional[str], Field(description="Case ID to add enrichment to (e.g., '350' or 'CASE-350')")] = None,
) -> str:
    """
    Enriches a URL using XSOAR threat intelligence integrations.

    PREREQUISITES:
    - Requires a URL reputation integration configured in XSOAR (VirusTotal, URLhaus, etc.)
    - If no integration configured, returns error: "!url command not available"
    - To check available integrations: run_xsoar_automation(command="!GetInstances")

    Runs the !url command in the War Room and automatically retrieves URL reputation,
    categorization, malware associations, and scanner detection results from configured
    threat intelligence sources.

    IMPORTANT: Requires alert_id from an alert that is PART OF A CASE. The alert must have
    an associated investigation (War Room). To find valid alert IDs:
    1. Use get_incident_extra_data to get alerts from a case, OR
    2. Use get_issues to find alerts, then check if they have a case_id field, OR
    3. Ask the user for an alert ID from a case they are investigating.

    Use this tool when:
    - Investigating suspicious URLs from phishing emails
    - Analyzing malware download locations
    - Checking C2 check-in URLs
    - Validating URLs from web traffic logs
    - Reviewing user-reported suspicious links

    Returns:
    - URL reputation scores
    - Category (malware/phishing/safe)
    - Associated malware downloads
    - Detection by URL scanners
    - Redirect chains
    - Hosting IP and ASN information

    Args:
        ctx: The FastMCP context.
        url: URL to enrich - must include protocol (e.g., "http://malicious.com/payload.exe").
        alert_id: Alert ID to add enrichment to (e.g., "6126").
        case_id: Case ID to add enrichment to (e.g., "350" or "CASE-350").

    Returns:
        JSON response with enrichment data from all configured threat intel sources.
    """
    if not case_id and not alert_id:
        return create_response(
            data={"error": "Either case_id or alert_id must be provided"},
            is_error=True
        )

    investigation_id = case_id if case_id else alert_id
    command = f"!url url={url}"

    logger.info(f"Enriching URL {url} in investigation {investigation_id}")

    try:
        fetcher = await get_fetcher(ctx)

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

            logger.info(f"Waiting for URL enrichment results for {url}...")
            enrichment_result = await _wait_for_url_enrichment_results(
                ctx=ctx,
                investigation_id=investigation_id,
                command_timestamp=command_timestamp,
                url=url,
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
        error_msg = str(e)
        logger.exception(f"Failed to enrich URL {url}: {e}")

        # Check if it's a missing integration error
        if "not found in module supports list" in error_msg:
            return create_response(
                data={
                    "error": f"!url command not available - missing required integration. Install a URL reputation integration (VirusTotal, URLhaus, etc.) to enable URL enrichment.",
                    "command_attempted": f"!url url={url}",
                    "suggestion": "Use run_xsoar_automation with integration-specific commands instead (e.g., '!vt-get-url-report url=...')"
                },
                is_error=True
            )

        return create_response(
            data={"error": f"Failed to execute enrichment: {error_msg}"},
            is_error=True
        )


class EnrichURLModule(BaseModule):
    """Module for URL threat intelligence enrichment via XSOAR War Room"""

    def register_tools(self):
        self._add_tool(enrich_url)

    def register_resources(self):
        pass
