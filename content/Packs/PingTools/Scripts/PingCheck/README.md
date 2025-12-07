# PingCheck Script

## Overview
A simple XSOAR automation script that pings an IP address and returns comprehensive statistics including latency, packet loss, and success/failure status.

## Use Cases
- Quick connectivity testing from XSOAR
- Network troubleshooting
- Verify host reachability
- Measure network latency
- Check for packet loss

## Script Data

| **Name** | **Description** |
| --- | --- |
| Script Type | python3 |
| Tags | network, diagnostic |

## Inputs

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| ip_address | IP address to ping | Required |

## Outputs

| **Path** | **Description** | **Type** |
| --- | --- | --- |
| PingCheck.IPAddress | IP address that was pinged | String |
| PingCheck.Success | Whether the ping was successful | Boolean |
| PingCheck.PacketsSent | Number of packets sent | Number |
| PingCheck.PacketsReceived | Number of packets received | Number |
| PingCheck.PacketLoss | Packet loss percentage | Number |
| PingCheck.MinLatency | Minimum latency in milliseconds | Number |
| PingCheck.AvgLatency | Average latency in milliseconds | Number |
| PingCheck.MaxLatency | Maximum latency in milliseconds | Number |
| PingCheck.Error | Error message if ping failed | String |

## Example Usage

### War Room Command
```
!PingCheck ip_address="8.8.8.8"
```

### Expected Output
```
### Ping Results for 8.8.8.8
**Status:** Success ✓

**Packet Statistics:**
- Packets Sent: 4
- Packets Received: 4
- Packet Loss: 0%

**Latency Statistics:**
- Minimum: 10.5 ms
- Average: 12.3 ms
- Maximum: 15.1 ms
```

## Technical Details
- Sends 4 ICMP echo requests (ping packets)
- Parses output from native OS ping command
- Supports both Windows and Unix/Linux/Mac platforms
- 30-second timeout for ping command
- Handles unreachable hosts gracefully

## Known Limitations
- Requires ICMP to be allowed through firewalls
- May require elevated permissions on some systems
- Dependent on OS-level ping utility
