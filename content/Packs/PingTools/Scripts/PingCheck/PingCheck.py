"""
PingCheck Script

Pings an IP address and returns comprehensive ping statistics including
latency, packet loss, and success/failure status.
"""

import subprocess
import re
from typing import Dict, Any
import demistomock as demisto
from CommonServerPython import *


def parse_ping_output(output: str, is_windows: bool = False) -> Dict[str, Any]:
    """
    Parse ping command output to extract statistics.

    Args:
        output: Raw ping command output
        is_windows: Whether the output is from Windows ping

    Returns:
        Dictionary containing ping statistics
    """
    result = {
        'success': False,
        'packets_sent': 0,
        'packets_received': 0,
        'packet_loss': 100.0,
        'min_latency': None,
        'avg_latency': None,
        'max_latency': None,
        'error': None
    }

    try:
        # Check if ping was successful (at least one packet received)
        if 'bytes from' in output.lower() or 'reply from' in output.lower():
            result['success'] = True

        # Parse packet statistics
        # Unix/Linux format: "4 packets transmitted, 4 received, 0% packet loss"
        # Windows format: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"

        if is_windows:
            sent_match = re.search(r'Sent\s*=\s*(\d+)', output)
            received_match = re.search(r'Received\s*=\s*(\d+)', output)
            loss_match = re.search(r'\((\d+)%\s+loss\)', output)
        else:
            sent_match = re.search(r'(\d+)\s+packets transmitted', output)
            received_match = re.search(r'(\d+)\s+received', output)
            loss_match = re.search(r'(\d+(?:\.\d+)?)%\s+packet loss', output)

        if sent_match:
            result['packets_sent'] = int(sent_match.group(1))
        if received_match:
            result['packets_received'] = int(received_match.group(1))
        if loss_match:
            result['packet_loss'] = float(loss_match.group(1))

        # Parse latency statistics
        # Unix/Linux format: "rtt min/avg/max/mdev = 10.123/15.456/20.789/2.345 ms"
        # Windows format: "Minimum = 10ms, Maximum = 20ms, Average = 15ms"

        if is_windows:
            min_match = re.search(r'Minimum\s*=\s*(\d+)ms', output)
            max_match = re.search(r'Maximum\s*=\s*(\d+)ms', output)
            avg_match = re.search(r'Average\s*=\s*(\d+)ms', output)

            if min_match:
                result['min_latency'] = float(min_match.group(1))
            if max_match:
                result['max_latency'] = float(max_match.group(1))
            if avg_match:
                result['avg_latency'] = float(avg_match.group(1))
        else:
            # Unix/Linux rtt format
            rtt_match = re.search(r'rtt min/avg/max/(?:mdev|stddev)\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)', output)
            if rtt_match:
                result['min_latency'] = float(rtt_match.group(1))
                result['avg_latency'] = float(rtt_match.group(2))
                result['max_latency'] = float(rtt_match.group(3))

    except Exception as e:
        result['error'] = f'Failed to parse ping output: {str(e)}'

    return result


def ping_host(ip_address: str) -> Dict[str, Any]:
    """
    Ping a host and return statistics.

    Args:
        ip_address: IP address to ping

    Returns:
        Dictionary containing ping results
    """
    # Determine platform and construct ping command
    import platform
    is_windows = platform.system().lower() == 'windows'

    if is_windows:
        # Windows: ping -n 4 <ip>
        cmd = ['ping', '-n', '4', ip_address]
    else:
        # Unix/Linux/Mac: ping -c 4 <ip>
        cmd = ['ping', '-c', '4', ip_address]

    try:
        # Execute ping command
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = process.stdout + process.stderr

        # Parse the output
        stats = parse_ping_output(output, is_windows)

        if process.returncode != 0 and not stats['success']:
            stats['error'] = f'Ping command failed with return code {process.returncode}'

        return stats

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'packets_sent': 4,
            'packets_received': 0,
            'packet_loss': 100.0,
            'min_latency': None,
            'avg_latency': None,
            'max_latency': None,
            'error': 'Ping command timed out after 30 seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'packets_sent': 0,
            'packets_received': 0,
            'packet_loss': 100.0,
            'min_latency': None,
            'avg_latency': None,
            'max_latency': None,
            'error': f'Failed to execute ping: {str(e)}'
        }


def main():
    """Main execution function."""
    try:
        # Get arguments
        args = demisto.args()
        ip_address = args.get('ip_address')

        if not ip_address:
            return_error('IP address is required')

        # Perform ping
        result = ping_host(ip_address)

        # Create context output
        context = {
            'PingCheck(val.IPAddress == obj.IPAddress)': {
                'IPAddress': ip_address,
                'Success': result['success'],
                'PacketsSent': result['packets_sent'],
                'PacketsReceived': result['packets_received'],
                'PacketLoss': result['packet_loss'],
                'MinLatency': result['min_latency'],
                'AvgLatency': result['avg_latency'],
                'MaxLatency': result['max_latency'],
                'Error': result['error']
            }
        }

        # Create human-readable output
        if result['success']:
            hr = f'''### Ping Results for {ip_address}
**Status:** Success ✓

**Packet Statistics:**
- Packets Sent: {result['packets_sent']}
- Packets Received: {result['packets_received']}
- Packet Loss: {result['packet_loss']}%

**Latency Statistics:**
- Minimum: {result['min_latency']} ms
- Average: {result['avg_latency']} ms
- Maximum: {result['max_latency']} ms
'''
        else:
            hr = f'''### Ping Results for {ip_address}
**Status:** Failed ✗

**Error:** {result['error'] or 'Host unreachable'}

**Packet Statistics:**
- Packets Sent: {result['packets_sent']}
- Packets Received: {result['packets_received']}
- Packet Loss: {result['packet_loss']}%
'''

        return_results({
            'Type': entryTypes['note'],
            'ContentsFormat': formats['json'],
            'Contents': result,
            'HumanReadable': hr,
            'EntryContext': context
        })

    except Exception as e:
        return_error(f'Failed to execute PingCheck: {str(e)}')


if __name__ in ['__main__', 'builtin', 'builtins']:
    main()
