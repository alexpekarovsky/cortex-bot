"""
Case Timeline Generator

Generates and updates a visual HTML timeline for a case showing all alerts/issues
chronologically with severity-based color coding and detailed event information.
"""

import logging
from typing import Annotated
from datetime import datetime

from fastmcp import Context, FastMCP
from pydantic import Field

from entities.exceptions import (
    PAPIAuthenticationError,
    PAPIClientError,
    PAPIClientRequestError,
    PAPIConnectionError,
    PAPIResponseError,
    PAPIServerError,
)
from pkg.util import create_response
from usecase.base_module import BaseModule
from usecase.fetcher import get_fetcher

logger = logging.getLogger(__name__)


def _get_severity_color(severity: str) -> str:
    """Return CSS color based on severity level."""
    colors = {
        "critical": "#8B0000",  # Dark red
        "high": "#DC3545",      # Red
        "medium": "#FD7E14",    # Orange
        "low": "#0D6EFD",       # Blue
        "informational": "#6C757D",  # Gray
    }
    return colors.get(severity.lower(), "#6C757D")


def _get_severity_icon(severity: str) -> str:
    """Return emoji icon based on severity level."""
    icons = {
        "critical": "&#x1F6A8;",  # Rotating light
        "high": "&#x26A0;",       # Warning
        "medium": "&#x1F7E0;",    # Orange circle
        "low": "&#x1F535;",       # Blue circle
        "informational": "&#x2139;",  # Info
    }
    return icons.get(severity.lower(), "&#x2022;")


def _format_timestamp(ts: int) -> str:
    """Convert millisecond timestamp to readable format."""
    if not ts:
        return "Unknown"
    try:
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, OSError):
        return "Invalid timestamp"


