# MODAX Network Architecture & OT/IT Separation

## Overview
This document describes the network architecture for the MODAX industrial control system, with emphasis on OT (Operational Technology) and IT (Information Technology) network separation following IEC 62443 guidelines and the Purdue Model.

## Purdue Model Implementation

```
┌─────────────────────────────────────────────────────────────┐
│ Level 5: Enterprise Network (IT)                            │
│ - ERP Systems (SAP, Oracle)                                 │
│ - Business Analytics                                        │
│ - Corporate Email, File Servers                             │
│ VLAN: 192.168.1.0/24                                        │
└────────────────┬────────────────────────────────────────────┘
                 │ Firewall + DMZ
                 │ Rules: HTTPS only, deep packet inspection
┌────────────────┴────────────────────────────────────────────┐
│ Level 4: Site Operations (IT/OT Boundary)                   │
│ - HMI Clients                                               │
│ - Historian Databases                                       │
│ - SCADA Systems                                             │
│ - Data Warehouses                                           │
│ VLAN: 10.0.1.0/24                                           │
└────────────────┬────────────────────────────────────────────┘
                 │ Industrial Firewall
                 │ Rules: Whitelisted protocols only
┌────────────────┴────────────────────────────────────────────┐
│ Level 3: Site Supervisory Control (OT)                      │
│ - Control Layer (Python)                                    │
│ - AI Layer (Python)                                         │
│ - MQTT Broker                                               │
│ - TimescaleDB                                               │
│ - Monitoring (Grafana, Prometheus)                          │
│ VLAN: 10.0.2.0/24                                           │
└────────────────┬────────────────────────────────────────────┘
                 │ Zone Firewall
                 │ Rules: MQTT, Modbus TCP only
┌────────────────┴────────────────────────────────────────────┐
│ Level 2: Area Control (OT)                                  │
│ - PLCs (Safety Systems)                                     │
│ - Industrial PCs                                            │
│ - Local HMI Terminals                                       │
│ VLAN: 10.0.3.0/24                                           │
└────────────────┬────────────────────────────────────────────┘
                 │ Device Firewall
                 │ Rules: Read-only MQTT publish
┌────────────────┴────────────────────────────────────────────┐
│ Level 1: Basic Control (OT)                                 │
│ - Industrial Switches                                       │
│ - I/O Modules                                               │
│ VLAN: 10.0.4.0/24                                           │
└────────────────┬────────────────────────────────────────────┘
                 │ Hardwired
┌────────────────┴────────────────────────────────────────────┐
│ Level 0: Process/Field Devices (OT)                         │
│ - ESP32 Devices                                             │
│ - Sensors & Actuators                                       │
│ - Motor Drives                                              │
│ VLAN: 10.0.5.0/24                                           │
└─────────────────────────────────────────────────────────────┘
```

## Network Segmentation

### VLAN Configuration

#### Level 5: Enterprise Network (192.168.1.0/24)
```
Purpose: Corporate IT systems
Access: General employees
Security: Standard IT security
Isolation: Complete separation from OT
```

#### Level 4: Site Operations (10.0.1.0/24)
```
Purpose: Operations management, HMI
Access: Operations team, engineers
Security: Role-based access control
Protocols: HTTPS, RDP, SSH (with MFA)
```

#### Level 3: Supervisory Control (10.0.2.0/24)
```
Purpose: MODAX Control & AI Layers
Access: Automated systems, administrators
Security: Certificate-based authentication
Protocols: MQTT over TLS, HTTPS API
Services:
  - Control Layer: 10.0.2.10
  - AI Layer: 10.0.2.11
  - MQTT Broker: 10.0.2.20
  - TimescaleDB: 10.0.2.30
  - Prometheus: 10.0.2.40
  - Grafana: 10.0.2.41
```

#### Level 2: Area Control (10.0.3.0/24)
```
Purpose: PLCs, safety systems
Access: Safety-critical automation
Security: Hardware interlocks
Protocols: Modbus TCP, EtherNet/IP
```

#### Level 1: Basic Control (10.0.4.0/24)
```
Purpose: I/O modules, industrial switches
Access: Direct equipment control
Security: Physical security
Protocols: Modbus RTU, EtherNet/IP
```

#### Level 0: Field Devices (10.0.5.0/24)
```
Purpose: ESP32, sensors, actuators
Access: Field devices only
Security: MAC filtering, port security
Protocols: MQTT publish only
IP Range: 10.0.5.100-10.0.5.254 (DHCP)
```

## Firewall Rules

### DMZ Firewall (Level 5 ↔ Level 4)

