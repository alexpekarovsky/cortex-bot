"""Override broken PANW builtin get_issues — fixes wrong API path.

Also works around XSIAM API bug where filtering by 'id' returns null/sparse
fields. When detected, a fallback query using issue_domain (extracted from
DOM: tags) retrieves the full record. (Cherry-picked from PR #11 by dor1412)
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

# --- Sparse result workaround (PR #11 by dor1412) ---

_DOM_TAG_MAP = {"Security": "Security", "Health": "Health", "Posture": "Posture", "Identity": "Identity"}


def _is_sparse(issue: dict) -> bool:
    return issue.get("name") is None and issue.get("severity") is None


def _get_id_filter_values(filters: list) -> list[int] | None:
    id_filters = [f for f in filters if f.get("field") == "id"]
    if id_filters and all(f.get("field") == "id" for f in filters):
        return [int(v) for v in id_filters[0].get("value", [])]
    return None


def _domain_from_tags(tags: list) -> str | None:
    for tag in (tags or []):
        if isinstance(tag, str) and tag.startswith("DOM:"):
            return _DOM_TAG_MAP.get(tag[4:])
    return None


async def _enrich_sparse(fetcher, issues: list, target_ids: list[int]) -> list:
    """Replace sparse records with full ones via issue_domain fallback."""
    sparse = [i for i in issues if _is_sparse(i) and i.get("id") in target_ids]
    if not sparse:
        return issues

    by_domain: dict[str, list[int]] = {}
    for issue in sparse:
        domain = _domain_from_tags(issue.get("tags", []))
        if domain:
            by_domain.setdefault(domain, []).append(issue["id"])

    full_map: dict[int, dict] = {}
    for domain, ids in by_domain.items():
        target_set = set(ids)
        for page in range(20):
            resp = await fetcher.send_request(
                path="/public_api/v1/issue/search/", method="POST",
                data={"request_data": {
                    "filters": [{"field": "issue_domain", "operator": "in", "value": [domain]}],
                    "search_from": page * 100, "search_to": (page + 1) * 100,
                    "sort": {"field": "id", "keyword": "desc"}
                }}
            )
            for item in resp.get("reply", resp).get("DATA", []):
                if item.get("id") in target_set and not _is_sparse(item):
                    full_map[item["id"]] = item
                    target_set.discard(item["id"])
            if not target_set or len(resp.get("reply", resp).get("DATA", [])) < 100:
                break

    return [full_map.get(i.get("id"), i) if _is_sparse(i) else i for i in issues]

# --- End sparse workaround ---

FIELD_ALIASES = {
    "status": "status.progress",
    "detection_method": "detection.method",
    "domain": "issue_domain",
    "issue_id": "id",
}

STATUS_ALIASES = {
    "new": "New",
    "under_investigation": "Under Investigation",
    "resolved": "Resolved",
}

SEVERITY_ALIASES = {
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "critical": "CRITICAL",
    "informational": "INFORMATIONAL",
}


def _normalize_filters(filters: list) -> list:
    """Translate user-friendly field names and values to the actual API format."""
    normalized = []
    for f in filters:
        f = dict(f)
        field = f.get("field", "")
        f["field"] = FIELD_ALIASES.get(field, field)

        if f["field"] == "status.progress" and isinstance(f.get("value"), list):
            f["value"] = [STATUS_ALIASES.get(v, v) for v in f["value"]]
        if f["field"] == "severity" and isinstance(f.get("value"), list):
            f["value"] = [SEVERITY_ALIASES.get(v, v) for v in f["value"]]

        normalized.append(f)
    return normalized


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
            Allowed fields: id, external_id, severity, status (or status.progress), detection_method (or detection.method),
            observation_time, _insert_time, last_modified, issue_domain (or domain), category, detection.rule_id,
            assigned_to, assigned_to_pretty, asset_ids, asset_names, asset_accounts, asset_regions,
            asset_classes, asset_group_ids, asset_providers, asset_types, asset_categories.
            Status values: "New", "Under Investigation", "Resolved" (case-insensitive).
            Severity values: "HIGH", "MEDIUM", "LOW", "CRITICAL" (case-insensitive).
            Detection method values: "FW" (firewall/NGFW), "CIEM_SCANNER", "XDR_AGENT", "BIOC", etc.
        search_from: Pagination start offset.
        search_to: Pagination end offset.
        sort: Sort field. Example: {"field": "modification_time", "keyword": "desc"}
    """
    payload = {
        "request_data": {
            "search_from": search_from,
            "search_to": search_to,
        }
    }
    if filters:
        payload["request_data"]["filters"] = _normalize_filters(filters)
    if sort:
        payload["request_data"]["sort"] = sort

    try:
        fetcher = await get_fetcher(ctx)
        response_data = await fetcher.send_request(
            path="/public_api/v1/issue/search/",
            method="POST",
            data=payload
        )
        # Workaround: XSIAM returns sparse data when filtering by 'id'
        reply = response_data.get("reply", response_data)
        issues = reply.get("DATA", [])
        if filters:
            target_ids = _get_id_filter_values(_normalize_filters(filters))
            if target_ids and any(_is_sparse(i) for i in issues):
                try:
                    reply["DATA"] = await _enrich_sparse(fetcher, issues, target_ids)
                except Exception:
                    pass  # Keep original sparse data if fallback fails

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
