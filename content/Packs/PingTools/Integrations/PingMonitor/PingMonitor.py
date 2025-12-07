"""
PingMonitor Integration

A long-running XSOAR integration that continuously monitors a host via ping,
tracks uptime/downtime statistics, and logs state changes.
"""

import subprocess
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *


def ping_host(ip_address: str, count: int = 1) -> Dict[str, Any]:
    """
    Ping a host and return basic statistics.

    Args:
        ip_address: IP address to ping
        count: Number of ping packets to send

    Returns:
        Dictionary with ping results
    """
    import platform
    is_windows = platform.system().lower() == 'windows'

    if is_windows:
        cmd = ['ping', '-n', str(count), ip_address]
    else:
        cmd = ['ping', '-c', str(count), '-W', '5', ip_address]

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        output = process.stdout + process.stderr
        success = process.returncode == 0 and ('bytes from' in output.lower() or 'reply from' in output.lower())

        # Extract latency if available
        latency = None
        if success:
            if is_windows:
                match = re.search(r'Average\s*=\s*(\d+)ms', output)
                if match:
                    latency = float(match.group(1))
            else:
                match = re.search(r'time=([\d.]+)\s*ms', output)
                if match:
                    latency = float(match.group(1))

        return {
            'success': success,
            'latency': latency,
            'error': None if success else 'Host unreachable'
        }

    except subprocess.TimeoutExpired:
        return {'success': False, 'latency': None, 'error': 'Ping timeout'}
    except Exception as e:
        return {'success': False, 'latency': None, 'error': str(e)}


def start_monitor_command(args: dict, params: dict) -> CommandResults:
    """
    Configure monitoring settings - actual monitoring runs in long_running_execution.

    Args:
        args: Command arguments
        params: Integration parameters

    Returns:
        CommandResults
    """
    host_ip = args.get('host_ip') or params.get('host_ip')

    if not host_ip:
        raise ValueError('Host IP address is required')

    # Save configuration to integration context
    ctx = demisto.getIntegrationContext()
    ctx['host_ip'] = host_ip
    ctx['running'] = 'true'
    ctx['ping_interval'] = str(params.get('ping_interval', 60))
    demisto.setIntegrationContext(ctx)

    return CommandResults(
        readable_output=f'Monitoring configured for {host_ip}. Monitoring runs in long-running integration instance.'
    )


def stop_monitor_command() -> CommandResults:
    """
    Stop the ping monitor by updating context.

    Returns:
        CommandResults
    """
    ctx = demisto.getIntegrationContext()
    ctx['running'] = 'false'
    demisto.setIntegrationContext(ctx)

    return CommandResults(
        readable_output='Ping monitoring stopped'
    )


def status_command() -> CommandResults:
    """
    Get current monitoring status from integration context.

    Returns:
        CommandResults with current statistics
    """
    ctx = demisto.getIntegrationContext()

    if ctx.get('running') != 'true':
        return CommandResults(
            readable_output='Ping monitor is not running'
        )

    # Parse state from context
    outputs = {
        'HostIP': ctx.get('host_ip'),
        'Status': ctx.get('is_up', 'unknown'),
        'Uptime': float(ctx.get('total_uptime', '0')),
        'Downtime': float(ctx.get('total_downtime', '0')),
        'LastCheck': ctx.get('last_check'),
        'LastLatency': float(ctx.get('last_latency', '0')) if ctx.get('last_latency') else None,
        'TotalChecks': int(ctx.get('total_checks', '0')),
        'FailedChecks': int(ctx.get('failed_checks', '0'))
    }

    # Calculate uptime percentage
    total_time = outputs['Uptime'] + outputs['Downtime']
    uptime_pct = (outputs['Uptime'] / total_time * 100) if total_time > 0 else 0

    status_str = 'UP ✓' if outputs['Status'] == 'up' else 'DOWN ✗'

    hr = f'''### Ping Monitor Status

**Host:** {outputs['HostIP']}
**Current Status:** {status_str}

**Statistics:**
- Total Checks: {outputs['TotalChecks']}
- Failed Checks: {outputs['FailedChecks']}
- Success Rate: {((outputs['TotalChecks'] - outputs['FailedChecks']) / outputs['TotalChecks'] * 100) if outputs['TotalChecks'] > 0 else 0:.2f}%

**Uptime Metrics:**
- Total Uptime: {outputs['Uptime']:.2f} seconds ({outputs['Uptime'] / 60:.2f} minutes)
- Total Downtime: {outputs['Downtime']:.2f} seconds ({outputs['Downtime'] / 60:.2f} minutes)
- Uptime Percentage: {uptime_pct:.2f}%

**Latest Check:**
- Last Check Time: {outputs['LastCheck'] or 'N/A'}
- Last Latency: {f'{outputs["LastLatency"]:.2f} ms' if outputs['LastLatency'] else 'N/A'}
'''

    return CommandResults(
        outputs_prefix='PingMonitor',
        outputs_key_field='HostIP',
        outputs=outputs,
        readable_output=hr
    )