```bash
# Allow HTTPS from Enterprise to Site Operations
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.1.0/24 -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT

# Allow HTTPS responses
iptables -A FORWARD -s 10.0.1.0/24 -d 192.168.1.0/24 -p tcp --sport 443 -m state --state ESTABLISHED -j ACCEPT

# Allow specific HMI access (authenticated users only)
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.1.10 -p tcp --dport 8000 -m state --state NEW,ESTABLISHED -j ACCEPT

# Deny all other traffic
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.0.0/16 -j LOG --log-prefix "DMZ-DENY: "
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.0.0/16 -j DROP
```

### Industrial Firewall (Level 4 ↔ Level 3)

```bash
# Allow HMI to Control Layer API
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.10 -p tcp --dport 8000 -j ACCEPT

# Allow HMI to AI Layer API  
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.11 -p tcp --dport 8001 -j ACCEPT

# Allow read access to TimescaleDB (queries only)
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.30 -p tcp --dport 5432 -m state --state NEW -m limit --limit 10/sec -j ACCEPT

# Allow Grafana access
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.41 -p tcp --dport 3000 -j ACCEPT

# Deny all other Level 4 → Level 3 traffic
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.0/24 -j LOG --log-prefix "L4-L3-DENY: "
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.0/24 -j DROP
```

### Zone Firewall (Level 3 ↔ Level 2)

```bash
# Allow Control Layer to PLC (read status)
iptables -A FORWARD -s 10.0.2.10 -d 10.0.3.0/24 -p tcp --dport 502 -j ACCEPT  # Modbus TCP

# Deny all commands from Control Layer to safety PLCs
# Safety commands must go through separate certified path

# Log and deny all other traffic
iptables -A FORWARD -s 10.0.2.0/24 -d 10.0.3.0/24 -j LOG --log-prefix "L3-L2-DENY: "
iptables -A FORWARD -s 10.0.2.0/24 -d 10.0.3.0/24 -j DROP
```

### Device Firewall (Level 2 ↔ Level 1 ↔ Level 0)

```bash
# Allow ESP32 (Level 0) to publish MQTT to broker (Level 3)
iptables -A FORWARD -s 10.0.5.0/24 -d 10.0.2.20 -p tcp --dport 8883 -j ACCEPT  # MQTT over TLS

# Deny ESP32 from accessing anything else
iptables -A FORWARD -s 10.0.5.0/24 ! -d 10.0.2.20 -j LOG --log-prefix "ESP32-DENY: "
iptables -A FORWARD -s 10.0.5.0/24 ! -d 10.0.2.20 -j DROP

# Deny Level 0 devices from communicating with each other (prevent lateral movement)
iptables -A FORWARD -s 10.0.5.0/24 -d 10.0.5.0/24 -j DROP
```

## Network Services Configuration

### DNS Configuration
```
# /etc/hosts or internal DNS
10.0.2.10    modax-control.local
10.0.2.11    modax-ai.local
10.0.2.20    modax-mqtt.local
10.0.2.30    modax-db.local
10.0.2.40    modax-prometheus.local
10.0.2.41    modax-grafana.local
```

### NTP Configuration
```
# ntp.conf for Level 3 (Supervisory Control)
server 10.0.2.50  # Local NTP server in OT network
restrict default kod nomodify notrap nopeer noquery
restrict 127.0.0.1
restrict ::1
restrict 10.0.2.0 mask 255.255.255.0 nomodify notrap
```

### DHCP Configuration for ESP32
```
# dhcpd.conf for Level 0 (Field Devices)
subnet 10.0.5.0 netmask 255.255.255.0 {
    range 10.0.5.100 10.0.5.254;
    option routers 10.0.5.1;
    option domain-name-servers 10.0.2.50;
    option ntp-servers 10.0.2.50;
    default-lease-time 86400;
    max-lease-time 172800;
    
    # Static assignments for known ESP32 devices
    host esp32-001 {
        hardware ethernet 24:0A:C4:XX:XX:XX;
        fixed-address 10.0.5.101;
    }
}
```

## Network Security Measures

### Port Security (Switch Configuration)
```
# Cisco switch configuration
interface GigabitEthernet1/0/1
  description ESP32-001
  switchport access vlan 1005
  switchport mode access
  switchport port-security
  switchport port-security maximum 1
  switchport port-security mac-address sticky
  switchport port-security violation restrict
  spanning-tree portfast
  spanning-tree bpduguard enable
```

### MAC Address Filtering
```python
# Whitelist of authorized ESP32 devices
AUTHORIZED_DEVICES = {
    "24:0A:C4:12:34:56": "esp32_001",
    "24:0A:C4:12:34:57": "esp32_002",
    "24:0A:C4:12:34:58": "esp32_003",
}

def validate_device_mac(mac_address):
    """Validate device is authorized to connect"""
    if mac_address not in AUTHORIZED_DEVICES:
        logger.security(f"Unauthorized device attempted connection: {mac_address}")
        return False
    return True
```

