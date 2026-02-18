"""
XSOAR File Hash Enrichment Wrapper

Wrapper that constructs !file commands for threat intelligence enrichment
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


async def _wait_for_file_enrichment_results(
    ctx: Context,
    investigation_id: str,
    command_timestamp: str,
    file_hash: str,
    timeout_seconds: int = 20
) -> dict:
    """Wait for XSOAR file enrichment results, collecting ALL responses for the specific hash."""
    from datetime import datetime

    fetcher = await get_fetcher(ctx)
    start_time = asyncio.get_event_loop().time()
    command_time = datetime.fromisoformat(command_timestamp.replace('Z', '+00:00'))

    collected_results = []
    seen_entry_ids = set()

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

                    if (entry.get("category") == "artifact" and
                        entry.get("parentContent") and
                        "!file" in entry.get("parentContent", "") and
                        file_hash.lower() in entry.get("parentContent", "").lower()):

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
            logger.warning(f"Error polling for file enrichment results: {e}")
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
        "message": f"No enrichment results found within {timeout_seconds} seconds for hash {file_hash}. Check War Room manually."
    }


async def enrich_file_hash(
    ctx: Context,
    file_hash: Annotated[str, Field(description="File hash to enrich (MD5, SHA1, or SHA256)")],
    alert_id: Annotated[Optional[str], Field(description="Alert ID to add enrichment to (e.g., '6126')")] = None,
    case_id: Annotated[Optional[str], Field(description="Case ID to add enrichment to (e.g., '350' or 'CASE-350')")] = None,
) -> str:
    """
    Enriches a file hash using XSOAR threat intelligence integrations.

    PREREQUISITES:
    - Requires a file reputation integration configured in XSOAR (VirusTotal, WildFire, etc.)
    - If no integration configured, returns error: "!file command not available"
    - To check available integrations: run_xsoar_automation(command="!GetInstances")

    Runs the !file command in the War Room and automatically retrieves results from
    VirusTotal, Google Threat Intelligence, and other configured integrations.

    =====================================================================
    CHOOSING THE RIGHT CONTEXT FOR ENRICHMENT
    =====================================================================

    **OPTION 1: GENERAL ENRICHMENT** (recommended for ad-hoc lookups)
    ─────────────────────────────────────────────────────────────────
    When you just want to check reputation of a file hash without a specific case:

    1. Create a workspace: workspace = create_issue()
    2. Use the returned alert_id: enrich_file_hash(file_hash="abc123...", alert_id=workspace["alert_id"])

    This keeps general lookups separate from real investigations.

    **OPTION 2: CASE-SPECIFIC INVESTIGATION** (for active incidents)
    ─────────────────────────────────────────────────────────────────
    When enriching file hashes found in a specific alert/case:

    1. Get case details: case_data = get_incident_extra_data(incident_id="100")
    2. Find an alert_id from the case's issues (e.g., "12345")
    3. Run enrichment: enrich_file_hash(file_hash="abc123...", alert_id="12345")

    Results appear in the specific issue's War Room, documenting your investigation.
    =====================================================================

    Use this tool when:
    - Investigating suspicious file hashes from malware alerts
    - Analyzing files from process execution events
    - Checking downloaded or created files
    - Validating file reputation
    - Threat hunting for known malware

    Returns:
    - File reputation scores
    - AV detection verdicts (number of engines detecting as malicious)
    - Malware family names and classifications
    - Related IOCs (if premium API)
    - Behavioral analysis results

    Args:
        ctx: The FastMCP context.
        file_hash: File hash to enrich - MD5, SHA1, or SHA256 (e.g., "44d88612fea8a8f36de82e1278abb02f").
        alert_id: Alert ID to add enrichment to (e.g., "12345").
        case_id: Case ID to add enrichment to (e.g., "100" or "CASE-350").

    Returns:
        JSON response with enrichment data from all configured threat intel sources.
    """
    if not case_id and not alert_id:
        return create_response(
            data={"error": "Either case_id or alert_id must be provided"},
            is_error=True
        )

    investigation_id = case_id if case_id else alert_id
    command = f"!file file={file_hash}"

    logger.info(f"Enriching file hash {file_hash} in investigation {investigation_id}")

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

            logger.info(f"Waiting for file enrichment results for hash {file_hash}...")
            enrichment_result = await _wait_for_file_enrichment_results(
                ctx=ctx,
                investigation_id=investigation_id,
                command_timestamp=command_timestamp,
                file_hash=file_hash,
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
        logger.exception(f"Failed to enrich file hash {file_hash}: {e}")

        # Check if it's a missing integration error
        if "not found in module supports list" in error_msg:
            return create_response(
                data={
                    "error": f"!file command not available - missing required integration. Install a file reputation integration (VirusTotal, WildFire, etc.) to enable file hash enrichment.",
                    "command_attempted": f"!file file={file_hash}",
                    "suggestion": "Use run_xsoar_automation with integration-specific commands instead (e.g., '!vt-get-file-report file=hash')"
                },
                is_error=True
            )

        return create_response(
            data={"error": f"Failed to execute enrichment: {error_msg}"},
            is_error=True
        )


class EnrichFileModule(BaseModule):
    """Module for file hash threat intelligence enrichment via XSOAR War Room"""

    def register_tools(self):
        self._add_tool(enrich_file_hash)

    def register_resources(self):
        pass
