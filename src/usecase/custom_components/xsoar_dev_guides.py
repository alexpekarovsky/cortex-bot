"""
XSOAR Development Pattern Guides

Provides comprehensive development guides for XSOAR integrations as MCP tools.
AI assistants can call these tools to learn the correct patterns for different
types of integrations (long-running, event collectors, regular integrations).

All guide content is embedded in this file as string constants.
"""

import logging
from typing import Annotated
from fastmcp import Context, FastMCP
from pydantic import Field
from pkg.util import create_response
from usecase.base_module import BaseModule

logger = logging.getLogger(__name__)

# ============================================================================
# PATTERN RECOGNITION GUIDE
# ============================================================================

PATTERN_RECOGNITION_GUIDE = """
# XSOAR Integration Pattern Recognition Guide

## How to Automatically Identify the Correct Pattern

Read the user's request and match keywords/intent to these patterns:

---

### Pattern 1: Long-Running Integration

**Official PANW Term:** "Long-Running Integration"
**YAML Config:** `longRunning: true`

**USER REQUEST INDICATORS (Keywords to detect):**
- "Monitor [service/host/application]"
- "Continuously check [something]"
- "Check [X] every [Y] seconds/minutes"
- "Receive webhooks from [Slack/Teams/GitHub/etc]"
- "Listen for [events/requests]"
- "Keep checking [status/health]"
- "Real-time monitoring"
- "Always running"
- ANY request for continuous, never-stopping operation

**YAML CONFIGURATION:**
```yaml
script:
  longRunning: true
  longRunningPort: false  # true if exposing HTTP endpoint
```

**ARCHITECTURE REQUIREMENTS:**
- ✅ `while True` loop in `long_running_execution_command()`
- ✅ ALL logic runs in MAIN THREAD (no background threads for main work)
- ✅ Use `demisto.setIntegrationContext()` for state persistence
- ✅ Use `demisto.createIncidents()` to create alerts/incidents
- ❌ NEVER use background threading for main monitoring logic
- ❌ NEVER use `demisto.executeCommand()` (integrations only)
- ❌ NEVER exit the while loop

**EXAMPLES:** Ping monitor, webhook receiver, service health checker, real-time log listener

---

### Pattern 2: Event Collector Integration

**Official PANW Term:** "Event Collector" or "Fetch Integration"
**YAML Config:** `isFetch: true` and/or `isFetchEvents: true`

**USER REQUEST INDICATORS (Keywords to detect):**
- "Fetch [tickets/logs/alerts/events] from [system]"
- "Pull data from [ServiceNow/Jira/Splunk/external API]"
- "Import [incidents/events/records] to XSIAM"
- "Get new [items] every X minutes"
- "Collect [data/logs] and send to XSIAM"
- "Sync [tickets/issues] from [external source]"
- "Retrieve [data] periodically"
- "Ingest [logs/events] into XSIAM"

**YAML CONFIGURATION:**
```yaml
script:
  isfetch: true          # Enable fetching
  isFetchEvents: true    # For event collectors specifically
```

**ARCHITECTURE REQUIREMENTS:**
- ✅ Implement `fetch-incidents` or `fetch-events` command
- ✅ Use `send_events_to_xsiam(events, vendor='X', product='Y')`
- ✅ Use `demisto.getLastRun()` / `demisto.setLastRun()` for tracking last fetch
- ✅ Handle pagination for large datasets
- ✅ Implement deduplication to avoid sending duplicates
- ✅ Use `params.get('first_fetch')` for initial fetch time range

**EXAMPLES:** ServiceNow ticket fetcher, Splunk log collector, Jira issue importer, Syslog collector

---

### Pattern 3: Regular Integration

**Official PANW Term:** "Integration"
**YAML Config:** No special flags (default)

**USER REQUEST INDICATORS (Keywords to detect):**
- "Query [API] for [information]"
- "Get [specific data] from [system]"
- "Run command to [perform action]"
- "Lookup [IP/domain/hash] in [system]"
- "Search for [something]"
- "Execute [one-time operation]"
- On-demand operations with no continuous running or periodic fetching

**YAML CONFIGURATION:**
```yaml
script:
  # No special flags needed
  type: python
  subtype: python3
```

**ARCHITECTURE:**
- ✅ Implement commands as individual functions
- ✅ Each command executes once and returns
- ✅ No continuous running, no periodic fetching
- ✅ Can have multiple commands

**EXAMPLES:** IP enrichment, domain lookup, one-time data queries, REST API wrappers

---

## Decision Tree

```
User request contains:
├─ "monitor", "continuously", "every X seconds", "webhook", "listen"
│  └─> LONG-RUNNING INTEGRATION
│      Call: get_xsoar_long_running_guide()
│
├─ "fetch", "pull", "import", "collect", "send to XSIAM", "ingest"
│  └─> EVENT COLLECTOR INTEGRATION
│      Call: get_xsoar_event_collector_guide()
│
├─ "poll", "sandbox", "async", "wait for results", "submit and check", "scan file"
│  └─> SCHEDULED COMMANDS (Polling Pattern)
│      Call: get_xsoar_scheduled_commands_guide()
│
├─ "sync", "mirror", "bidirectional", "two-way", "chat integration"
│  └─> MIRRORING INTEGRATION
│      Call: get_xsoar_mirroring_guide()
│
├─ "threat feed", "indicators", "IOC", "TAXII", "STIX", "feed"
│  └─> FEED INTEGRATION
│      Call: get_xsoar_feed_guide()
│
└─ "query", "get", "lookup", "search" (one-time)
   └─> REGULAR INTEGRATION
       Use standard integration pattern (no special guide needed)
```

---

## Important: When to Call Which Guide

**BEFORE starting ANY integration development:**

1. Analyze user's request
2. Match keywords to patterns above
3. Call appropriate guide tool:
   - Long-running → `get_xsoar_long_running_guide()`
   - Event collector → `get_xsoar_event_collector_guide()`
4. Read guide completely
5. Implement following the patterns EXACTLY

**Don't guess!** If user says "monitor Redis", that's continuous operation → long-running integration.
"""

