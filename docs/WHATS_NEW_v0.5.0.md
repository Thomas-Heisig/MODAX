# What's New in MODAX v0.5.0

## MDI Interface & Network Scanner Release

**Release Date:** 2025-12-17  
**Version:** 0.5.0

---

## 🎉 Major New Features

### 1. Multiple Document Interface (MDI)

MODAX now features a modern MDI interface that allows you to work with multiple windows simultaneously in a single application container.

**Key Features:**
- **Menu Bar** with File, View, Window, and Help menus
- **Toolbar** with quick access buttons for common operations
- **Status Bar** showing connection status and system time
- **Child Windows** that can be cascaded, tiled, or arranged
- **Keyboard Shortcuts** for fast navigation (Ctrl+D, Ctrl+N, F1, etc.)

**How to Use:**
- Launch MODAX HMI to start in MDI mode by default
- Use `View` menu or toolbar buttons to open different windows
- Use `Window` menu to arrange multiple windows
- Press `F1` for comprehensive help

**Classic Mode:**
If you prefer the traditional single-window interface, set:
```bash
export MODAX_MDI_MODE=false
```

### 2. Enhanced Dashboard

The new Dashboard provides a comprehensive overview of your MODAX system with multiple tabs:

#### Overview Tab
- **System Status**: Real-time connection indicator
- **Devices Online**: Count of connected devices
- **AI Status**: Shows if AI analysis is enabled
- **System Uptime**: Displays system runtime

#### Devices Tab
- **Device Grid**: View all connected devices in a table
- **Refresh Button**: Manually update device list
- **Real-time Updates**: Auto-refresh every 2 seconds
- **Device Details**: Shows device ID, type, status, and last seen

#### Analytics Tab
- Placeholder for future charts and statistics
- Ready for integration with real-time metrics

#### Logs Tab
- **Real-time Activity Log**: See system events as they happen
- **Auto-scrolling**: Automatically scrolls to latest entries
- **Clear Button**: Clear log history
- **Size Limit**: Keeps last 1000 lines to prevent memory issues

**How to Access:**
- Click `Dashboard` in toolbar or press `Ctrl+D`
- Window opens as MDI child and can be resized/moved
- Updates automatically every 2 seconds

### 3. Network Scanner & Port Scanner

Revolutionary new tool for automatic network device discovery and service detection.

#### Network Scanner
**Features:**
- **Full Network Scan**: Scan entire subnets using CIDR notation (e.g., 192.168.1.0/24)
- **Local Subnet Scan**: One-click scan of your local network
- **Device Discovery**: Automatically finds active devices
- **Hostname Resolution**: Resolves IP addresses to hostnames
- **Device Type Detection**: Identifies Modbus, OPC UA, MODAX, Web servers, etc.
- **Open Ports Detection**: Shows which services are running

**How to Use:**
1. Click `Network Scanner` in toolbar or press `Ctrl+N`
2. Choose "Network Scanner" tab
3. Enter network range or click "Scan Local Subnet"
4. View results in the grid showing IP, hostname, type, and ports

#### Port Scanner
**Features:**
- **Common Ports Preset**: Scan 20+ common ports (SSH, HTTP, MQTT, Modbus, OPC UA, etc.)
- **Custom Port List**: Specify exact ports to scan
- **Service Identification**: Automatically identifies services by port
- **Color-coded Results**: Green for open ports, gray for closed
- **Fast Scanning**: Optimized timeout settings

**How to Use:**
1. Open Network Scanner window
2. Choose "Port Scanner" tab
3. Enter host IP or hostname
4. Check "Scan common ports" or enter custom ports
5. Click "Scan Ports" to see results

**Detected Device Types:**
- Modbus Device (port 502)
- OPC UA Device (ports 44818, 4840)
- MODAX Control System (ports 8000, 8001)
- Web Server (ports 80, 443)
- SSH Device (port 22)
- And more...

---

## 🚀 Backend Improvements

### New API Endpoints

Four new REST API endpoints for network discovery:

1. **POST /api/v1/network/scan**
   - Scan entire network ranges
   - Auto-discover local subnet
   - Rate limited: 5 requests/minute

2. **POST /api/v1/network/scan/quick**
   - Quick scan of specific hosts
   - Maximum 100 hosts per request
   - Rate limited: 10 requests/minute

3. **POST /api/v1/port/scan**
   - Scan common or custom ports
   - Maximum 1000 ports per scan
   - Rate limited: 10 requests/minute

4. **POST /api/v1/port/scan/range**
   - Scan port ranges (e.g., 8000-8100)
   - Maximum 1000 ports per scan
   - Rate limited: 5 requests/minute

See [API.md](API.md) for complete documentation.

