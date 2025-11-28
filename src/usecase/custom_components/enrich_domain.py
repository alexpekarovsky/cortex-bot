"""
XSOAR Domain Enrichment Wrapper

Wrapper that constructs !domain commands for threat intelligence enrichment
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


async def _wait_for_domain_enrichment_results(
    ctx: Context,
    investigation_id: str,
    command_timestamp: str,
    domain: str,
    timeout_seconds: int = 20
) -> dict:
    """Wait for XSOAR domain enrichment results, collecting ALL responses for the specific domain."""
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
                        "!domain" in entry.get("parentContent", "") and
                        domain.lower() in entry.get("parentContent", "").lower()):

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
            logger.warning(f"Error polling for domain enrichment results: {e}")
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
        "message": f"No enrichment results found within {timeout_seconds} seconds for domain {domain}. Check War Room manually."
    }


async def enrich_domain(
    ctx: Context,
    domain: Annotated[str, Field(description="Domain name to enrich")],
    alert_id: Annotated[Optional[str], Field(description="Alert ID to add enrichment to (e.g., '6126')")] = None,
    case_id: Annotated[Optional[str], Field(description="Case ID to add enrichment to (e.g., '350' or 'CASE-350')")] = None,
) -> str:
    """
    Enriches a domain name using XSOAR threat intelligence integrations.

    Runs the !domain command in the War Room and automatically retrieves WHOIS,
    reputation, DNS records, and threat categorization data from configured threat
    intelligence sources (VirusTotal, Google Threat Intelligence, etc.).

    Use this tool when:
    - Investigating suspicious domains from phishing emails
    - Analyzing C2 infrastructure domains
    - Checking domains found in network logs
    - Validating sender domains
    - Threat hunting for malicious domains

    Returns:
    - Domain reputation scores
    - WHOIS registration information
    - Passive DNS records
    - Malware family associations
    - Phishing/malicious categorization
    - Domain age and registrar details

    Args:
        ctx: The FastMCP context.
        domain: Domain name to enrich (e.g., "example.com", "malicious-site.net").
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
    command = f"!domain domain={domain}"

    logger.info(f"Enriching domain {domain} in investigation {investigation_id}")

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

            logger.info(f"Waiting for domain enrichment results for {domain}...")
            enrichment_result = await _wait_for_domain_enrichment_results(
                ctx=ctx,
                investigation_id=investigation_id,
                command_timestamp=command_timestamp,
                domain=domain,
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
        logger.exception(f"Failed to enrich domain {domain}: {e}")
        return create_response(
            data={"error": f"Failed to execute enrichment: {str(e)}"},
            is_error=True
        )


class EnrichDomainModule(BaseModule):
    """Module for domain threat intelligence enrichment via XSOAR War Room"""

    def register_tools(self):
        self._add_tool(enrich_domain)

    def register_resources(self):
        pass