# ============================================================================
# LONG-RUNNING INTEGRATION GUIDE
# ============================================================================

LONG_RUNNING_GUIDE = """
# XSOAR Long-Running Integration Complete Guide

> Based on actual debugging experience with PingMonitor integration

## Architecture Overview

Long-running integrations run in a dedicated Docker container that **NEVER STOPS**. The `long-running-execution` command contains a `while True` loop that runs forever in the MAIN THREAD.

```python
def long_running_execution_command(params: dict):
    # Initialize
    ctx = demisto.getIntegrationContext()

    # NEVER-ENDING LOOP - All logic in MAIN THREAD
    while True:
        try:
            # Do work
            result = check_something()

            # Update state
            demisto.setIntegrationContext(new_state)

        except Exception as e:
            demisto.error(f'Error: {e}')
            # NEVER exit!

        time.sleep(interval)
```

---

## ❌ CRITICAL MISTAKES (From Real Debugging)

### ❌ MISTAKE #1: Using Background Threads

**DON'T DO THIS (WILL FAIL):**
```python
import threading  # ❌ Remove this!

def long_running_execution_command(params):
    # ❌ Creating background thread
    thread = threading.Thread(target=monitor_loop, args=(params,))
    thread.daemon = True
    thread.start()

    # Main loop just sleeps
    while True:
        time.sleep(60)  # ❌ Main thread does nothing!

def monitor_loop(params):
    while True:
        demisto.info('Checking...')  # ❌ FAILS WITH: NameError: name 'SERVER_ERROR_MARKER' is not defined
        do_work()
```

**ERROR YOU'LL GET:**
```
NameError: name 'SERVER_ERROR_MARKER' is not defined
```

**WHY IT FAILS:**
XSOAR's containerized environment does NOT support calling `demisto.info()`, `demisto.error()`, or other demisto functions from background threads. The `SERVER_ERROR_MARKER` variable is not accessible in thread context.

**THE FIX:**
```python
# ✅ DO THIS - No threading, all in main loop
def long_running_execution_command(params):
    while True:
        try:
            demisto.info('Checking...')  # ✅ Works from main thread!
            do_work()
            time.sleep(60)
        except Exception as e:
            demisto.error(f'Error: {e}')
```

---

### ❌ MISTAKE #2: Using demisto.executeCommand()

**DON'T DO THIS (WILL FAIL):**
```python
def send_alert_email(subject, body):
    # ❌ executeCommand ONLY works in SCRIPTS, NOT integrations!
    demisto.executeCommand('send-mail', {
        'to': 'admin@company.com',
        'subject': subject,
        'body': body
    })
```

**ERROR YOU'LL GET:**
```
Error: executeCommand is not available in integrations
```

**THE FIX - Option 1: Create Incidents (Recommended)**
```python
def send_alert(message):
    # ✅ Create incident that can trigger playbooks for email
    demisto.createIncidents([{
        'name': f'Alert: {message}',
        'type': 'Monitoring Alert',
        'severity': 3,  # High
        'details': message,
        'occurred': datetime.now().isoformat()
    }])
```

**THE FIX - Option 2: Just Log**
```python
def send_alert(message):
    # ✅ Log to XSOAR server logs (visible in UI)
    demisto.info(f'ALERT: {message}')
```

---

### ❌ MISTAKE #3: Exiting the Loop

**DON'T DO THIS:**
```python
def long_running_execution_command(params):
    while True:
        try:
            result = check_service()
            if not result:
                return_error('Service down!')  # ❌ Container exits!

        except Exception as e:
            raise e  # ❌ Container exits!
```

**THE FIX:**
```python
def long_running_execution_command(params):
    while True:
        try:
            result = check_service()
            if not result:
                demisto.error('Service down!')  # ✅ Log and continue
                demisto.createIncidents([{...}])  # Create incident

        except Exception as e:
            demisto.error(f'Error: {e}')  # ✅ Log and continue
            # NEVER exit!

        time.sleep(60)
```

---

### ❌ MISTAKE #4: Using Global State Without Persistence

**DON'T DO THIS:**
```python
# ❌ Global state - lost on container restart
STATE = {
    'last_check': None,
    'total_checks': 0
}

def long_running_execution_command(params):
    global STATE
    while True:
        STATE['total_checks'] += 1  # ❌ Lost if container restarts!
```

**THE FIX:**
```python
def long_running_execution_command(params):
    while True:
        # ✅ Load state from integration context (persists!)
        ctx = demisto.getIntegrationContext()
        total_checks = int(ctx.get('total_checks', '0'))

        # Do work
        total_checks += 1

        # ✅ Save state (survives container restarts)
        ctx = {
            'total_checks': str(total_checks),  # Must be strings!
            'last_check': datetime.now().isoformat()
        }
        demisto.setIntegrationContext(ctx)

        time.sleep(60)
```

---

## Complete Working Example: PingMonitor

```python
'''PingMonitor - Long-Running Integration Example'''

import subprocess
import time
from datetime import datetime
from typing import Dict, Any
import demistomock as demisto
from CommonServerPython import *

def ping_host(ip_address: str) -> Dict[str, Any]:
    '''Ping a host and return results.'''
    import platform
    is_windows = platform.system().lower() == 'windows'

    cmd = ['ping', '-n' if is_windows else '-c', '1', ip_address]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        success = process.returncode == 0
        return {'success': success, 'error': None if success else 'Host unreachable'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def start_monitor_command(args: dict, params: dict) -> CommandResults:
    '''Configure monitoring - saves to context.'''
    host_ip = args.get('host_ip') or params.get('host_ip')
    if not host_ip:
        raise ValueError('Host IP required')

    ctx = demisto.getIntegrationContext()
    ctx['host_ip'] = host_ip
    ctx['running'] = 'true'
    demisto.setIntegrationContext(ctx)

    return CommandResults(
        readable_output=f'Monitoring configured for {host_ip}'
    )


def status_command() -> CommandResults:
    '''Get status from integration context.'''
    ctx = demisto.getIntegrationContext()

    if ctx.get('running') != 'true':
        return CommandResults(readable_output='Monitor not running')

    outputs = {
        'HostIP': ctx.get('host_ip'),
        'TotalChecks': int(ctx.get('total_checks', '0')),
        'Status': ctx.get('status', 'unknown')
    }

    return CommandResults(
        outputs_prefix='PingMonitor',
        outputs=outputs,
        readable_output=f"Host: {outputs['HostIP']}, Checks: {outputs['TotalChecks']}"
    )


def long_running_execution_command(params: dict):
    '''
    Main entry point - runs FOREVER in main thread.
    NO BACKGROUND THREADS!
    '''
    # Initialize
    host_ip = params.get('host_ip')
    interval = int(params.get('ping_interval', 60))

    ctx = demisto.getIntegrationContext()
    if not ctx.get('host_ip'):
        ctx = {
            'host_ip': host_ip,
            'running': 'true',
            'total_checks': '0',
            'status': 'unknown'
        }
        demisto.setIntegrationContext(ctx)

    demisto.info(f'Starting ping monitor for {host_ip}')

    last_state = None

    # NEVER-ENDING LOOP - All logic here in MAIN THREAD
    while True:
        try:
            # Check if paused
            ctx = demisto.getIntegrationContext()
            if ctx.get('running') != 'true':
                demisto.info('Monitoring paused')
                time.sleep(10)
                continue

            # Do the actual work
            result = ping_host(host_ip)
            current_state = result['success']

            # Parse state
            total_checks = int(ctx.get('total_checks', '0'))
            total_checks += 1

            # Detect state changes
            if last_state is not None and last_state != current_state:
                state_str = 'UP' if current_state else 'DOWN'
                demisto.info(f'Host {host_ip} changed to {state_str}')

                # Create incident on state change
                demisto.createIncidents([{
                    'name': f'Host {host_ip} is {state_str}',
                    'type': 'Host Monitoring',
                    'severity': 1 if current_state else 3,
                    'details': f'Status: {state_str}\\nTime: {datetime.now()}'
                }])

            last_state = current_state

            # Save state (persists across container restarts!)
            ctx = {
                'host_ip': host_ip,
                'running': 'true',
                'total_checks': str(total_checks),
                'status': 'up' if current_state else 'down'
            }
            demisto.setIntegrationContext(ctx)

        except Exception as e:
            demisto.error(f'Error: {e}')
            # NEVER exit! Just log and continue

        time.sleep(interval)


def main():
    '''Main execution function.'''
    try:
        command = demisto.command()

        if command == 'long-running-execution':
            long_running_execution_command(demisto.params())
        elif command == 'ping-monitor-start':
            return_results(start_monitor_command(demisto.args(), demisto.params()))
        elif command == 'ping-monitor-status':
            return_results(status_command())
        elif command == 'test-module':
            return_results('ok')

    except Exception as e:
        return_error(f'Failed: {e}')

if __name__ in ['__main__', 'builtin', 'builtins']:
    main()
```

---

## State Management with Integration Context

**Integration context stores state that PERSISTS across container restarts.**

### API Reference

```python
# Get current state
ctx = demisto.getIntegrationContext()
# Returns: {'key': 'value', ...}  # All values are STRINGS

# Save state
ctx = {
    'last_check': datetime.now().isoformat(),  # ✅ String
    'total_checks': '42',  # ✅ String, not int!
    'is_running': 'true'  # ✅ String, not boolean!
}
demisto.setIntegrationContext(ctx)
```

**CRITICAL RULE:** All values MUST be strings. Convert numbers/booleans before saving.

```python
# ❌ WRONG
ctx = {'count': 42, 'active': True}  # Will cause errors!

# ✅ CORRECT
ctx = {'count': '42', 'active': 'true'}  # All strings
```

---

## Testing Checklist

✅ **Before Upload:**
1. No `import threading` for main logic
2. No background threads in long_running_execution
3. No `demisto.executeCommand()` calls
4. No `return_error()` or `sys.exit()` in while loop
5. Integration context values are all strings

✅ **After Upload:**
1. Enable "Long running instance" checkbox in XSIAM UI
2. Check container status (should be "Running")
3. Run status command, verify state updates
4. Check server logs for startup messages
5. Verify state persists after container restart

---

## Summary: Quick Checklist

✅ **Required:**
- `longRunning: true` in YAML
- `while True` in `long_running_execution_command()`
- All logic in MAIN THREAD
- Use `demisto.setIntegrationContext()` for state
- Catch all exceptions, never exit

❌ **Forbidden:**
- Background threads for main work
- `demisto.executeCommand()`
- `return_error()` or `sys.exit()` in loop
- Global state without persistence
- Non-string values in integration context
"""

