# MDI Interface Documentation

## Overview

MODAX now features a **Multiple Document Interface (MDI)** that provides a modern, tabbed workspace for managing multiple views and tools simultaneously. This interface enhances productivity by allowing users to work with multiple windows within a single application container.

## Features

### MDI Parent Window

The main MDI parent window provides:

- **Menu Bar**: Access to all features and commands
- **Toolbar**: Quick access to common operations
- **Status Bar**: Real-time connection status and time display
- **MDI Client Area**: Workspace for child windows

### Child Windows

#### 1. Dashboard
The Dashboard provides a comprehensive overview of the MODAX system with multiple tabs:

**Overview Tab:**
- System status display
- Devices online count
- AI status indicator
- System uptime

**Devices Tab:**
- Device list in grid format
- Device status monitoring
- Refresh functionality
- Real-time device information

**Analytics Tab:**
- Statistical charts (planned)
- Trend analysis (planned)
- Performance metrics (planned)

**Logs Tab:**
- System event logs
- Real-time activity monitoring
- Log filtering and clearing
- Auto-scrolling with size limit (1000 lines)

#### 2. Network Scanner
The Network Scanner tool provides two main functions:

**Network Scanner Tab:**
- Scan entire network ranges (CIDR notation)
- Quick local subnet scanning
- Device discovery with hostname resolution
- Device type identification
- Open ports detection
- Results displayed in searchable grid

**Port Scanner Tab:**
- Scan specific hosts for open ports
- Common ports preset (22, 80, 443, 502, 8000, 8001, etc.)
- Custom port range scanning
- Service identification
- Color-coded results (green for open, gray for closed)

#### 3. Classic View
Access to the original single-window interface for users who prefer the traditional layout.

## Keyboard Shortcuts

### General
- `F1` - Show comprehensive help documentation
- `Ctrl+H` - Show keyboard shortcuts

### Window Management
- `Ctrl+D` - Open Dashboard
- `Ctrl+N` - Open Network Scanner
- `Ctrl+K` - Open Classic View
- `Ctrl+W` - Close active window
- `Ctrl+Shift+W` - Close all windows

### Layout Management
- `Ctrl+1` - Cascade windows
- `Ctrl+2` - Tile windows horizontally
- `Ctrl+3` - Tile windows vertically

### Application
- `Alt+F4` - Exit application

## Menu Structure

### File Menu
- Exit - Close the application

### View Menu
- Dashboard - Open Dashboard window
- Network Scanner - Open Network Scanner window
- Classic View - Open traditional interface
- Refresh All - Refresh all open windows

### Window Menu
- Cascade - Arrange windows in cascade
- Tile Horizontal - Tile windows horizontally
- Tile Vertical - Tile windows vertically
- Arrange Icons - Arrange minimized window icons
- Close All - Close all child windows

### Help Menu
- Documentation (F1) - Open comprehensive documentation
- Keyboard Shortcuts - Show keyboard shortcuts
- About - Show about dialog

## Network Scanner API

The network scanner functionality is powered by backend API endpoints:

### Network Scanning
**Endpoint:** `POST /api/v1/network/scan`

**Parameters:**
- `network` (optional): CIDR notation (e.g., "192.168.1.0/24")

**Features:**
- Scans entire network range for active devices
- Auto-discovers local subnet if network not specified
- Rate limited to prevent abuse (5 requests/minute)
- Returns device IP, hostname, type, and open ports

### Quick Scan
**Endpoint:** `POST /api/v1/network/scan/quick`

**Parameters:**
- `hosts`: List of IP addresses or hostnames

**Features:**
- Quick scan of specific hosts
- Maximum 100 hosts per request
- Rate limited (10 requests/minute)
- Returns active devices from provided list

### Port Scanning
**Endpoint:** `POST /api/v1/port/scan`

**Parameters:**
- `host`: IP address or hostname
- `ports` (optional): List of specific ports
- `common_ports`: Boolean, scan common ports

**Features:**
- Scans specific ports on a host
- Common ports preset available
- Maximum 1000 ports per scan
- Service identification
- Rate limited (10 requests/minute)

### Port Range Scanning
**Endpoint:** `POST /api/v1/port/scan/range`

