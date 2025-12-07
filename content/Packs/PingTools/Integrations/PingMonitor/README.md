# PingMonitor Integration

## Overview
A long-running XSOAR integration that continuously monitors a host via ping, tracks uptime/downtime statistics, and sends email alerts when the host goes down or comes back up.

## Use Cases
- Continuous availability monitoring
- Network uptime tracking
- Proactive alerting for host failures
- SLA monitoring and reporting
- Automated incident creation for downtime events

## Configuration

### Integration Settings

| **Parameter** | **Description** | **Required** |
| --- | --- | --- |
| Host IP Address | IP address of the host to monitor | Required |
| Ping Interval (seconds) | How often to ping the host (default: 60) | Required |
| Alert Email Address | Email address to send alerts to | Optional |
| Email Instance Name | Name of email integration to use (default: Gmail) | Optional |
| Long running instance | Enable long-running mode | Required |

### Initial Setup
1. Configure an email integration (e.g., Gmail, Office 365) if you want email alerts
2. Create a new PingMonitor integration instance
3. Enter the target host IP address
4. Set the ping interval (recommended: 60-300 seconds)
5. Optionally configure alert email and email instance name
6. Enable "Long running instance"
7. Save the configuration
8. The monitoring will start automatically

## Commands

### ping-monitor-start
Start or restart the ping monitoring service.

#### Arguments
| **Name** | **Description** | **Required** |
| --- | --- | --- |
| host_ip | IP address to monitor (overrides configured value) | Optional |

#### Example
```
!ping-monitor-start host_ip="192.168.1.1"
```

---

### ping-monitor-status
Get current monitoring status and statistics.

#### Context Output
| **Path** | **Type** | **Description** |
| --- | --- | --- |
| PingMonitor.HostIP | String | IP address being monitored |
| PingMonitor.Status | String | Current status (up/down) |
| PingMonitor.Uptime | Number | Total uptime in seconds |
| PingMonitor.Downtime | Number | Total downtime in seconds |
| PingMonitor.UptimePercentage | Number | Uptime percentage |
| PingMonitor.LastCheck | Date | Timestamp of last ping check |
| PingMonitor.LastLatency | Number | Last measured latency in milliseconds |
| PingMonitor.TotalChecks | Number | Total number of ping checks performed |
| PingMonitor.FailedChecks | Number | Number of failed ping checks |

#### Example
```
!ping-monitor-status
```

#### Expected Output
```
### Ping Monitor Status

**Host:** 8.8.8.8
**Current Status:** UP ✓

**Statistics:**
- Total Checks: 120
- Failed Checks: 2
- Success Rate: 98.33%

**Uptime Metrics:**
- Total Uptime: 7080.00 seconds (118.00 minutes)
- Total Downtime: 120.00 seconds (2.00 minutes)
- Uptime Percentage: 98.33%

**Latest Check:**
- Last Check Time: 2025-12-07 15:30:45
- Last Latency: 12.5 ms
```

---

### ping-monitor-stop
Stop the ping monitoring service.

#### Example
```
!ping-monitor-stop
```

## Email Alerts

When configured with an alert email address, PingMonitor automatically sends emails when:

### Host Goes Down
```
Subject: [ALERT] Host 192.168.1.1 is DOWN
Body:
The monitored host 192.168.1.1 is no longer responding to ping.

Last Successful Check: 2025-12-07 15:25:30
Detection Time: 2025-12-07 15:26:30
Error: Host unreachable

This is an automated alert from XSOAR PingMonitor.
```

### Host Comes Back Up
```
Subject: [RESOLVED] Host 192.168.1.1 is now UP
Body:
The monitored host 192.168.1.1 has recovered and is now responding to ping.

Downtime Duration: 180.00 seconds
Recovery Time: 2025-12-07 15:29:30

This is an automated alert from XSOAR PingMonitor.
```

## Integration Architecture

### Long-Running Mode
- Runs continuously in the background
- Uses a separate monitoring thread
- Automatic state management
- Thread-safe operations

### Monitoring Logic
1. Performs ping check at configured interval
2. Tracks state transitions (up → down, down → up)
3. Calculates cumulative uptime/downtime
4. Sends email alerts on state changes
5. Stores statistics for reporting

### Statistics Tracking
- Total checks performed
- Failed checks count
- Uptime in seconds
- Downtime in seconds
- Uptime percentage
- Last check timestamp
- Current latency

## Technical Details
- **Platform Support:** Windows, Linux, Unix, macOS
- **Ping Method:** Native OS ping command (ICMP)
- **Thread Safety:** Uses threading.Lock for state protection
- **Timeout:** 10 seconds per ping attempt
- **Packets:** Sends 1 packet per check for efficiency

## Troubleshooting

### Monitor Not Starting
- Verify the host IP is valid
- Check that long-running mode is enabled
- Review integration logs for errors
- Ensure firewall allows ICMP

### Email Alerts Not Received
- Verify email integration is configured correctly
- Check the alert email address is valid
- Confirm email instance name matches configured integration
- Review War Room for email command errors

### High Latency or Packet Loss
- Check network conditions
- Verify target host is properly functioning
- Consider increasing ping interval to reduce load
- Review host firewall rules

## Best Practices
1. Set ping interval based on criticality (critical hosts: 30-60s, normal: 60-300s)
2. Monitor from XSOAR instance with good network connectivity
3. Use separate monitoring instances for different network segments
4. Configure email alerts for critical infrastructure only
5. Regularly review uptime statistics via ping-monitor-status
6. Pair with playbooks for automated incident response

## Known Limitations
- Monitors one host per integration instance
- Requires ICMP to be allowed
- Email requires separate email integration configured
- Statistics reset when integration is restarted
- Does not persist data across XSOAR restarts
