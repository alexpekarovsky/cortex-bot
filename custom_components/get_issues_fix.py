"""Override broken PANW builtin get_issues — fixes wrong API path.

Also works around XSIAM API bug where filtering by 'id' (and some other fields
like observation_time) returns null/sparse fields. When detected, a fallback
query using issue_domain (extracted from tags) retrieves the full record.
"""
import logging
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError, PAPIClientError, PAPIClientRequestError,
    PAPIConnectionError, PAPIResponseError, PAPIServerError,
)
from entities.llm_config import LLM_FORMATTING_BASE_INSTRUCTIONS
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)

PAPI_ERRORS = (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
               PAPIClientRequestError, PAPIResponseError, PAPIClientError)

# Maps DOM tag values to issue_domain API filter values
_DOM_TAG_MAP = {
    "Security": "Security",
    "Health": "Health",
    "Posture": "Posture",
    "Identity": "Identity",
}


def _is_sparse_result(issue: dict) -> bool:
    """Check if the API returned a sparse/null record (known id-filter bug)."""
    return issue.get("name") is None and issue.get("severity") is None


def _extract_id_filter_values(filters: list) -> list[int] | None:
    """Return the list of issue IDs if filters contain only an 'id' filter."""
    id_filters = [f for f in filters if f.get("field") == "id"]
    non_id_filters = [f for f in filters if f.get("field") != "id"]
    if id_filters and not non_id_filters:
        return [int(v) for v in id_filters[0].get("value", [])]
    return None


def _extract_domain_from_tags(tags: list) -> str | None:
    """Extract the issue domain from DOM: tags (e.g. 'DOM:Security' -> 'Security')."""
    for tag in (tags or []):
        if isinstance(tag, str) and tag.startswith("DOM:"):
            domain = tag[4:]
            if domain in _DOM_TAG_MAP:
                return _DOM_TAG_MAP[domain]
    return None


async def _send_issue_search(fetcher, payload: dict) -> dict:
    """Send a single issue search request."""
    return await fetcher.send_request(
        path="/public_api/v1/issue/search/",
        method="POST",
        data=payload,
    )


async def _enrich_sparse_issues(fetcher, issues: list, target_ids: list[int]) -> list:
    """Replace sparse issue records with full ones via issue_domain fallback.

    The XSIAM issue search API returns null fields when filtering by 'id'.
    The issue_domain filter does NOT have this bug, so we use it as fallback.
    We extract the domain from the DOM: tag (always present even in sparse results),
    query by issue_domain sorted by id, and page through to find the target issues.
    """
    sparse_issues = [i for i in issues if _is_sparse_result(i) and i.get("id") in target_ids]
    if not sparse_issues:
        return issues

    # Group sparse issues by domain
    domain_to_ids: dict[str, list[int]] = {}
    for issue in sparse_issues:
        domain = _extract_domain_from_tags(issue.get("tags", []))
        if domain:
            domain_to_ids.setdefault(domain, []).append(issue["id"])

    if not domain_to_ids:
        logger.warning("Could not extract domain from tags for sparse issues")
        return issues

    # For each domain, query and find the target issues
    full_by_id: dict[int, dict] = {}
    for domain, ids_needed in domain_to_ids.items():
        ids_set = set(ids_needed)
        # Page through results sorted by id desc until we find all targets
        page_size = 100
        page_start = 0
        max_pages = 20  # Safety limit

        for _ in range(max_pages):
            fallback_payload = {
                "request_data": {
                    "filters": [
                        {"field": "issue_domain", "operator": "in", "value": [domain]},
                    ],
                    "search_from": page_start,
                    "search_to": page_start + page_size,
                    "sort": {"field": "id", "keyword": "desc"},
                }
            }
            fallback_data = await _send_issue_search(fetcher, fallback_payload)
            fallback_issues = fallback_data.get("reply", {}).get("DATA", [])
            if not fallback_issues:
                break

            for fi in fallback_issues:
                fid = fi.get("id")
                if fid in ids_set and not _is_sparse_result(fi):
                    full_by_id[fid] = fi
                    ids_set.discard(fid)

            # Stop if we found all or passed the smallest target id
            if not ids_set:
                break
            smallest_in_page = min(fi.get("id", 0) for fi in fallback_issues)
            if smallest_in_page < min(ids_set):
                break

            page_start += page_size

    if not full_by_id:
        logger.warning(f"Fallback query could not find full records for ids: {target_ids}")
        return issues

    # Replace sparse records with full ones
    enriched = []
    for issue in issues:
        iid = issue.get("id")
        if iid in full_by_id:
            enriched.append(full_by_id[iid])
        else:
            enriched.append(issue)

    logger.info(f"Enriched {len(full_by_id)}/{len(sparse_issues)} sparse issues via issue_domain fallback")
    return enriched


async def get_issues(
    ctx: Context,
    filters: Annotated[list, Field(description="Filters list to get the issues by. Leave empty to get all issues")],
    search_from: Annotated[int, Field(description="Marker for pagination starting point", default=0)] = 0,
    search_to: Annotated[int, Field(description="Marker for pagination ending point", default=30)] = 30,
    sort: Annotated[Optional[dict], Field(
        description="Dictionary of field and keyword to sort by. By default the sort is defined as creation_time, desc"
    )] = None,
) -> str:
    """Retrieves a list of issues or alerts from the Cortex platform.
    Use this tool to fetch all issues, or a filtered subset of issues, or one issue,
    based on various criteria such as time range, severity, status, or specific alert IDs.

    Args:
        filters: Filters list. Example: [{"field": "status", "operator": "in", "value": ["new", "under_investigation"]}]
            Allowed fields: id, external_id, detection.method, issue_domain, severity,
            _insert_time, status.progress, observation_time, last_modified, category,
            detection.rule_id, assigned_to, assigned_to_pretty, asset_ids, asset_names,
            asset_accounts, asset_regions, asset_classes, asset_group_ids, asset_providers,
            asset_types, asset_categories
        search_from: Pagination start offset.
        search_to: Pagination end offset.
        sort: Sort field. Example: {"field": "observation_time", "keyword": "desc"}
            Allowed sort fields: id, observation_time, severity.
    """
    payload = {
        "request_data": {
            "search_from": search_from,
            "search_to": search_to,
        }
    }
    if filters:
        payload["request_data"]["filters"] = filters
    if sort:
        payload["request_data"]["sort"] = sort

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await _send_issue_search(fetcher, payload)

        # Workaround: XSIAM API returns null fields when filtering by 'id'.
        # Detect this and re-query using issue_domain (from tags) to get full records.
        target_ids = _extract_id_filter_values(filters) if filters else None
        if target_ids and "reply" in response_data:
            issues = response_data["reply"].get("DATA", [])
            if any(_is_sparse_result(i) for i in issues if i.get("id") in target_ids):
                logger.info("Detected sparse results for id filter (known XSIAM API bug), "
                            "attempting issue_domain fallback")
                enriched = await _enrich_sparse_issues(fetcher, issues, target_ids)
                response_data["reply"]["DATA"] = enriched

        response_data["_metadata"] = {
            "formatting_instructions": LLM_FORMATTING_BASE_INSTRUCTIONS,
        }
        return create_response(data=response_data)
    except PAPI_ERRORS as e:
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to get issues: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class GetIssuesFixModule(BaseModule):
    """Overrides broken PANW get_issues with correct API path."""
    def register_tools(self):
        self._add_tool(get_issues)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