# ============================================================================
# EVENT COLLECTOR GUIDE
# ============================================================================

EVENT_COLLECTOR_GUIDE = """
# XSOAR Event Collector Integration Complete Guide

## Pattern Overview

Event Collector integrations periodically fetch data from external sources (ServiceNow, Jira, Splunk, etc.) and send it to XSIAM for ingestion and analysis.

---

## Architecture Pattern

```python
def fetch_incidents_command(params: dict):
    '''
    Called by XSOAR scheduler to fetch new data periodically.
    Frequency configured in integration settings.
    '''

    # Get last run info
    last_run = demisto.getLastRun()
    last_fetch_time = last_run.get('last_fetch')
    last_id = last_run.get('last_id', 0)

    # Fetch new data from external source
    incidents = fetch_from_external_api(
        since=last_fetch_time,
        after_id=last_id
    )

    # Send to XSIAM
    from CommonServerPython import send_events_to_xsiam
    send_events_to_xsiam(
        incidents,
        vendor='YourCompany',
        product='YourProduct'
    )

    # Update last run
    demisto.setLastRun({
        'last_fetch': datetime.now().isoformat(),
        'last_id': incidents[-1]['id'] if incidents else last_id
    })
```

---

## YAML Configuration

```yaml
commonfields:
  id: ServiceNowEventCollector
  version: -1
name: ServiceNow Event Collector
category: Analytics & SIEM
description: Fetches incidents from ServiceNow and sends to XSIAM

configuration:
  - display: ServiceNow URL
    name: url
    type: 0
    required: true

  - display: Fetch incidents
    name: isFetch
    type: 8
    required: false

  - display: Incident type
    name: incidentType
    type: 13
    required: false

  - display: First fetch time
    name: first_fetch
    defaultvalue: '3 days'
    type: 0
    required: false

script:
  type: python
  subtype: python3
  dockerimage: demisto/python3:3.10.14.100715
  isfetch: true         # ← REQUIRED for fetch
  isFetchEvents: true   # ← REQUIRED for event collectors
```

---

## Complete Working Example: ServiceNow Event Collector

```python
'''ServiceNow Event Collector Integration'''

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import demistomock as demisto
from CommonServerPython import *

class ServiceNowClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.auth = (username, password)
        self.headers = {'Content-Type': 'application/json'}

    def get_incidents(self, since: str = None, limit: int = 50) -> List[Dict]:
        '''Fetch incidents from ServiceNow.'''
        endpoint = f'{self.url}/api/now/table/incident'

        params = {
            'sysparm_limit': limit,
            'sysparm_display_value': 'true'
        }

        if since:
            params['sysparm_query'] = f'sys_created_on>{since}'

        response = requests.get(
            endpoint,
            params=params,
            headers=self.headers,
            auth=self.auth,
            timeout=30
        )
        response.raise_for_status()

        return response.json().get('result', [])


def fetch_incidents_command(client: ServiceNowClient, params: dict):
    '''
    Main fetch function - called by XSOAR scheduler.
    '''
    # Get last run
    last_run = demisto.getLastRun()
    last_fetch_time = last_run.get('last_fetch')

    # Use first_fetch if no last run
    if not last_fetch_time:
        first_fetch = params.get('first_fetch', '3 days')
        last_fetch_time = (datetime.now() - timedelta(days=3)).isoformat()

    demisto.info(f'Fetching ServiceNow incidents since {last_fetch_time}')

    try:
        # Fetch incidents from ServiceNow
        incidents = client.get_incidents(since=last_fetch_time)

        if not incidents:
            demisto.info('No new incidents to fetch')
            return

        demisto.info(f'Fetched {len(incidents)} incidents from ServiceNow')

        # Transform to XSIAM format
        events = []
        for inc in incidents:
            events.append({
                '_time': inc.get('sys_created_on'),
                'event_type': 'ServiceNow Incident',
                'severity': inc.get('severity', 'Low'),
                'description': inc.get('short_description'),
                'number': inc.get('number'),
                'state': inc.get('state'),
                'assigned_to': inc.get('assigned_to'),
                'category': inc.get('category'),
                'priority': inc.get('priority'),
                'raw_data': inc  # Include full incident
            })

        # Send to XSIAM
        send_events_to_xsiam(
            events,
            vendor='ServiceNow',
            product='ITSM'
        )

        # Update last run
        demisto.setLastRun({
            'last_fetch': incidents[-1].get('sys_created_on'),
            'last_id': incidents[-1].get('sys_id')
        })

        demisto.info(f'Successfully sent {len(events)} events to XSIAM')

    except Exception as e:
        demisto.error(f'Error fetching incidents: {e}')
        raise


def test_module_command(client: ServiceNowClient) -> str:
    '''Test connectivity.'''
    try:
        incidents = client.get_incidents(limit=1)
        return 'ok'
    except Exception as e:
        return f'Test failed: {str(e)}'


def main():
    params = demisto.params()

    client = ServiceNowClient(
        url=params.get('url'),
        username=params.get('credentials', {}).get('identifier'),
        password=params.get('credentials', {}).get('password')
    )

    command = demisto.command()

    if command == 'test-module':
        return_results(test_module_command(client))
    elif command == 'fetch-incidents':
        fetch_incidents_command(client, params)
    else:
        raise NotImplementedError(f'Command {command} not implemented')

if __name__ in ['__main__', 'builtin', 'builtins']:
    main()
```

---

## Key Components Explained

### 1. send_events_to_xsiam()

```python
from CommonServerPython import send_events_to_xsiam

events = [
    {
        '_time': '2025-01-15T10:30:00Z',  # Event timestamp
        'event_type': 'MyEvent',
        'field1': 'value1',
        # ... your event fields
    }
]

send_events_to_xsiam(
    events,
    vendor='YourCompany',    # Your organization name
    product='YourProduct'     # Product/service name
)
```

### 2. Last Run Management

```python
# Get last run
last_run = demisto.getLastRun()
# Returns: {'last_fetch': '2025-01-15T10:00:00', ...}

# Set last run
demisto.setLastRun({
    'last_fetch': datetime.now().isoformat(),
    'last_id': 12345
})
```

### 3. Deduplication

```python
# Track seen IDs to avoid duplicates
last_run = demisto.getLastRun()
seen_ids = set(last_run.get('seen_ids', []))

new_events = [e for e in all_events if e['id'] not in seen_ids]

# Update seen IDs (keep only recent)
recent_ids = [e['id'] for e in new_events[-1000:]]  # Keep last 1000
demisto.setLastRun({
    'last_fetch': datetime.now().isoformat(),
    'seen_ids': recent_ids
})
```

### 4. Pagination

```python
def fetch_all_incidents(client, since):
    all_incidents = []
    offset = 0
    limit = 100

    while True:
        batch = client.get_incidents(since=since, offset=offset, limit=limit)
        if not batch:
            break

        all_incidents.extend(batch)
        offset += limit

        if len(batch) < limit:
            break  # Last page

    return all_incidents
```

---

## Summary: Event Collector Checklist

✅ **Required:**
- `isfetch: true` and `isFetchEvents: true` in YAML
- Implement `fetch-incidents` command
- Use `send_events_to_xsiam()` to send data
- Use `demisto.getLastRun()` / `demisto.setLastRun()`
- Handle pagination for large datasets
- Implement deduplication

✅ **Best Practices:**
- Transform external format to XSIAM-friendly format
- Include `_time` field in events
- Handle API rate limits
- Log fetch progress with `demisto.info()`
- Handle errors gracefully
"""

