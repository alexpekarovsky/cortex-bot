"""MDR/MTH managed threat detection tools — read, comment on, and triage the reports
Unit 42 Managed Services analysts write for managed (child) tenants.

Note on the wire format: the published OpenAPI spec shows flat request bodies, but the live
API rejects those with err_code 101 ("Missing required param: `request_data`"). Every payload
here is therefore wrapped in the standard {"request_data": {...}} envelope, matching the
spec's own *RequestData schema names and every other Cortex PAPI endpoint."""
import json
import logging
import re
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError, PAPIClientError, PAPIClientRequestError,
    PAPIConnectionError, PAPIResponseError, PAPIServerError,
)
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)

PAPI_ERRORS = (PAPIConnectionError, PAPIAuthenticationError, PAPIServerError,
               PAPIClientRequestError, PAPIResponseError, PAPIClientError)

MTH_BASE = "/public_api/v1/mth/child"

# Requests carry the display form; responses always carry the internal form.
STATUS_DISPLAY = [
    "New",
    "In Progress",
    "On Hold",
    "Resolved False Positive",
    "Resolved True Positive",
    "Resolved Other",
    "Resolved Security Testing",
]
STATUS_INTERNAL_TO_DISPLAY = {
    "NEW": "New",
    "IN_PROGRESS": "In Progress",
    "ON_HOLD": "On Hold",
    "RESOLVED_FP": "Resolved False Positive",
    "RESOLVED_TP": "Resolved True Positive",
    "RESOLVED_OTHER": "Resolved Other",
    "RESOLVED_SECURITY_TESTING": "Resolved Security Testing",
}

COMMENT_MAX_LEN = 4096
ATTACHMENT_PREFIXES = ("send_report/", "update_report/", "add_comment/", "update_comment/", "comment/")