def _generate_html_timeline(case_data: dict, alerts: list, incident_details: dict) -> str:
    """Generate a comprehensive HTML timeline visualization optimized for dark backgrounds."""

    case_id = case_data.get("case_id", "Unknown")
    case_name = case_data.get("description", "Security Incident")
    severity = case_data.get("severity", "medium")
    creation_time = case_data.get("creation_time", 0)

    # Sort alerts by detection timestamp
    sorted_alerts = sorted(
        alerts,
        key=lambda x: x.get("detection_timestamp") or x.get("local_insert_ts") or 0
    )

    # Severity class mapping for the vertical timeline
    def get_sev_class(sev: str) -> str:
        return {
            "critical": "critical-sev",
            "high": "high-sev",
            "medium": "medium-sev",
            "low": "low-sev",
        }.get(sev.lower(), "medium-sev")

    # Generate timeline items - simple vertical layout
    timeline_items = ""
    for alert in sorted_alerts:
        alert_severity = alert.get("severity", "medium")
        alert_name = alert.get("name", "Unknown Alert")
        alert_id = alert.get("alert_id", "N/A")
        detection_time = alert.get("detection_timestamp") or alert.get("local_insert_ts")
        category = alert.get("category", "Unknown")
        host_name = alert.get("host_name", "N/A")
        user_name = alert.get("user_name", "N/A")
        mitre_tactic = alert.get("mitre_tactic_id_and_name", "")
        mitre_technique = alert.get("mitre_technique_id_and_name", "")
        description = alert.get("description", "")[:200]

        formatted_time = _format_timestamp(detection_time)
        sev_class = get_sev_class(alert_severity)

        mitre_html = ""
        if mitre_tactic:
            mitre_html = f'<div class="mitre">&#x1F3AF; MITRE: {mitre_tactic} | {mitre_technique}</div>'

        timeline_items += f'''
    <div class="event {sev_class}">
        <div class="event-header">
            <span class="sev-badge sev-{alert_severity.lower()}">{alert_severity.upper()}</span>
            <span class="alert-id">Alert #{alert_id}</span>
        </div>
        <h3>{alert_name}</h3>
        <p><strong>Host:</strong> {host_name} | <strong>User:</strong> {user_name} | <strong>Category:</strong> {category}</p>
        {mitre_html}
        <p class="desc">{description}...</p>
        <div class="time">&#x1F4C5; {formatted_time}</div>
    </div>
'''

    # Build the complete HTML - optimized for dark backgrounds (XSIAM default)
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: transparent;
    color: #e2e8f0;
    padding: 16px;
    line-height: 1.5;
}}
.header {{
    text-align: center;
    padding: 20px;
    background: rgba(30, 41, 59, 0.8);
    border-radius: 12px;
    margin-bottom: 24px;
    border: 1px solid rgba(148, 163, 184, 0.2);
}}
.header h1 {{
    color: #f8fafc;
    font-size: 1.5em;
    margin-bottom: 8px;
    font-weight: 600;
}}
.header p {{
    color: #94a3b8;
    font-size: 0.9em;
}}
.badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 0.75em;
    font-weight: 600;
    margin: 8px 4px 0;
}}
.badge-critical {{ background: #991b1b; color: white; }}
.badge-high {{ background: #dc2626; color: white; }}
.badge-medium {{ background: #ea580c; color: white; }}
.badge-low {{ background: #2563eb; color: white; }}
.badge-severity {{ background: {_get_severity_color(severity)}; color: white; }}
.stats {{
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 20px 0;
    flex-wrap: wrap;
}}
.stat {{
    background: rgba(30, 41, 59, 0.6);
    padding: 12px 20px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    min-width: 80px;
}}
.stat-val {{
    font-size: 1.75em;
    font-weight: 700;
    line-height: 1.2;
}}
.stat-label {{
    font-size: 0.75em;
    color: #94a3b8;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.critical {{ color: #fca5a5; }}
.high {{ color: #f87171; }}
.medium {{ color: #fb923c; }}
.low {{ color: #60a5fa; }}
.success {{ color: #4ade80; }}
.info {{ color: #38bdf8; }}
.timeline {{
    position: relative;
    padding: 20px 0;
    margin-left: 20px;
}}
.timeline::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(180deg, #ef4444 0%, #f97316 50%, #3b82f6 100%);
    border-radius: 2px;
}}
.event {{
    position: relative;
    margin-left: 30px;
    margin-bottom: 20px;
    padding: 16px;
    background: rgba(30, 41, 59, 0.7);
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.15);
}}
.event::before {{
    content: "";
    position: absolute;
    left: -34px;
    top: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 3px solid;
}}
.event.critical-sev::before {{ border-color: #dc2626; background: #1e293b; }}
.event.high-sev::before {{ border-color: #ef4444; background: #1e293b; }}
.event.medium-sev::before {{ border-color: #f97316; background: #1e293b; }}
.event.low-sev::before {{ border-color: #3b82f6; background: #1e293b; }}
.event-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    flex-wrap: wrap;
}}
.sev-badge {{
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7em;
    font-weight: 700;
    color: white;
    text-transform: uppercase;
}}
.sev-critical {{ background: #991b1b; }}
.sev-high {{ background: #dc2626; }}
.sev-medium {{ background: #ea580c; }}
.sev-low {{ background: #2563eb; }}
.alert-id {{
    color: #64748b;
    font-size: 0.8em;
}}
.event h3 {{
    color: #f1f5f9;
    font-size: 1em;
    font-weight: 600;
    margin-bottom: 8px;
    line-height: 1.4;
}}
.event p {{
    color: #cbd5e1;
    font-size: 0.85em;
    line-height: 1.5;
    margin-bottom: 8px;
}}
.event p strong {{
    color: #e2e8f0;
}}
.desc {{
    color: #94a3b8 !important;
    font-style: italic;
}}
.mitre {{
    background: rgba(251, 146, 60, 0.15);
    border: 1px solid rgba(251, 146, 60, 0.3);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.8em;
    color: #fdba74;
    margin-bottom: 8px;
}}
.time {{
    color: #64748b;
    font-size: 0.75em;
}}
.footer {{
    text-align: center;
    padding: 20px;
    color: #64748b;
    font-size: 0.8em;
    margin-top: 10px;
}}
</style>
</head>
<body>
<div class="header">
    <h1>&#x1F6E1; Case {case_id} - Investigation Timeline</h1>
    <p>{case_name[:100]}</p>
    <span class="badge badge-severity">{severity.upper()} SEVERITY</span>
</div>

<div class="stats">
    <div class="stat"><div class="stat-val critical">{case_data.get('critical_severity_issue_count', 0)}</div><div class="stat-label">Critical</div></div>
    <div class="stat"><div class="stat-val high">{case_data.get('high_severity_issue_count', 0)}</div><div class="stat-label">High</div></div>
    <div class="stat"><div class="stat-val medium">{case_data.get('med_severity_issue_count', 0)}</div><div class="stat-label">Medium</div></div>
    <div class="stat"><div class="stat-val low">{case_data.get('low_severity_issue_count', 0)}</div><div class="stat-label">Low</div></div>
    <div class="stat"><div class="stat-val success">{case_data.get('host_count', 0)}</div><div class="stat-label">Hosts</div></div>
    <div class="stat"><div class="stat-val info">{case_data.get('user_count', 0)}</div><div class="stat-label">Users</div></div>
</div>

<div class="timeline">
{timeline_items}
</div>

<div class="footer">
    &#x1F916; Generated by Cortex XSIAM MCP | {datetime.now().strftime('%Y-%m-%d')}
</div>
</body>
</html>'''
    return html


async def update_case_timeline(
    ctx: Context,
    case_id: Annotated[str, Field(description="The case/incident ID to generate timeline for")],
) -> str:
    """
    Generates and updates a visual HTML timeline for a case showing all alerts chronologically.

    This tool creates a comprehensive, interactive HTML timeline visualization that displays
    all alerts/issues in a case with:
    - Severity-based color coding (critical=dark red, high=red, medium=orange, low=blue)
    - Chronological ordering of events
    - MITRE ATT&CK tactic/technique mapping
    - Alert details including host, user, category, and description
    - Statistics summary (alert counts by severity, hosts, users)

    The generated timeline is stored in the case's 'dynamictimeline' custom field and can
    be viewed in the XSIAM case interface.

    **USE THIS TOOL WHEN:**
    - User requests a "visual timeline" for a case
    - User asks to "generate timeline" or "update timeline"
    - User wants to see the "attack progression" visually
    - User requests "chronological view" of alerts

    Args:
        ctx: The FastMCP context
        case_id: The case/incident ID to generate timeline for (e.g., "350")

    Returns:
        JSON response with success status and timeline preview
    """

    try:
        logger.info(f"Starting timeline generation for case {case_id}")
        fetcher = await get_fetcher(ctx)

        # 1. Get case details
        case_response = await fetcher.send_request(
            "/public_api/v1/case/search/",
            data={
                "request_data": {
                    "filters": [{"field": "case_id", "operator": "in", "value": [int(case_id)]}],
                    "search_from": 0,
                    "search_to": 1
                }
            }
        )

        if 'reply' not in case_response or 'DATA' not in case_response['reply']:
            return create_response(
                data={"error": f"Case {case_id} not found"},
                is_error=True
            )

        case_data = case_response['reply']['DATA'][0]

        # 2. Get incident extra data with alerts
        incident_response = await fetcher.send_request(
            "/public_api/v1/incidents/get_incident_extra_data/",
            data={
                "request_data": {
                    "incident_id": case_id,
                    "alerts_limit": 100
                }
            }
        )

        incident_details = incident_response.get('reply', {})
        alerts_data = incident_details.get('alerts', {})
        alerts = alerts_data.get('data', []) if isinstance(alerts_data, dict) else []

        logger.info(f"Collected {len(alerts)} alerts for timeline")

        # 3. Generate HTML timeline
        html_timeline = _generate_html_timeline(case_data, alerts, incident_details)

        logger.info(f"Generated timeline HTML: {len(html_timeline)} characters")

        # 4. Update the case with the timeline
        update_response = await fetcher.send_request(
            "/public_api/v1/incidents/update_incident/",
            data={
                "request_data": {
                    "incident_id": case_id,
                    "update_data": {
                        "timeline": html_timeline
                    }
                }
            }
        )

        logger.info(f"Successfully updated case {case_id} with dynamic timeline")

        return create_response(data={
            "case_id": case_id,
            "timeline_length": len(html_timeline),
            "alerts_included": len(alerts),
            "status": "Timeline successfully generated and updated",
            "field_updated": "timeline",
            "preview": f"Timeline includes {len(alerts)} alerts from {case_data.get('creation_time', 'unknown')} to present"
        })

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while updating case timeline: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to generate/update case timeline: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class UpdateCaseTimelineModule(BaseModule):
    """
    Module for generating and updating visual HTML timelines for security cases.

    This module provides a specialized tool that creates interactive, visually appealing
    HTML timeline visualizations for security incidents. The timeline shows all alerts
    chronologically with severity-based color coding and detailed event information.

    Tools provided:
        - update_case_timeline: Generate visual HTML timeline for a case
    """

    def register_tools(self):
        self._add_tool(update_case_timeline)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