# ============================================================================
# BEST PRACTICES GUIDES
# ============================================================================

THREADING_BEST_PRACTICES = """
# XSOAR Threading Best Practices

## ❌ THE RULE: No Background Threads for Main Logic

**From real debugging experience:**

### What Fails
```python
import threading

def long_running_execution_command(params):
    # ❌ Background thread for main work
    thread = threading.Thread(target=worker)
    thread.start()

    while True:
        time.sleep(60)

def worker():
    while True:
        demisto.info('Working...')  # ❌ NameError: SERVER_ERROR_MARKER not defined
```

### What Works
```python
# NO threading import needed!

def long_running_execution_command(params):
    # ✅ All work in main thread
    while True:
        demisto.info('Working...')  # ✅ Works perfectly
        do_work()
        time.sleep(60)
```

## When Threading is Acceptable

✅ **OK for:** HTTP server management (Flask/WSGI)
✅ **OK for:** Short-lived helper threads
❌ **NOT OK for:** Main monitoring/polling logic
❌ **NOT OK for:** Calling demisto functions from threads

## Summary
Run everything in the main thread's `while True` loop. No background threads.
"""

STATE_MANAGEMENT_GUIDE = """
# XSOAR State Management Guide

## Integration Context: Persistent State

**Use for:** Data that must survive container restarts

```python
# Save
ctx = {
    'count': '42',  # Must be string!
    'timestamp': datetime.now().isoformat()
}
demisto.setIntegrationContext(ctx)

# Load
ctx = demisto.getIntegrationContext()
count = int(ctx.get('count', '0'))  # Convert back to int
```

## Last Run: Fetch Tracking

**Use for:** Track last fetch time in event collectors

```python
# Save
demisto.setLastRun({
    'last_fetch': datetime.now().isoformat(),
    'last_id': 12345
})

# Load
last_run = demisto.getLastRun()
last_fetch = last_run.get('last_fetch')
```

## In-Memory State: Temporary Data

**Use for:** Temporary data within single execution

```python
# Local variables in functions - OK for temporary state
last_state = None

while True:
    current_state = check()
    if last_state != current_state:
        # Detected change
        pass
    last_state = current_state  # ✅ OK - resets on restart
```

## Summary
- **Persist across restarts:** integration context
- **Track fetching:** last run
- **Temporary:** local variables
"""