def long_running_execution_command(params: dict):
    """
    Main entry point for long-running integration.
    Runs monitoring loop in main thread - NO BACKGROUND THREADS.

    Args:
        params: Integration parameters
    """
    # Initialize from params
    host_ip = params.get('host_ip')
    ping_interval = int(params.get('ping_interval', 60))

    # Initialize context if empty
    ctx = demisto.getIntegrationContext()
    if not ctx.get('host_ip'):
        ctx = {
            'host_ip': host_ip,
            'running': 'true',
            'is_up': 'false',
            'total_uptime': '0',
            'total_downtime': '0',
            'last_check': '',
            'last_state_change': datetime.now().isoformat(),
            'last_latency': '0',
            'total_checks': '0',
            'failed_checks': '0',
            'ping_interval': str(ping_interval)
        }
        demisto.setIntegrationContext(ctx)

    demisto.info(f'Starting ping monitor for {host_ip} with {ping_interval}s interval')

    last_state = None
    last_state_change = datetime.now()

    # NEVER-ENDING LOOP - All monitoring logic runs here in main thread
    while True:
        try:
            # Check if monitoring should stop
            ctx = demisto.getIntegrationContext()
            if ctx.get('running') != 'true':
                demisto.info('Monitoring paused by command')
                time.sleep(10)
                continue

            # Get current config from context (allows dynamic updates)
            host_ip = ctx.get('host_ip', host_ip)
            ping_interval = int(ctx.get('ping_interval', ping_interval))

            # Perform ping check
            result = ping_host(host_ip)
            current_state = result['success']

            # Parse existing state from context
            total_checks = int(ctx.get('total_checks', '0'))
            failed_checks = int(ctx.get('failed_checks', '0'))
            total_uptime = float(ctx.get('total_uptime', '0'))
            total_downtime = float(ctx.get('total_downtime', '0'))

            # Update counters
            total_checks += 1
            if not current_state:
                failed_checks += 1

            # Calculate time deltas for uptime/downtime
            now = datetime.now()
            if last_state is not None:
                time_delta = (now - last_state_change).total_seconds()
                if last_state:
                    total_uptime += time_delta
                else:
                    total_downtime += time_delta

            # Detect state changes and log
            if last_state is not None and last_state != current_state:
                state_str = 'UP' if current_state else 'DOWN'
                demisto.info(f'Host {host_ip} state changed to {state_str}')

                # Log alert message
                if current_state:
                    message = f'Host {host_ip} recovered (UP). Downtime: {total_downtime:.2f}s'
                else:
                    message = f'Host {host_ip} is DOWN! Error: {result.get("error", "Unknown")}'

                demisto.info(f'Alert: {message}')

            # Update state tracking variables
            last_state = current_state
            last_state_change = now

            # Save state to integration context (persists across restarts)
            ctx = {
                'host_ip': host_ip,
                'running': 'true',
                'is_up': 'up' if current_state else 'down',
                'total_uptime': str(total_uptime),
                'total_downtime': str(total_downtime),
                'last_check': now.isoformat(),
                'last_state_change': last_state_change.isoformat(),
                'last_latency': str(result.get('latency') or 0),
                'total_checks': str(total_checks),
                'failed_checks': str(failed_checks),
                'ping_interval': str(ping_interval)
            }
            demisto.setIntegrationContext(ctx)

        except Exception as e:
            demisto.error(f'Error in monitor loop: {str(e)}')
            # NEVER exit - just log and continue

        # Sleep until next check
        time.sleep(ping_interval)


def main():
    """Main execution function."""
    try:
        params = demisto.params()
        command = demisto.command()

        demisto.debug(f'Command being called is {command}')

        if command == 'long-running-execution':
            long_running_execution_command(params)

        elif command == 'ping-monitor-start':
            return_results(start_monitor_command(demisto.args(), params))

        elif command == 'ping-monitor-stop':
            return_results(stop_monitor_command())

        elif command == 'ping-monitor-status':
            return_results(status_command())

        elif command == 'test-module':
            # Test connectivity
            host_ip = params.get('host_ip')
            if not host_ip:
                return_error('Host IP address is required')

            result = ping_host(host_ip)
            if result['success']:
                return_results('ok')
            else:
                return_error(f'Failed to ping {host_ip}: {result["error"]}')

    except Exception as e:
        return_error(f'Failed to execute {demisto.command()} command: {str(e)}')


if __name__ in ['__main__', 'builtin', 'builtins']:
    main()