def _parse(data):
    """Accept JSON strings from clients that stringify list/dict arguments."""
    if data is None:
        return None
    if isinstance(data, str):
        stripped = data.strip()
        if stripped.startswith(("[", "{")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return data
    return data


def _as_str_list(value, field: str) -> list:
    """Coerce a scalar / list / JSON-string into a list of non-empty strings.

    The API rejects numeric JSON for incident_ids even though the column is an int,
    so everything is stringified here."""
    value = _parse(value)
    if isinstance(value, (str, int)):
        value = [value]
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a string or a list of strings")
    out = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            out.append(text)
    if not out:
        raise ValueError(f"{field} must contain at least one non-empty value")
    return out


def _lower_keys(obj):
    """Recursively lower-case dict keys so UPPER_SNAKE and lower_snake rows match."""
    if isinstance(obj, dict):
        return {str(k).lower(): _lower_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_lower_keys(item) for item in obj]
    return obj


def _normalize_report(row):
    """One report shape regardless of which endpoint produced it."""
    if not isinstance(row, dict):
        return row
    report = _lower_keys(row)

    # get_reports_by_source_id returns the raw MySQL column: a JSON-encoded string.
    attachments = report.get("attachments")
    if isinstance(attachments, str):
        try:
            attachments = json.loads(attachments)
        except json.JSONDecodeError:
            attachments = []
    if isinstance(attachments, dict):
        attachments = list(attachments.values()) if attachments else []
    if attachments is None:
        attachments = []
    report["attachments"] = attachments

    status = report.get("report_status")
    if isinstance(status, str):
        report["report_status_display"] = STATUS_INTERNAL_TO_DISPLAY.get(status, status)
    return report


def _unwrap(response):
    """Collapse the four incompatible envelopes into (rows, reported_count).

    {DATA,COUNT} | {status,data} | bare array | single object.
    Uses isinstance because client_patch.py returns a dict *subclass*."""
    reply = response
    if isinstance(response, dict) and "reply" in response:
        reply = response["reply"]

    if isinstance(reply, list):
        return reply, len(reply)
    if isinstance(reply, dict):
        if "DATA" in reply:
            rows = reply.get("DATA") or []
            return rows, reply.get("COUNT", len(rows))
        if "data" in reply:
            rows = reply.get("data") or []
            return rows, len(rows)
        return [reply], 1
    if reply is None:
        return [], 0
    return [reply], 1


def _papi_error(exc) -> dict:
    """Surface reply.err_extra — the only field that says *why* a call was rejected.

    Validation and licensing failures on these endpoints come back as HTTP 500 with a
    generic err_msg, and the client embeds the whole response body in the exception text."""
    detail = str(exc)
    match = re.search(r"\{.*\}", detail, re.DOTALL)
    if match:
        try:
            body = json.loads(match.group(0))
            reply = body.get("reply") if isinstance(body, dict) else None
            if isinstance(reply, dict):
                reason = reply.get("err_extra") or reply.get("err_msg")
                if reason:
                    return {"error": reason, "err_code": reply.get("err_code"), "detail": detail}
        except json.JSONDecodeError:
            pass
    return {"error": detail}


def _err(message: str) -> str:
    return create_response(data={"error": message}, is_error=True)


async def get_mdr_reports(
    ctx: Context,
    source_ids: Annotated[Optional[list | str], Field(
        description="XSOAR source ID(s) of specific reports. String or list of strings."
    )] = None,
    incident_ids: Annotated[Optional[list | str], Field(
        description="Incident ID(s) the reports are attached to. String or list; numbers are coerced to strings."
    )] = None,
    statuses: Annotated[Optional[list | str], Field(
        description='Filter by status. Valid values: "New", "In Progress", "On Hold", '
                    '"Resolved False Positive", "Resolved True Positive", "Resolved Other", '
                    '"Resolved Security Testing". Note there is no bare "Resolved".'
    )] = None,
    limit: Annotated[int, Field(
        description="Maximum reports to return (client-side; the API does not page). 0 = no limit."
    )] = 50,
    raw: Annotated[bool, Field(description="Return the untouched API response instead of normalized reports.")] = False,
) -> str:
    """Retrieves Managed Threat Hunting (MTH) / Unit 42 MDR reports for this tenant.

    These are the analyst-written reports delivered to a managed *child* tenant — they are
    not XSIAM cases or issues. Use get_cases/get_issues for those.

    Provide at most ONE selector: source_ids, incident_ids, or statuses. With none, all
    reports are returned. Results are normalized to lower_snake_case with parsed attachments
    and a report_status_display field alongside the internal report_status.

    Only works on tenants provisioned as MTH or MDR child tenants; other tenants are rejected."""
    selectors = [name for name, value in
                 (("source_ids", source_ids), ("incident_ids", incident_ids), ("statuses", statuses)) if value]
    if len(selectors) > 1:
        return _err(f"Provide at most one of source_ids, incident_ids, statuses — got {', '.join(selectors)}. "
                    "These map to three different endpoints and cannot be combined.")

    try:
        if source_ids:
            mode = "by_source_id"
            path = f"{MTH_BASE}/get_reports_by_source_id"
            payload = {"xsoar_source_ids": _as_str_list(source_ids, "source_ids")}
        elif incident_ids:
            mode = "by_incident_id"
            path = f"{MTH_BASE}/get_reports_by_incident_id"
            payload = {"incident_ids": _as_str_list(incident_ids, "incident_ids")}
        elif statuses:
            mode = "by_statuses"
            status_list = _as_str_list(statuses, "statuses")
            invalid = [s for s in status_list if s not in STATUS_DISPLAY]
            if invalid:
                return _err(f"Invalid status value(s): {invalid}. Valid values: {STATUS_DISPLAY}")
            path = f"{MTH_BASE}/get_reports_by_statuses"
            payload = {"report_statuses": status_list}
        else:
            mode = "all"
            path = f"{MTH_BASE}/get_all_reports"
            payload = {}
    except ValueError as e:
        return _err(str(e))

    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(path, data={"request_data": payload})
        if raw:
            return create_response(data={"mode": mode, "raw": response})
        rows, count = _unwrap(response)
        reports = [_normalize_report(row) for row in rows]
        truncated = 0 < limit < len(reports)
        if truncated:
            reports = reports[:limit]
        return create_response(data={
            "mode": mode,
            "count": count,
            "returned": len(reports),
            "truncated": truncated,
            "reports": reports,
        })
    except PAPI_ERRORS as e:
        return create_response(data=_papi_error(e), is_error=True)
    except Exception as e:
        logger.exception(f"get_mdr_reports failed: {e}")
        return _err(str(e))


async def get_mdr_report_comments(
    ctx: Context,
    source_id: Annotated[Optional[str], Field(
        description="XSOAR source ID of the report. Takes precedence over the time range."
    )] = None,
    start_time: Annotated[Optional[int], Field(
        description="Start of the comment window, epoch milliseconds. Requires end_time."
    )] = None,
    end_time: Annotated[Optional[int], Field(
        description="End of the comment window, epoch milliseconds. Requires start_time."
    )] = None,
    raw: Annotated[bool, Field(description="Return the untouched API response.")] = False,
) -> str:
    """Retrieves comments on MDR/MTH reports — the analyst/customer conversation thread.

    Supply either source_id (comments on one report) or both start_time and end_time
    (all comments in a window). If source_id is given the time range is ignored.
    Hunter-authored comments may show the author as "Unit 42 Managed Services"."""
    if source_id:
        payload = {"xsoar_source_id": str(source_id).strip()}
    elif start_time is not None and end_time is not None:
        if start_time > end_time:
            return _err("start_time must not be greater than end_time (both are epoch milliseconds).")
        payload = {"start_time": int(start_time), "end_time": int(end_time)}
    else:
        return _err("Provide either source_id, or both start_time and end_time (epoch milliseconds).")

    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(f"{MTH_BASE}/get_comments", data={"request_data": payload})
        if raw:
            return create_response(data={"raw": response})
        rows, count = _unwrap(response)
        comments = [_lower_keys(row) for row in rows]
        return create_response(data={"count": count, "returned": len(comments), "comments": comments})
    except PAPI_ERRORS as e:
        return create_response(data=_papi_error(e), is_error=True)
    except Exception as e:
        logger.exception(f"get_mdr_report_comments failed: {e}")
        return _err(str(e))


async def add_mdr_report_comment(
    ctx: Context,
    source_id: Annotated[str, Field(description="XSOAR source ID of the report to comment on.")],
    comment_text: Annotated[str, Field(description=f"Comment body, maximum {COMMENT_MAX_LEN} characters.")],
    created_by: Annotated[str, Field(
        description="Email or username of the comment author. Free text, not validated against tenant users."
    )],
    path_to_file: Annotated[Optional[str], Field(
        description="Optional storage key of an attachment already uploaded to the public API bucket. "
                    "Must start with send_report/, update_report/, add_comment/, update_comment/ or comment/."
    )] = None,
    extract_zip_file: Annotated[bool, Field(
        description="Set true when the attachment is a zip archive that should be extracted."
    )] = False,
) -> str:
    """Adds a comment to an MDR/MTH report — how a customer replies to Unit 42 analysts.

    Writes to the report thread and is visible to the managed services team. Comments cannot
    be deleted through this API, so review the text before sending."""
    source_id = str(source_id or "").strip()
    if not source_id:
        return _err("source_id is required")
    if not comment_text or not comment_text.strip():
        return _err("comment_text is required")
    if len(comment_text) > COMMENT_MAX_LEN:
        return _err(f"comment_text is {len(comment_text)} characters; the API limit is {COMMENT_MAX_LEN}.")
    if not created_by or not created_by.strip():
        return _err("created_by is required — the API rejects comments without an author")

    payload = {
        "xsoar_source_id": source_id,
        "comment_text": comment_text,
        "comment_created_by": created_by.strip(),
    }
    if path_to_file:
        if not path_to_file.startswith(ATTACHMENT_PREFIXES):
            return _err(f"path_to_file must start with one of {list(ATTACHMENT_PREFIXES)} — got '{path_to_file}'")
        payload["path_to_file"] = path_to_file
        # The API rejects a JSON boolean here; it must be a string.
        payload["extract_zip_file"] = "true" if extract_zip_file else "false"

    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(f"{MTH_BASE}/add_comment", data={"request_data": payload})
        reply = response.get("reply") if isinstance(response, dict) else response
        return create_response(data={"added": bool(reply), "source_id": source_id, "reply": reply})
    except PAPI_ERRORS as e:
        return create_response(data=_papi_error(e), is_error=True)
    except Exception as e:
        logger.exception(f"add_mdr_report_comment failed: {e}")
        return _err(str(e))


async def update_mdr_report_status(
    ctx: Context,
    source_id: Annotated[str, Field(
        description="XSOAR source ID of the report. An array is accepted by the API but only its first element is used."
    )],
    report_status: Annotated[str, Field(
        description='New status: "New", "In Progress", "On Hold", "Resolved False Positive", '
                    '"Resolved True Positive", "Resolved Other" or "Resolved Security Testing". '
                    'There is no bare "Resolved".'
    )],
    raw: Annotated[bool, Field(description="Return the untouched API response.")] = False,
) -> str:
    """Updates the workflow status of an MDR/MTH report.

    Moves a report through triage (New -> In Progress -> On Hold -> one of the four Resolved
    states). Reversible: call again with the previous status. Returns the updated report;
    its comments and attachments are always null on this endpoint."""
    source_id = str(source_id or "").strip()
    if not source_id:
        return _err("source_id is required")
    status = (report_status or "").strip()
    if status not in STATUS_DISPLAY:
        return _err(f"Invalid report_status '{report_status}'. Valid values: {STATUS_DISPLAY}")

    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(
            f"{MTH_BASE}/report/update/status",
            data={"request_data": {"xsoar_source_id": source_id, "report_status": status}})
        if raw:
            return create_response(data={"raw": response})
        rows, _ = _unwrap(response)
        report = _normalize_report(rows[0]) if rows else None
        return create_response(data={"updated": True, "source_id": source_id, "report_status": status,
                                     "report": report})
    except PAPI_ERRORS as e:
        return create_response(data=_papi_error(e), is_error=True)
    except Exception as e:
        logger.exception(f"update_mdr_report_status failed: {e}")
        return _err(str(e))


async def update_mdr_report_assignment(
    ctx: Context,
    source_id: Annotated[str, Field(description="XSOAR source ID of the report to assign.")],
    user: Annotated[Optional[str], Field(
        description="Identifier (usually email) of the assignee. Validated against the tenant's users."
    )] = None,
    username: Annotated[Optional[str], Field(
        description="Display name of the assignee. Free text; forced to null when the assignment is cleared."
    )] = None,
    clear_assignment: Annotated[bool, Field(
        description="Set true to explicitly UNASSIGN the report. Required when user is omitted."
    )] = False,
    raw: Annotated[bool, Field(description="Return the untouched API response.")] = False,
) -> str:
    """Assigns an MDR/MTH report to a user, or clears the assignment.

    The API treats a missing user as "clear the assignment", so this tool requires either a
    user or an explicit clear_assignment=True rather than silently unassigning. Reversible:
    call again with the previous assignee."""
    source_id = str(source_id or "").strip()
    if not source_id:
        return _err("source_id is required")
    user = user.strip() if isinstance(user, str) else user
    if user and clear_assignment:
        return _err("Pass either user or clear_assignment=True, not both.")
    if not user and not clear_assignment:
        return _err("No user given. Pass user='<email>' to assign, or clear_assignment=True to unassign — "
                    "the API would otherwise clear the existing assignment silently.")

    payload = {"xsoar_source_id": source_id}
    if clear_assignment:
        payload["user"] = None
        payload["username"] = None
    else:
        payload["user"] = user
        if username:
            payload["username"] = username

    try:
        fetcher = await get_fetcher(ctx)
        response = await fetcher.send_request(f"{MTH_BASE}/report/update/assign", data={"request_data": payload})
        if raw:
            return create_response(data={"raw": response})
        rows, _ = _unwrap(response)
        report = _normalize_report(rows[0]) if rows else None
        return create_response(data={"updated": True, "source_id": source_id,
                                     "assigned_user": None if clear_assignment else user,
                                     "cleared": clear_assignment, "report": report})
    except PAPI_ERRORS as e:
        return create_response(data=_papi_error(e), is_error=True)
    except Exception as e:
        logger.exception(f"update_mdr_report_assignment failed: {e}")
        return _err(str(e))


class MDRReportsModule(BaseModule):
    """MDR/MTH managed threat detection reports: read, comment, status, assignment."""
    def register_tools(self):
        self._add_tool(get_mdr_reports)
        self._add_tool(get_mdr_report_comments)
        self._add_tool(add_mdr_report_comment)
        self._add_tool(update_mdr_report_status)
        self._add_tool(update_mdr_report_assignment)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