# ============================================================================
# SCHEDULED COMMANDS GUIDE (Polling Pattern)
# ============================================================================

SCHEDULED_COMMANDS_GUIDE = """
# XSOAR Scheduled Commands (Polling Pattern)

## Pattern Overview

Scheduled commands enable **asynchronous polling** for operations that cannot return results immediately.

**Use cases:**
- Sandbox file analysis (submit file → poll for results)
- Long-running searches (start search → check status → get results)
- External async operations requiring status checks

**Official PANW Term:** "Scheduled Commands"
**YAML Config:** `polling: true`

---

## Architecture Pattern

### Simple Implementation (polling_function decorator)

```python
from CommonServerPython import ScheduledCommand

@polling_function(
    name='file-scan',
    interval=30,  # Poll every 30 seconds
    timeout=600   # Give up after 10 minutes
)
def scan_file_command(args):
    '''Submit file for scanning and poll for results.'''

    file_hash = args.get('file_hash')

    # First call: Submit for analysis
    if not args.get('_hide_polling_output'):
        result = submit_file_to_sandbox(file_hash)
        return PollResult(
            response=None,  # No results yet
            continue_to_poll=True,
            args_for_next_run={'scan_id': result['scan_id']}
        )

    # Subsequent calls: Poll for results
    scan_id = args.get('scan_id')
    status = check_scan_status(scan_id)

    if status['completed']:
        # Analysis complete - return results
        return PollResult(
            response=CommandResults(
                outputs_prefix='FileScan',
                outputs=status['results']
            ),
            continue_to_poll=False
        )
    else:
        # Still processing - keep polling
        return PollResult(
            response=None,
            continue_to_poll=True
        )
```

### YAML Configuration

```yaml
script:
  polling: true  # Enable scheduled commands

commands:
  - name: file-scan
    description: Scan file in sandbox (async with polling)
    polling: true  # This specific command uses polling
    arguments:
      - name: file_hash
        description: File hash to scan
        required: true
```

---

## Key Components

### PollResult Object

```python
from CommonServerPython import PollResult

PollResult(
    response=CommandResults(...),  # Results to return (or None if not ready)
    continue_to_poll=True/False,   # Keep polling or stop?
    args_for_next_run={'key': 'value'}  # Args to pass to next poll
)
```

### Polling Behavior

1. **First execution:** Command submitted via War Room
2. **Polling starts:** XSOAR calls command repeatedly at `interval`
3. **Continue polling:** Until `continue_to_poll=False` or `timeout` reached
4. **Results returned:** When operation completes

---

## Complete Example: VirusTotal File Scan

```python
from CommonServerPython import *

@polling_function(
    name='vt-scan-file',
    interval=30,
    timeout=600,
    requires_polling_arg=False
)
def scan_file_command(args, client):
    file_hash = args.get('file_hash')

    # First call - submit file
    if not args.get('scan_id'):
        demisto.info(f'Submitting {file_hash} for analysis')
        result = client.submit_file(file_hash)

        return PollResult(
            response=CommandResults(
                readable_output=f'File submitted for analysis. Scan ID: {result["scan_id"]}'
            ),
            continue_to_poll=True,
            args_for_next_run={'scan_id': result['scan_id']}
        )

    # Polling - check status
    scan_id = args.get('scan_id')
    status = client.get_scan_status(scan_id)

    if status['status'] == 'completed':
        demisto.info(f'Scan {scan_id} completed')
        return PollResult(
            response=CommandResults(
                outputs_prefix='VirusTotal.Scan',
                outputs=status['results'],
                readable_output=f"Scan complete. Verdict: {status['results']['verdict']}"
            ),
            continue_to_poll=False
        )

    elif status['status'] == 'error':
        raise DemistoException(f"Scan failed: {status['error']}")

    else:
        # Still in progress
        demisto.debug(f'Scan {scan_id} still in progress')
        return PollResult(
            response=None,
            continue_to_poll=True
        )
```

---

## Summary: Scheduled Commands Checklist

✅ **Required:**
- `polling: true` in YAML
- `@polling_function` decorator or manual ScheduledCommand implementation
- Return `PollResult` objects
- Handle first call vs subsequent polls differently

✅ **Best Practices:**
- Set reasonable `interval` (minimum 10 seconds)
- Set appropriate `timeout` based on operation
- Pass operation ID via `args_for_next_run`
- Log polling status with `demisto.debug()`

**When to use:** Operations that can't complete immediately (sandbox analysis, long searches, async external operations)
"""