**Parameters:**
- `host`: IP address or hostname
- `start_port`: Starting port number
- `end_port`: Ending port number

**Features:**
- Scans continuous port range
- Maximum 1000 ports per scan
- Faster timeout for range scans
- Rate limited (5 requests/minute)

## Device Type Detection

The network scanner automatically identifies device types based on open ports:

- **Modbus Device**: Port 502 open
- **OPC UA Device**: Ports 44818 or 4840 open
- **MODAX Control System**: Ports 8000 and 8001 open
- **MODAX Control Layer**: Port 8000 open
- **MODAX AI Layer**: Port 8001 open
- **Web Server**: Ports 80 or 443 open
- **SSH Device**: Port 22 open
- **Telnet Device**: Port 23 open
- **Unknown Device**: Other port combinations

## Configuration

### MDI Mode Toggle
Set the environment variable to control MDI mode:

```bash
# Enable MDI mode (default)
export MODAX_MDI_MODE=true

# Disable MDI mode (use classic view)
export MODAX_MDI_MODE=false
```

### Scanner Timeouts
Default timeouts are optimized for typical network environments:
- Network scan: 1.0 second per host
- Port scan: 1.0 second per port
- Range scan: 0.5 second per port (faster)

## Security Considerations

### Rate Limiting
All network scanning endpoints are rate-limited to prevent abuse:
- Network scan: 5 requests/minute
- Quick scan: 10 requests/minute
- Port scan: 10 requests/minute
- Range scan: 5 requests/minute

### Audit Logging
All scanning activities are logged with:
- Timestamp
- User/API key (if authenticated)
- Scan parameters
- Results summary

### Network Access
Scanning operations:
- Require appropriate API authentication if enabled
- Log all activities for security audit
- May be restricted by firewall rules
- Should only be used on authorized networks

## Best Practices

### Dashboard Usage
1. Keep Dashboard open for continuous system monitoring
2. Use Logs tab to track system events
3. Refresh devices regularly to ensure accurate status
4. Monitor uptime and device counts

### Network Scanning
1. Always obtain authorization before scanning networks
2. Use quick scan for known hosts instead of full network scans
3. Start with common ports before custom port lists
4. Be aware that scans can trigger security alerts
5. Use appropriate CIDR notation for network ranges

### Window Management
1. Use keyboard shortcuts for faster navigation
2. Tile windows for multi-task viewing
3. Close unused windows to improve performance
4. Use cascade for better window organization

## Troubleshooting

### Dashboard Not Updating
- Check Control Layer connection in status bar
- Verify network connectivity
- Check if Control Layer service is running
- Review Logs tab for error messages

### Network Scan Fails
- Verify network parameter format (CIDR notation)
- Check if you have network access permissions
- Ensure firewall allows outbound connections
- Try scanning smaller network ranges
- Check API rate limits

### Port Scan Returns No Results
- Verify host is reachable
- Check firewall settings
- Ensure host is running target services
- Try common ports first
- Increase timeout if needed

### MDI Windows Not Opening
- Check for errors in Logs tab
- Verify sufficient system resources
- Try closing other windows first
- Restart application if persists

## Future Enhancements

Planned improvements for the MDI interface:

1. **Window State Persistence**: Remember window positions and sizes
2. **Preferences Dialog**: Customize MDI behavior and appearance
3. **Enhanced Analytics Tab**: Real-time charts and statistics
4. **Network Tab in Dashboard**: Integrated network view
5. **Custom Layouts**: Save and restore window arrangements
6. **Docking Support**: Dock windows to edges
7. **Tabbed Document Interface**: Alternative to MDI

## Related Documentation

- [HMI Layer Documentation](../csharp-hmi-layer/README.md)
- [API Documentation](API.md)
- [Network Architecture](NETWORK_ARCHITECTURE.md)
- [Security](SECURITY.md)

## Support

For issues related to the MDI interface:

1. Check this documentation
2. Review keyboard shortcuts (Ctrl+H)
3. Check Logs tab in Dashboard
4. Consult [Troubleshooting Guide](TROUBLESHOOTING.md)
5. Open an issue on GitHub

---

**Version**: 0.5.0  
**Last Updated**: 2025-12-17  
**Author**: Thomas Heisig