### 802.1X Authentication (Future Enhancement)
```
# Enable 802.1X on switches
aaa new-model
radius-server host 10.0.2.60 key SecretKey
aaa authentication dot1x default group radius

interface GigabitEthernet1/0/1
  authentication port-control auto
  dot1x pae authenticator
```

## Traffic Flow Examples

### Normal Sensor Data Flow
```
ESP32 (10.0.5.101) 
  → Port 8883/TCP
  → MQTT Broker (10.0.2.20)
  → Topic: modax/sensor/data
  → Control Layer (10.0.2.10) subscribes
  → Writes to TimescaleDB (10.0.2.30)
```

### HMI Query Flow
```
HMI Client (10.0.1.50)
  → Port 8000/TCP (HTTPS)
  → Control Layer API (10.0.2.10)
  → Queries TimescaleDB (10.0.2.30)
  → Returns JSON to HMI
```

### AI Analysis Flow
```
Control Layer (10.0.2.10)
  → Port 8001/TCP (HTTPS)
  → AI Layer (10.0.2.11)
  → Performs analysis
  → Returns recommendations
  → Control Layer logs to DB
```

## VPN Access for Remote Maintenance

### WireGuard VPN Server Configuration
```
# /etc/wireguard/wg0.conf (on Level 4 gateway)
[Interface]
Address = 10.0.1.254/24
PrivateKey = <server-private-key>
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT

# Engineer 1
[Peer]
PublicKey = <engineer1-public-key>
AllowedIPs = 10.0.1.201/32

# Engineer 2
[Peer]
PublicKey = <engineer2-public-key>
AllowedIPs = 10.0.1.202/32
```

### VPN Client Configuration
```
# Engineer's laptop
[Interface]
Address = 10.0.1.201/24
PrivateKey = <engineer1-private-key>
DNS = 10.0.2.50

[Peer]
PublicKey = <server-public-key>
Endpoint = vpn.modax.company.com:51820
AllowedIPs = 10.0.1.0/24, 10.0.2.0/24
PersistentKeepalive = 25
```

### VPN Access Rules
```bash
# Only allow VPN users to access Level 4 and Level 3
iptables -A FORWARD -i wg0 -d 10.0.1.0/24 -j ACCEPT
iptables -A FORWARD -i wg0 -d 10.0.2.0/24 -j ACCEPT
iptables -A FORWARD -i wg0 -j LOG --log-prefix "VPN-DENY: "
iptables -A FORWARD -i wg0 -j DROP

# Log all VPN access for audit
iptables -A FORWARD -i wg0 -j LOG --log-prefix "VPN-ACCESS: " --log-level 6
```

## Network Monitoring

### Traffic Analysis Points
```
┌─────────────────────────────────────────────────────────┐
│ Monitoring Probes                                        │
│                                                         │
│ - DMZ Firewall: Mirror port → IDS/IPS                   │
│ - Industrial Firewall: NetFlow → SIEM                   │
│ - Level 3 Switch: SPAN → Packet capture                │
│ - MQTT Broker: Internal metrics → Prometheus           │
└─────────────────────────────────────────────────────────┘
```

### IDS/IPS Configuration (Suricata)
```yaml
# suricata.yaml
vars:
  address-groups:
    HOME_NET: "[10.0.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    OT_NETWORK: "[10.0.2.0/24,10.0.3.0/24,10.0.4.0/24,10.0.5.0/24]"
    IT_NETWORK: "[192.168.1.0/24,10.0.1.0/24]"

# Custom rules
alert tcp $EXTERNAL_NET any -> $OT_NETWORK any (msg:"Unauthorized external access to OT network"; sid:1000001;)
alert tcp $IT_NETWORK any -> $OT_NETWORK ![8000,8001,3000,5432] (msg:"Unauthorized IT to OT traffic"; sid:1000002;)
alert tcp $OT_NETWORK 502 -> any any (msg:"Modbus traffic to non-PLC destination"; sid:1000003;)
```

### Network Flow Monitoring
```bash
# Configure NetFlow export on routers
flow exporter SIEM
  destination 10.0.2.45
  transport udp 2055
  export-protocol netflow-v9

flow monitor OT_TRAFFIC
  exporter SIEM
  record netflow ipv4 original-input
  cache timeout active 60

interface GigabitEthernet0/1
  ip flow monitor OT_TRAFFIC input
  ip flow monitor OT_TRAFFIC output
```

## Wireless Network Considerations