# ============================================================================
# MIRRORING INTEGRATION GUIDE
# ============================================================================

MIRRORING_GUIDE = """
# XSOAR Mirroring Integration Pattern

## Pattern Overview

Mirroring integrations enable **bidirectional synchronization** between XSOAR incidents and external systems (ServiceNow, Jira, ticketing systems, chat platforms).

**Official PANW Term:** "Mirroring Integration"
**YAML Config:** `ismappable: true`

**Use cases:**
- ServiceNow incident sync
- Jira issue sync
- Slack/Teams chat-based incident management
- Any bidirectional incident sync requirement

---

## Required Commands

### 1. get-remote-data
**Purpose:** Pull updates from external system to XSOAR

**Called:** Every 1 minute per mirrored incident

```python
def get_remote_data_command(client, args):
    '''
    Pulls updates from remote system for a specific incident.

    Args:
        id: Remote incident ID (from dbotMirrorId)
        lastUpdate: Last update timestamp
    '''
    remote_id = args.get('id')
    last_update = args.get('lastUpdate')

    # Fetch updates from external system
    remote_incident = client.get_incident(remote_id, since=last_update)

    # Transform to XSOAR format
    entries = []
    for comment in remote_incident.get('comments', []):
        entries.append({
            'Type': EntryType.NOTE,
            'Contents': comment['text'],
            'Note': True
        })

    return GetRemoteDataResponse(
        mirrored_object=remote_incident,  # Full incident data
        entries=entries  # New comments/notes to add
    )
```

### 2. update-remote-system
**Purpose:** Push XSOAR changes to external system

**Called:** When XSOAR incident is modified

```python
def update_remote_system_command(client, args):
    '''
    Pushes XSOAR incident changes to remote system.

    Args:
        data: Modified incident data
        entries: New entries (comments, notes)
        incidentChanged: True if incident fields changed
        remoteId: External system incident ID
    '''
    remote_id = args.get('remoteId')
    data = args.get('data')
    entries = args.get('entries', [])

    # Update incident fields if changed
    if args.get('incidentChanged'):
        client.update_incident(remote_id, {
            'status': data.get('status'),
            'severity': data.get('severity')
        })

    # Add new comments
    for entry in entries:
        if entry['Type'] == EntryType.NOTE:
            client.add_comment(remote_id, entry['Contents'])

    return remote_id
```

### 3. get-modified-remote-data
**Purpose:** Optimization - only check incidents modified since last check

```python
def get_modified_remote_data_command(client, args):
    '''
    Returns IDs of incidents modified since last check.
    Reduces API calls by only polling changed incidents.
    '''
    last_update = args.get('lastUpdate')

    # Query only modified incidents
    modified_ids = client.get_modified_incident_ids(since=last_update)

    return GetModifiedRemoteDataResponse(modified_incident_ids=modified_ids)
```

### 4. get-mapping-fields
**Purpose:** Retrieve remote system schema for field mapping

```python
def get_mapping_fields_command(client):
    '''
    Returns schema of remote system for field mapping in XSOAR.
    '''
    # Get schema from remote system
    schema = client.get_schema()

    return GetMappingFieldsResponse(schema)
```

---

## Required Incident Fields

Mirrored incidents must have these fields:

```python
# In incident data
{
    'dbotMirrorDirection': 'Both',  # 'In', 'Out', or 'Both'
    'dbotMirrorId': 'INC0012345',   # Remote system ID
    'dbotMirrorInstance': 'ServiceNow_Instance_1',  # Integration instance name
    'dbotMirrorTags': ['tag1', 'tag2']  # Tags to mirror
}
```

---

## YAML Configuration

```yaml
commonfields:
  id: ServiceNowMirror
  version: -1
name: ServiceNow Mirroring
category: Case Management
description: Bidirectional sync with ServiceNow

script:
  ismappable: true  # Enable mirroring
  isfetch: true     # Also fetch incidents

commands:
  - name: get-remote-data
    description: Get updates from ServiceNow
  - name: update-remote-system
    description: Push changes to ServiceNow
  - name: get-modified-remote-data
    description: Get list of modified incidents
  - name: get-mapping-fields
    description: Get ServiceNow schema
```

---

## Summary: Mirroring Checklist

✅ **Required:**
- `ismappable: true` in YAML
- Implement all 4 commands (get-remote-data, update-remote-system, get-modified-remote-data, get-mapping-fields)
- Set dbotMirrorId, dbotMirrorDirection, dbotMirrorInstance in incidents
- Handle incremental updates (only sync what changed)

**When to use:** Bidirectional sync with ServiceNow, Jira, chat platforms, any external incident tracking system
"""