### Network Scanner Module

New Python module `network_scanner.py` with:
- **NetworkScanner** class for device discovery
- **PortScanner** class for service detection
- **NetworkDevice** class for device representation
- Automatic device type identification
- Hostname resolution
- Concurrent scanning with asyncio

**Quality Assurance:**
- 11 unit tests with 100% pass rate
- No security vulnerabilities (CodeQL verified)
- Rate limiting to prevent abuse
- Comprehensive error handling

---

## 📊 Statistics

### Test Coverage
- **172+ Unit Tests** (was 161+)
- **11 New Tests** for network scanner module
- **96-97% Code Coverage** maintained
- **0 Security Vulnerabilities** (CodeQL checked)

### Code Changes
- **7 New Files Created**
  - 3 C# view forms (MDI, Dashboard, Network Scanner)
  - 1 Python module (network_scanner)
  - 1 Test file (test_network_scanner)
  - 2 Documentation files
- **4 Files Modified**
  - Program.cs (MDI mode support)
  - control_api.py (new endpoints)
  - README.md (version update)
  - INDEX.md (documentation index)

---

## 🎹 Keyboard Shortcuts

### General
- `F1` - Help documentation
- `Ctrl+H` - Keyboard shortcuts

### Windows
- `Ctrl+D` - Open Dashboard
- `Ctrl+N` - Open Network Scanner
- `Ctrl+K` - Open Classic View
- `Ctrl+W` - Close active window
- `Ctrl+Shift+W` - Close all windows

### Layout
- `Ctrl+1` - Cascade windows
- `Ctrl+2` - Tile horizontally
- `Ctrl+3` - Tile vertically

---

## 🔒 Security Features

### Rate Limiting
All network scanning endpoints are protected with rate limits to prevent abuse and ensure system stability.

### Audit Logging
All network and port scanning activities are logged with:
- Timestamp
- User/API key (if authenticated)
- Scan parameters
- Results summary

### Best Practices
- Only scan authorized networks
- Be aware scans may trigger security alerts
- Use appropriate permissions
- Follow your organization's security policies

---

## 📚 Documentation

### New Documentation
- **[MDI_INTERFACE.md](MDI_INTERFACE.md)** - Complete MDI interface guide
- **[WHATS_NEW_v0.5.0.md](WHATS_NEW_v0.5.0.md)** - This document

### Updated Documentation
- **[README.md](../README.md)** - Version 0.5.0 features
- **[API.md](API.md)** - Network scanner endpoints
- **[INDEX.md](INDEX.md)** - Documentation index

---

## 🔄 Migration Guide

### From v0.4.1 to v0.5.0

**No Breaking Changes!** v0.5.0 is fully backward compatible.

**For Developers:**
1. Update to latest code: `git pull`
2. Install any new dependencies (none required)
3. Run tests to verify: `./test_with_coverage.sh`

**For Users:**
1. Launch MODAX HMI - automatically starts in MDI mode
2. Explore new Dashboard and Network Scanner
3. Use classic mode if preferred: `export MODAX_MDI_MODE=false`

**For API Clients:**
- All existing endpoints continue to work
- New endpoints available at `/api/v1/network/*` and `/api/v1/port/*`
- Rate limiting applies to new endpoints

---

## 🐛 Known Limitations

1. **Window State Persistence**: Window positions and sizes are not saved between sessions (planned for future release)
2. **Preferences Dialog**: Centralized settings dialog not yet implemented (planned for future release)
3. **C# Build on Linux**: Building C# components requires Windows or EnableWindowsTargeting (expected limitation)
4. **Network Scan Speed**: Large network scans may take several minutes depending on network size

---

## 🔮 What's Next?

### Planned for v0.6.0
- Window state persistence (save window positions)
- Preferences dialog for customization
- Enhanced analytics with real-time charts
- Network topology visualization
- Automated device configuration

### Future Roadmap
- Dark mode support
- Multi-language internationalization
- Advanced filtering and search
- Export capabilities (CSV, JSON, PDF)
- Integration with external monitoring tools

---

## 🙏 Acknowledgments

Special thanks to:
- Contributors who suggested MDI interface
- Security researchers who validated our scanning implementation
- Community members who tested early versions

---

## 📞 Support

Need help with v0.5.0?

1. **Documentation**: Press `F1` in HMI or see [MDI_INTERFACE.md](MDI_INTERFACE.md)
2. **Keyboard Shortcuts**: Press `Ctrl+H` in HMI
3. **Issues**: Check [ISSUES.md](../ISSUES.md) or create a new issue
4. **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📜 License

MODAX v0.5.0 is released under the MIT License.

© 2024 Thomas Heisig

---

**Enjoy the new features!** 🎉