### Separate Wireless Networks
```
Guest WiFi (Isolated):
  SSID: CompanyGuest
  VLAN: 192.168.100.0/24
  Access: Internet only, no internal network

Employee WiFi:
  SSID: CompanySecure
  VLAN: 192.168.1.0/24 (IT Network)
  Access: IT resources only
  Security: WPA3-Enterprise + 802.1X

OT WiFi (If absolutely necessary):
  SSID: ModaxOT (Hidden)
  VLAN: 10.0.5.0/24
  Access: Field devices only
  Security: WPA3-PSK + MAC filtering
  Isolation: Client isolation enabled
```

### Wireless Security
- Use WPA3 encryption
- Separate SSIDs for different zones
- MAC address filtering for OT WiFi
- Disable WPS
- Regular password rotation
- Client isolation enabled

## Physical Network Design

### Cabling Standards
- **Level 0-2:** Industrial Ethernet (Cat6A, shielded)
- **Level 3:** Data center grade (Cat6A)
- **Level 4-5:** Standard corporate (Cat6)
- **Fiber backbone:** Single-mode for long runs

### Redundant Paths
```
┌─────────┐         ┌─────────┐
│Switch A │◄──────►│Switch B │
│ (VLAN 3)│         │ (VLAN 3)│
└────┬────┘         └────┬────┘
     │   ┌──────────┐    │
     └──►│  Router  │◄───┘
         │          │
         └────┬─────┘
              ↓
         To other levels
```

### Power over Ethernet (PoE)
- ESP32 with PoE adapters
- PoE switches for Level 0 devices
- Backup power via UPS

## Network Documentation

### As-Built Network Diagrams
- Logical network topology
- Physical network layout
- IP address assignments
- VLAN assignments
- Firewall rule documentation
- Cable routing documentation

### Network Inventory
```csv
Device,IP,MAC,VLAN,Location,Purpose
Control-Layer-1,10.0.2.10,AA:BB:CC:DD:EE:01,1002,Rack A,Primary control
AI-Layer-1,10.0.2.11,AA:BB:CC:DD:EE:02,1002,Rack A,AI processing
MQTT-Broker,10.0.2.20,AA:BB:CC:DD:EE:03,1002,Rack A,Message broker
TimescaleDB,10.0.2.30,AA:BB:CC:DD:EE:04,1002,Rack B,Database
ESP32-001,10.0.5.101,24:0A:C4:12:34:56,1005,Line 1,Sensor device
```

## Compliance & Standards

### IEC 62443 Zones and Conduits
```
Zone: Level 5 (IT)
  Security Level: SL-1
  Conduit to Level 4: Hardened

Zone: Level 4 (Operations)
  Security Level: SL-2
  Conduit to Level 3: Secured

Zone: Level 3 (Supervisory)
  Security Level: SL-3
  Conduit to Level 2: Restricted

Zone: Level 2-0 (Control/Field)
  Security Level: SL-4
  Conduit: Isolated
```

### NIST SP 800-82 Recommendations
✅ Network segmentation implemented  
✅ Defense in depth strategy  
✅ Least privilege access  
✅ Continuous monitoring  
✅ Secure remote access  

## Implementation Roadmap

### Phase 1: Basic Segmentation (Weeks 1-2)
- [ ] Define VLANs
- [ ] Configure switches
- [ ] Implement basic firewall rules
- [ ] Document IP addressing

### Phase 2: Hardened Security (Weeks 3-4)
- [ ] Deploy industrial firewalls
- [ ] Configure port security
- [ ] Implement MAC filtering
- [ ] Set up VPN access

### Phase 3: Monitoring (Weeks 5-6)
- [ ] Deploy IDS/IPS
- [ ] Configure NetFlow
- [ ] Set up SIEM integration
- [ ] Create network dashboards

### Phase 4: Compliance (Weeks 7-8)
- [ ] Security assessment
- [ ] Penetration testing
- [ ] Documentation review
- [ ] Certification preparation

## Best Practices

### DO:
✅ Implement defense in depth  
✅ Monitor all traffic  
✅ Document all changes  
✅ Use principle of least privilege  
✅ Regularly review firewall rules  
✅ Test disaster recovery procedures  

### DON'T:
❌ Mix OT and IT networks  
❌ Allow direct internet access from OT  
❌ Use default credentials  
❌ Disable security features for convenience  
❌ Trust internal traffic by default  
❌ Forget to update network documentation  

## References
- [IEC 62443 - Industrial Security Standards](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards)
- [NIST SP 800-82 Rev. 2 - Guide to ICS Security](https://csrc.nist.gov/publications/detail/sp/800-82/rev-2/final)
- [Purdue Enterprise Reference Architecture](https://en.wikipedia.org/wiki/Purdue_Enterprise_Reference_Architecture)
- [WireGuard VPN](https://www.wireguard.com/)

---
**Last Updated:** 2024-12-06  
**Maintained By:** MODAX Network Security Team