# ============================================================================
# FEED INTEGRATION GUIDE
# ============================================================================

FEED_GUIDE = """
# XSOAR Feed Integration Pattern

## Pattern Overview

Feed integrations ingest **threat intelligence indicators** (IOCs) from external sources and make them available in XSOAR/XSIAM for threat detection.

**Official PANW Term:** "Feed Integration"
**YAML Config:** `isFeed: true`

**Use cases:**
- TAXII threat feeds
- STIX indicator feeds
- Custom IOC sources (APIs, RSS, CSV files)
- Threat intelligence vendor feeds

---

## Naming Convention

**CRITICAL:** Integration name MUST end with "Feed"

✅ **Correct:** ThreatStreamFeed, AlienVaultFeed, CustomIOCFeed
❌ **Wrong:** ThreatStream, AlienVault, CustomIOC

---

## Required Parameters (6 core + 1 optional)

```yaml
configuration:
  - display: Fetch indicators
    name: feed
    type: 8
    required: false

  - display: Indicator Reputation
    name: feedReputation
    type: 18
    required: false
    defaultvalue: 'None'
    options: ['None', 'Good', 'Suspicious', 'Bad']

  - display: Source Reliability
    name: feedReliability
    type: 15
    required: true
    defaultvalue: 'F - Reliability cannot be judged'
    options: ['A+ - Completely reliable', 'A - Reliable', 'B - Usually reliable', ...]

  - display: Expiration Policy
    name: feedExpirationPolicy
    type: 17
    required: false

  - display: Expiration Interval (minutes)
    name: feedExpirationInterval
    type: 1
    required: false
    defaultvalue: '20160'  # 14 days

  - display: Feed Fetch Interval (minutes)
    name: feedFetchInterval
    type: 19
    required: false
    defaultvalue: '240'  # 4 hours

  - display: Bypass exclusion list
    name: feedBypassExclusionList
    type: 8
    required: false
```

---

## Architecture Pattern

```python
def fetch_indicators_command(client, params):
    '''
    Main fetch function for feed integrations.
    Called by XSOAR scheduler based on feedFetchInterval.
    '''
    # Get feed configuration
    feed_tags = ['MyFeed', 'ThreatIntel']
    tlp_color = params.get('tlp_color')

    # Fetch indicators from external source
    indicators = client.get_indicators()

    # Transform to XSOAR indicator format
    formatted_indicators = []
    for ioc in indicators:
        formatted_indicators.append({
            'value': ioc['indicator'],
            'type': ioc['type'],  # ip, domain, file, url, etc.
            'rawJSON': ioc,
            'fields': {
                'tags': feed_tags,
                'trafficlightprotocol': tlp_color,
                'threattypes': ioc.get('threat_types', [])
            }
        })

    # Create indicators in batches (~2000 per batch)
    for i in range(0, len(formatted_indicators), 2000):
        batch = formatted_indicators[i:i+2000]
        demisto.createIndicators(batch)

    demisto.info(f'Created {len(formatted_indicators)} indicators')
```

### Manual Fetch Command

Provide a manual fetch command for testing:

```python
def get_indicators_command(client, args):
    '''
    Manual command to fetch and return indicators.
    For testing and ad-hoc fetching.
    '''
    limit = int(args.get('limit', 10))

    indicators = client.get_indicators(limit=limit)

    return CommandResults(
        outputs_prefix='ThreatFeed.Indicator',
        outputs=indicators,
        readable_output=tableToMarkdown('Indicators', indicators)
    )
```

---

## YAML Configuration

```yaml
commonfields:
  id: ThreatStreamFeed
  version: -1
name: ThreatStream Feed
category: Data Enrichment & Threat Intelligence
description: Threat intelligence indicator feed

script:
  type: python
  subtype: python3
  dockerimage: demisto/python3:3.10.14.100715
  feed: true       # ← Enable feed
  isFeed: true     # ← Enable feed (alternative)

commands:
  - name: threatstream-get-indicators
    description: Fetch indicators manually (for testing)
```

---

## Incremental Feeds

For feeds that support incremental updates:

```yaml
configuration:
  - display: Incremental Feed
    name: feedIncremental
    type: 8
    defaultvalue: 'true'
```

```python
def fetch_indicators_command(client, params):
    last_run = demisto.getLastRun()
    last_fetch = last_run.get('last_fetch')

    # Fetch only new indicators since last fetch
    indicators = client.get_indicators(since=last_fetch)

    # Update last run
    demisto.setLastRun({'last_fetch': datetime.now().isoformat()})
```

---

## Summary: Feed Integration Checklist

✅ **Required:**
- Name ends with "Feed"
- `isFeed: true` in YAML
- 6 required parameters (reputation, reliability, expiration, etc.)
- Implement `fetch-indicators` command
- Use `demisto.createIndicators()` with batching (~2000 per batch)
- Provide manual `[vendor]-get-indicators` command

✅ **Best Practices:**
- Batch indicators to avoid memory issues
- Support incremental feeds when possible
- Set appropriate fetch interval (default: 240 min)
- Use standard reliability ratings (A-F)

**When to use:** Ingesting threat intelligence indicators from TAXII, STIX, or custom feeds
"""

# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

async def get_xsoar_pattern_guide(ctx: Context) -> str:
    """
    Get guide for recognizing which XSOAR integration pattern to use.

    **CALL THIS TOOL FIRST** before creating any XSOAR integration!

    This tool teaches you how to automatically identify the correct integration
    pattern based on the user's request, without them needing to specify
    "long-running" or "event collector".

    Recognition keywords:
    - "monitor", "continuously", "every X seconds" → Long-Running Integration
    - "fetch", "pull", "import", "send to XSIAM" → Event Collector Integration
    - "query", "get", "lookup" (one-time) → Regular Integration

    Returns complete guide with:
    - Pattern recognition decision tree
    - Keywords to look for in user requests
    - Which guide to call for each pattern
    - Quick reference for all three patterns
    """
    return PATTERN_RECOGNITION_GUIDE


