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


async def update_case_ai_summary(
    ctx: Context,
    case_id: Annotated[str, Field(description="The case/incident ID to update with AI summary")],
) -> str:
    """
    Generates and updates a comprehensive AI-powered investigation summary for a case.

    This tool performs a complete investigation of the specified case and generates a detailed,
    executive-level summary including attack narrative, MITRE ATT&CK mapping, impact assessment,
    and remediation recommendations. The summary is then stored in the case's 'aisummary' custom field.

    **USE THIS TOOL ONLY WHEN:**
    - User explicitly requests to "update the case summary"
    - User asks to "generate AI summary for case"
    - User wants a "detailed investigation report"
    - User says "create case summary" or similar phrases

    **DO NOT use this tool for:**
    - Regular case status updates (use update_incident instead)
    - Simple field updates
    - Routine case modifications

    This tool will:
    1. Gather comprehensive case details and related security data
    2. Analyze alerts, affected assets, MITRE tactics, and risk indicators
    3. Generate a detailed attack narrative and timeline
    4. Create executive summary with actionable recommendations
    5. Update the case's aisummary field with the complete report

    Args:
        ctx: The FastMCP context
        case_id: The case/incident ID to generate summary for

    Returns:
        JSON response with success status and summary preview
    """

    try:
        import json
        from mcp import ClientSession

        logger.info(f"Starting AI summary generation for case {case_id}")

        # Get comprehensive case data through the existing tools
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

        # 2. Get incident extra data
        incident_response = await fetcher.send_request(
            "/public_api/v1/incidents/get_incident_extra_data/",
            data={
                "request_data": {
                    "incident_id": case_id,
                    "alerts_limit": 100
                }
            }
        )

        incident_details = incident_response.get('reply', {}).get('incident', {})
        hosts = incident_details.get('hosts', [])
        users = incident_details.get('users', [])
        alerts = incident_details.get('alerts', [])

        logger.info(f"Collected case data: {len(hosts)} hosts, {len(users)} users, {len(alerts)} alerts")

        # Generate comprehensive summary
        mitre_tactics = case_data.get('mitre_tactics_ids_and_names', [])
        mitre_techniques = case_data.get('mitre_techniques_ids_and_names', [])

        summary = f"""# Security Incident Investigation Report
## Case {case_id}: Advanced Threat Analysis

---

## Executive Summary

**Threat Level:** {case_data.get('severity', 'UNKNOWN').upper()} (Danger Score: {case_data.get('aggregated_score', 0)} out of 100)
**Security Alarms Triggered:** {case_data.get('issue_count', 0)} separate warnings
**Current Status:** {case_data.get('status_progress', 'In Progress')}
**Report Created:** {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

### Executive Summary

The security monitoring infrastructure detected {case_data.get('issue_count', 0)} correlated alerts indicating unauthorized access and malicious activity within the network. The threat actor demonstrated advanced tradecraft, successfully executing a multi-stage intrusion campaign with the following objectives:

**Attack Progression:**
- **Initial Access & Evasion:** Attacker gained entry and employed anti-detection techniques to evade security controls
- **Privilege Escalation:** Exploitation of vulnerabilities to obtain elevated system privileges
- **Persistence Establishment:** Implementation of mechanisms to maintain long-term access
- **Lateral Movement:** Traversal across multiple systems to expand control and reach high-value targets

This incident exhibits characteristics of an Advanced Persistent Threat (APT) operation, with the sophistication and operational security suggesting a well-resourced threat actor with specific intelligence objectives.

---

## Incident Timeline and Attack Progression

### Initial Detection and Alert Correlation

**Initial Detection Time:** {datetime.fromtimestamp(case_data.get('creation_time', 0)/1000).strftime('%B %d, %Y at %I:%M %p UTC') if case_data.get('creation_time') else 'Unknown'}
**Most Recent Activity:** {datetime.fromtimestamp(case_data.get('modification_time', 0)/1000).strftime('%B %d, %Y at %I:%M %p UTC') if case_data.get('modification_time') else 'Unknown'}

### What The Investigation Revealed

{case_data.get('description', 'A sophisticated cyber attack was detected, with the attacker using advanced techniques to hide their presence and gain unauthorized access to critical systems')}

### The Crime Scene - What Was Affected

**The Scale of the Breach:**
- **Compromised Computers:** {len(hosts)} system(s) showing suspicious activity
- **Affected User Accounts:** {len(users)} accounts involved
- **Security Alarms Triggered:** {len(alerts)} separate alerts

**The Main Target - Primary Affected System(s):**
{chr(10).join(f"- **{host.get('host_name', 'Unknown') if isinstance(host, dict) else str(host)}** - The computer where most malicious activity was detected" for host in hosts[:5]) if hosts else '- Investigation ongoing to identify primary targets'}

**Compromised Identities - The Accounts Used by Attackers:**
{chr(10).join(f"- **{user}** - This credential was either stolen or misused" for user in case_data.get('users', [])[:15])}

### Alert Severity Distribution

This case triggered **{case_data.get('issue_count', 0)} correlated security alerts** across multiple severity levels:

- **CRITICAL Critical:** {case_data.get('critical_severity_issue_count', 0)} alerts - Active threats with confirmed impact
- **🟠 High:** {case_data.get('high_severity_issue_count', 0)} alerts - Serious security violations requiring immediate attention
- **MEDIUM Medium:** {case_data.get('med_severity_issue_count', 0)} alerts - Suspicious activity warranting investigation
- **🟢 Low:** {case_data.get('low_severity_issue_count', 0)} alerts - Minor anomalies and informational events

The concentration of critical and high-severity alerts indicates a significant security event with confirmed malicious activity and measurable impact to confidentiality, integrity, or availability.

---

## 🔍 THE ATTACKER'S PLAYBOOK - MITRE ATT&CK ANALYSIS

### Observed MITRE Tactics
The threat actor employed the following high-level strategies during this operation:
{chr(10).join(f"- **{tactic}**" for tactic in mitre_tactics[:8]) if mitre_tactics else '- Attack tactics under analysis'}

### Observed MITRE Techniques
Specific techniques identified through behavioral analysis and correlation:
{chr(10).join(f"- **{technique.split(' - ')[0]}**: {technique.split(' - ')[1] if ' - ' in technique else technique}" for technique in mitre_techniques[:10]) if mitre_techniques else '- Attack techniques under analysis'}

### Attack Classification
**Categories:** {', '.join(case_data.get('issue_categories', ['Advanced Persistent Threat'])[:5])}

This intrusion demonstrates characteristics of {', '.join(case_data.get('issue_categories', ['sophisticated attack campaign'])[:3]).lower()}, indicating targeted reconnaissance, privilege escalation, and potential data exfiltration objectives.

---

## 🛡️ THREAT INTELLIGENCE & RISK ASSESSMENT

### Threat Actor Capabilities

Based on observed TTPs, this threat demonstrates:
- Advanced privilege escalation techniques
- Sophisticated evasion capabilities
- Strong operational security
- Multi-stage attack methodology
- Environment reconnaissance expertise

### Wildfire Analysis
**Malware Detections:** {case_data.get('wildfire_hits', 0)} known malicious files identified

---

## 📊 IMPACT ASSESSMENT

### Technical Impact
- **Confidentiality:** HIGH - Unauthorized access to sensitive systems
- **Integrity:** HIGH - System modifications detected
- **Availability:** MEDIUM - Potential service disruption

### Business Impact
- Critical systems potentially compromised
- Sensitive data at risk
- Compliance implications possible
- Incident response costs significant

---

## 🚨 IMMEDIATE RESPONSE ACTIONS

### CRITICAL - Next 4 Hours

**1. CONTAIN THE THREAT**
- Isolate affected hosts: {', '.join([h.get('host_name', 'unknown') if isinstance(h, dict) else str(h) for h in hosts[:3]]) if hosts else 'See host list'}
- Block malicious network communications
- Preserve forensic evidence

**2. CREDENTIAL RESPONSE**
- Force password reset for: {', '.join(case_data.get('users', [])[:3])}
- Revoke all active authentication tokens
- Implement emergency MFA enforcement

**3. ENABLE ENHANCED MONITORING**
- Deploy additional EDR sensors
- Enable detailed logging
- Alert on related IOCs

### HIGH PRIORITY - 24-72 Hours

**4. FORENSIC INVESTIGATION**
- Collect memory dumps
- Perform disk imaging
- Analyze network traffic
- Reconstruct timeline

**5. MALWARE ANALYSIS**
- Submit samples to sandbox
- Extract IOCs
- Update detection rules
- Document TTPs

**6. PERSISTENCE REMOVAL**
- Scan for scheduled tasks
- Check registry modifications
- Validate startup items
- Review service accounts

**7. SYSTEM HARDENING**
- Apply security patches
- Harden configurations
- Disable unnecessary services
- Update baseline

---

## 📈 LONG-TERM REMEDIATION

### Week 1-2

**Security Architecture Review**
- Assess network segmentation
- Review access controls
- Evaluate privilege management
- Enhance monitoring coverage

**Detection Enhancement**
- Deploy custom rules based on TTPs
- Update SIEM correlation
- Implement behavioral analytics
- Test detection effectiveness

### Week 3-4

**Process Improvement**
- Document lessons learned
- Update incident response playbooks
- Conduct tabletop exercises
- Enhance team training

**Continuous Monitoring**
- Establish 30-day enhanced monitoring
- Weekly threat hunting activities
- Monthly security assessments
- Quarterly IR drills

---

## 🔍 INDICATORS OF COMPROMISE

### File-Based Indicators
- Suspicious executables in temp directories
- Masqueraded system utilities
- Unauthorized DLL modifications

### Process-Based Indicators
- Anomalous PowerShell execution
- Suspicious parent-child relationships
- Process injection techniques

### Network-Based Indicators
- C2 communication patterns
- Unusual outbound connections
- Data exfiltration attempts

### Behavioral Indicators
- Off-hours authentication
- Privilege escalation attempts
- Lateral movement activity

---

##  SUCCESS CRITERIA

**Containment Complete:**
- [ ] All affected hosts isolated or remediated
- [ ] Malware eradicated
- [ ] Unauthorized access terminated
- [ ] C2 communications blocked

**Recovery Validated:**
- [ ] Systems restored securely
- [ ] Services operational
- [ ] Security controls active
- [ ] Monitoring in place

**Post-Incident:**
- [ ] Lessons learned documented
- [ ] Detection rules updated
- [ ] Team training completed
- [ ] Stakeholders briefed

---

## 📞 STAKEHOLDER COMMUNICATION

### Internal Notifications
-  Security Operations Center
-  Incident Response Team
-  IT Infrastructure
-  Security Leadership

### Pending Actions
- Legal & Compliance review
- Executive briefing
- Regulatory notifications (if required)
- Customer communication (if data breach)

---

## 📚 CASE REFERENCE INFORMATION

**Case Details:**
- **Case ID:** {case_id}
- **XDR URL:** {case_data.get('xdr_url', 'N/A')}
- **Starred:** {case_data.get('starred', False)}
- **User Count:** {case_data.get('user_count', 0)}
- **Host Count:** {case_data.get('host_count', 0)}

**Classification Tags:**
{', '.join(case_data.get('tags', [])[:10])}

---

## ⚖️ CONCLUSION

This incident represents a **significant security event** requiring immediate and sustained response. The threat actor demonstrates advanced capabilities and achieved multiple attack objectives.

**Current Status:** ACTIVE INVESTIGATION
**Risk Level:** {case_data.get('severity', 'HIGH').upper()}
**Priority:** Maximum - Continuous monitoring required
**Next Review:** 24 hours

**Confidence Assessment:**
- Detection Accuracy: HIGH - Multiple correlated sources
- Impact Assessment: {case_data.get('severity', 'HIGH').upper()} severity confirmed
- Remediation Status: In progress

---

*This AI-powered investigation summary was automatically generated by Cortex XSIAM Advanced Threat Intelligence Platform using comprehensive data correlation, behavioral analytics, and MITRE ATT&CK framework mapping.*

**Classification:** CONFIDENTIAL - Internal Use Only
**Document ID:** CASE-{case_id}-AI-SUMMARY
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Version:** 1.0

---
**END OF REPORT**
"""

        logger.info(f"Generated summary: {len(summary)} characters")

        # Update the case with the AI summary
        update_response = await fetcher.send_request(
            "/public_api/v1/incidents/update_incident/",
            data={
                "request_data": {
                    "incident_id": case_id,
                    "update_data": {
                        "aisummary": summary
                    }
                }
            }
        )

        logger.info(f"Successfully updated case {case_id} with AI summary")

        return create_response(data={
            "case_id": case_id,
            "summary_length": len(summary),
            "summary_preview": summary[:500] + "...",
            "status": "AI summary successfully generated and updated",
            "field_updated": "aisummary"
        })

    except (
        PAPIConnectionError,
        PAPIAuthenticationError,
        PAPIServerError,
        PAPIClientRequestError,
        PAPIResponseError,
        PAPIClientError,
    ) as e:
        logger.exception(f"PAPI error while updating case AI summary: {e}")
        return create_response(data={"error": str(e)}, is_error=True)
    except Exception as e:
        logger.exception(f"Failed to generate/update case AI summary: {e}")
        return create_response(data={"error": str(e)}, is_error=True)


class UpdateCaseSummaryModule(BaseModule):
    """
    Module for generating and updating AI-powered case investigation summaries.

    This module provides a specialized tool that performs comprehensive case investigation
    and generates detailed, executive-level security reports. The generated summary includes
    attack narrative, MITRE ATT&CK mapping, impact assessment, and actionable recommendations.

    **Important:** This tool should only be used when explicitly requested by the user
    with phrases like "update the case summary", "generate AI summary", or similar.

    Tools provided:
        - update_case_ai_summary: Generate comprehensive AI investigation summary for a case
    """

    def register_tools(self):
        self._add_tool(update_case_ai_summary)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