async def get_xsoar_long_running_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for implementing XSOAR long-running integrations.

    Use this tool when user requests:
    - Monitoring integrations (ping monitors, service health checks)
    - Webhook receivers (Slack, Teams, generic webhooks)
    - Polling integrations (checking APIs on intervals)
    - Any integration that runs continuously

    Based on real debugging experience fixing PingMonitor integration.

    Covers:
    - Complete architecture pattern (while True in main thread)
    - ❌ Critical mistakes: background threading, executeCommand, exiting loop
    - State management with integration context
    - Creating incidents for alerts
    - Complete working example (PingMonitor)
    - Testing checklist

    Returns: Complete markdown guide with working code examples
    """
    return LONG_RUNNING_GUIDE


async def get_xsoar_event_collector_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for implementing XSOAR event collector integrations.

    Use this tool when user requests:
    - Fetching data from external sources (ServiceNow, Jira, Splunk)
    - Importing logs/events into XSIAM
    - Pulling tickets/alerts periodically
    - Collecting data from APIs and sending to XSIAM

    Covers:
    - fetch-incidents command pattern
    - send_events_to_xsiam() usage
    - Last run tracking (demisto.getLastRun/setLastRun)
    - Pagination for large datasets
    - Deduplication strategies
    - Complete working example (ServiceNow)

    Returns: Complete markdown guide with working code examples
    """
    return EVENT_COLLECTOR_GUIDE


async def get_xsoar_best_practices(
    ctx: Context,
    topic: Annotated[str, Field(description="Best practices topic: 'threading', 'state', or 'all'")] = "all"
) -> str:
    """
    Get XSOAR integration development best practices for specific topics.

    Use this tool to:
    - Check specific patterns when unsure
    - Fix issues (e.g., threading errors)
    - Learn state management
    - Understand error handling

    Args:
        topic: Specific topic or "all". Options:
            - "all": All best practices (default)
            - "threading": Threading patterns (why background threads fail)
            - "state": State management (integration context vs in-memory)

    Returns: Best practices guide for the specified topic
    """
    practices = {
        "threading": THREADING_BEST_PRACTICES,
        "state": STATE_MANAGEMENT_GUIDE
    }

    if topic == "all":
        return "\n\n---\n\n".join(practices.values())

    if topic in practices:
        return practices[topic]

    return f"Unknown topic '{topic}'. Available: {', '.join(practices.keys())}, all"


async def get_xsoar_scheduled_commands_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for implementing XSOAR scheduled commands (polling pattern).

    Use this tool when user requests:
    - Sandbox file analysis (submit → poll → get results)
    - Long-running searches that require status checking
    - Async external operations (detonation, scanning, analysis)
    - Any operation that can't return results immediately

    Covers:
    - polling: true configuration
    - @polling_function decorator usage
    - PollResult object and args_for_next_run
    - Complete working example (VirusTotal file scan)
    - Polling intervals and timeouts

    Returns: Complete markdown guide with working code examples
    """
    return SCHEDULED_COMMANDS_GUIDE


async def get_xsoar_mirroring_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for implementing XSOAR mirroring integrations.

    Use this tool when user requests:
    - Bidirectional sync with ServiceNow, Jira, ticketing systems
    - Chat-based incident management (Slack, Teams)
    - Two-way incident synchronization
    - Mirror incidents between XSOAR and external systems

    Covers:
    - ismappable: true configuration
    - Required commands: get-remote-data, update-remote-system, get-modified-remote-data, get-mapping-fields
    - dbotMirror fields (direction, id, instance, tags)
    - Complete implementation patterns
    - Optimization with get-modified-remote-data

    Returns: Complete markdown guide with working code examples
    """
    return MIRRORING_GUIDE


async def get_xsoar_feed_guide(ctx: Context) -> str:
    """
    Get comprehensive guide for implementing XSOAR feed integrations.

    Use this tool when user requests:
    - Threat intelligence feed ingestion
    - TAXII or STIX feed integration
    - Custom IOC sources (APIs, RSS, CSV files)
    - Indicator collection from threat intelligence vendors

    Covers:
    - isFeed: true configuration
    - Naming convention (must end with "Feed")
    - 6 required feed parameters (reputation, reliability, expiration, etc.)
    - fetch-indicators command pattern
    - demisto.createIndicators() with batching (~2000 per batch)
    - Incremental feed support

    Returns: Complete markdown guide with working code examples
    """
    return FEED_GUIDE


# ============================================================================
# MODULE REGISTRATION
# ============================================================================

class XSOARDevGuidesModule(BaseModule):
    """
    XSOAR Development Guides Module

    Provides comprehensive development guides for XSOAR integrations as callable
    MCP tools. Guides are based on real debugging experience and official PANW
    documentation.

    Tools provided:
        - get_xsoar_pattern_guide: Pattern recognition (call first!)
        - get_xsoar_long_running_guide: Long-running integrations guide
        - get_xsoar_event_collector_guide: Event collector integrations guide
        - get_xsoar_scheduled_commands_guide: Polling pattern for async operations
        - get_xsoar_mirroring_guide: Bidirectional sync pattern
        - get_xsoar_feed_guide: Threat intelligence feed pattern
        - get_xsoar_best_practices: Topic-specific best practices
    """

    def register_tools(self):
        self._add_tool(get_xsoar_pattern_guide)
        self._add_tool(get_xsoar_long_running_guide)
        self._add_tool(get_xsoar_event_collector_guide)
        self._add_tool(get_xsoar_scheduled_commands_guide)
        self._add_tool(get_xsoar_mirroring_guide)
        self._add_tool(get_xsoar_feed_guide)
        self._add_tool(get_xsoar_best_practices)

    def register_resources(self):
        pass

    def __init__(self, mcp: FastMCP):
        super().__init__(mcp)
