# MODAX Security Concept

## Overview
This document describes the comprehensive security strategy for the MODAX industrial control system. Security is critical in industrial environments where safety, data integrity, and system availability are paramount.

## Security Principles

### 1. Defense in Depth
Multiple layers of security controls to protect against various threat vectors:
- Network segmentation (OT/IT separation)
- Transport encryption
- Authentication and authorization
- Audit logging
- Input validation

### 2. Zero Trust Architecture
- All components must authenticate
- No implicit trust between layers
- Least privilege access
- Continuous verification

### 3. Safety-Security Integration
- Security measures must not compromise safety functions
- Safety-critical paths remain deterministic
- Security failures default to safe state

## Threat Model

### Attack Vectors
1. **Network Attacks**
   - MQTT message interception
   - Man-in-the-middle attacks
   - Denial of service
   - Network flooding

2. **Application Attacks**
   - API injection attacks
   - Authentication bypass
   - Privilege escalation
   - Data tampering

3. **Physical Attacks**
   - Unauthorized device access
   - Firmware manipulation
   - Hardware tampering
   - Side-channel attacks

4. **Supply Chain Attacks**
   - Compromised dependencies
   - Backdoored firmware
   - Malicious libraries

### Assets to Protect
- **Critical**: Safety system integrity, emergency stop functionality
- **High**: Sensor data integrity, control commands, system configuration
- **Medium**: Performance data, logs, AI models
- **Low**: UI preferences, temporary data

## Transport Security

### MQTT over TLS (Priority 1)

#### Current State
- ❌ Unencrypted MQTT connections
- ❌ No authentication required
- ❌ Plain text sensor data

#### Required Implementation
```python
# MQTT TLS Configuration
MQTT_TLS_ENABLED = True
MQTT_TLS_VERSION = ssl.PROTOCOL_TLSv1_2  # Minimum TLS 1.2
MQTT_CA_CERT = "/etc/modax/certs/ca.crt"
MQTT_CLIENT_CERT = "/etc/modax/certs/client.crt"
MQTT_CLIENT_KEY = "/etc/modax/certs/client.key"
MQTT_CERT_REQUIRED = ssl.CERT_REQUIRED
MQTT_TLS_INSECURE = False  # Verify server certificate
```

#### Certificate Management
- Use internal PKI or Let's Encrypt for certificates
- Certificate rotation every 90 days
- Automated renewal process
- CRL/OCSP for revocation checking

### HTTPS for REST APIs (Priority 1)

#### Required Configuration
```python
# Control Layer API (FastAPI)
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="/etc/modax/certs/api.key",
    ssl_certfile="/etc/modax/certs/api.crt",
    ssl_ca_certs="/etc/modax/certs/ca.crt"
)
```

#### API Security Headers
```python
app.add_middleware(
    Middleware,
    headers={
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'"
    }
)
```

## Authentication & Authorization

### MQTT Authentication (Priority 1)

#### Username/Password Authentication
```python
# mosquitto.conf
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

# ACL Rules (/etc/mosquitto/acl)
user control_layer
topic readwrite modax/sensor/#
topic readwrite modax/control/#
topic readwrite modax/ai/#

user field_device_001
topic write modax/sensor/data
topic read modax/control/commands

user ai_layer
topic read modax/sensor/#
topic write modax/ai/#
```

#### Token-Based Authentication (Future)
- JWT tokens for service-to-service communication
- Short-lived tokens (15 minutes)
- Refresh token mechanism
- Token revocation list

### API Authentication (Priority 1)

#### API Key Authentication
```python
# config.py
API_KEYS = {
    "hmi-client": {
        "key": os.getenv("HMI_API_KEY"),
        "permissions": ["read", "write"],
        "rate_limit": 100  # requests per minute
    },
    "monitoring": {
        "key": os.getenv("MONITORING_API_KEY"),
        "permissions": ["read"],
        "rate_limit": 1000
    }
}

# API Key Header: X-API-Key
```

#### OAuth2 Integration (Future)
- OpenID Connect for user authentication
- Integration with corporate SSO
- Fine-grained permission scopes
- Multi-factor authentication support

### Role-Based Access Control (RBAC)

#### Roles
1. **Administrator**
   - Full system access
   - Configuration changes
   - User management
   - Security settings

2. **Operator**
   - Monitor system status
   - Execute pre-approved commands
   - View AI recommendations
   - Acknowledge alarms

3. **Maintenance**
   - View diagnostic data
   - Reset wear counters
   - Update AI models
   - Access logs

4. **Read-Only**
   - View dashboards
   - Read sensor data
   - View historical data
   - No control commands

#### Permission Matrix
| Resource | Admin | Operator | Maintenance | Read-Only |
|----------|-------|----------|-------------|-----------|
| System Config | RW | R | R | R |
| Control Commands | RW | RW* | R | - |
| Sensor Data | RW | RW | R | R |
| AI Models | RW | R | RW | R |
| User Management | RW | - | - | - |
| Audit Logs | RW | R | R | R |

*Operator: Only pre-approved safe commands

## Audit Logging (Priority 1)

### Security Event Categories

#### Authentication Events
```python
{
    "timestamp": "2024-12-06T21:19:21.971Z",
    "event_type": "authentication",
    "severity": "INFO",
    "source_ip": "192.168.1.100",
    "user": "operator1",
    "action": "login_success",
    "metadata": {
        "method": "api_key",
        "user_agent": "MODAX-HMI/1.0"
    }
}
```

#### Authorization Events
```python
{
    "timestamp": "2024-12-06T21:19:21.971Z",
    "event_type": "authorization",
    "severity": "WARNING",
    "user": "operator1",
    "action": "access_denied",
    "resource": "/control/emergency-stop",
    "reason": "insufficient_permissions"
}
```

#### Control Command Events
```python
{
    "timestamp": "2024-12-06T21:19:21.971Z",
    "event_type": "control_command",
    "severity": "WARNING",
    "user": "operator1",
    "device_id": "esp32_001",
    "command": "motor_start",
    "status": "blocked",
    "reason": "safety_interlock_active"
}
```

#### Configuration Change Events
```python
{
    "timestamp": "2024-12-06T21:19:21.971Z",
    "event_type": "configuration_change",
    "severity": "INFO",
    "user": "admin1",
    "parameter": "AI_LAYER_TIMEOUT",
    "old_value": "5",
    "new_value": "10",
    "reason": "network_latency_adjustment"
}
```

### Audit Log Requirements
- **Immutability**: Logs cannot be modified after creation
- **Integrity**: Cryptographic signatures or write-once storage
- **Retention**: Minimum 1 year for compliance
- **Separation**: Audit logs on separate system/storage
- **Monitoring**: Real-time alerting on critical events

### Log Storage
```python
# Structured logging to file and SIEM
import logging
import json

class SecurityAuditHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            "timestamp": record.created,
            "event_type": record.event_type,
            "severity": record.levelname,
            "user": getattr(record, 'user', 'system'),
            "action": record.msg,
            "metadata": getattr(record, 'metadata', {})
        }
        # Write to SIEM, Elasticsearch, or file
        self.write_to_audit_store(log_entry)
```

## Secrets Management (Priority 1)

### Current Issues
- ❌ Passwords in configuration files
- ❌ API keys in environment variables
- ❌ TLS certificates without encryption
- ❌ No secret rotation

### Recommended Solution: HashiCorp Vault

#### Architecture
```
Applications → Vault Agent → Vault Server → Encrypted Storage
                  ↓
              Dynamic Secrets
              Lease Management
              Auto-Rotation
```

#### Implementation
```python
# vault_client.py
import hvac

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_mqtt_credentials(self):
        secret = self.client.secrets.kv.v2.read_secret_version(
            path='mqtt/credentials'
        )
        return {
            'username': secret['data']['data']['username'],
            'password': secret['data']['data']['password']
        }
    
    def get_tls_certificates(self, component):
        pki = self.client.secrets.pki
        cert = pki.generate_certificate(
            name=f'modax-{component}',
            common_name=f'{component}.modax.local'
        )
        return cert
```

### Alternative: Environment Variable Encryption
For simpler deployments without Vault:
```bash
# Use encrypted .env files
sops -e .env > .env.encrypted
sops -d .env.encrypted > .env
```

## Input Validation & Sanitization

### API Input Validation

#### Pydantic Models
```python
from pydantic import BaseModel, Field, validator

class ControlCommand(BaseModel):
    device_id: str = Field(..., regex=r'^esp32_[0-9]{3}$')
    command: str = Field(..., regex=r'^[a-z_]+$')
    parameters: dict = Field(default_factory=dict)
    
    @validator('command')
    def validate_command(cls, v):
        allowed_commands = [
            'motor_start', 'motor_stop',
            'set_speed', 'reset_wear'
        ]
        if v not in allowed_commands:
            raise ValueError(f'Invalid command: {v}')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        if values.get('command') == 'set_speed':
            if 'speed' not in v:
                raise ValueError('Speed parameter required')
            if not 0 <= v['speed'] <= 100:
                raise ValueError('Speed must be 0-100')
        return v
```

### MQTT Message Validation
```python
import json
from jsonschema import validate, ValidationError

SENSOR_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "device_id": {"type": "string", "pattern": "^esp32_[0-9]{3}$"},
        "timestamp": {"type": "number"},
        "current": {"type": "number", "minimum": 0, "maximum": 20},
        "vibration": {"type": "number", "minimum": 0, "maximum": 1000},
        "temperature": {"type": "number", "minimum": -40, "maximum": 125}
    },
    "required": ["device_id", "timestamp", "current", "vibration", "temperature"]
}

def validate_sensor_message(payload):
    try:
        data = json.loads(payload)
        validate(instance=data, schema=SENSOR_DATA_SCHEMA)
        return data
    except (json.JSONDecodeError, ValidationError) as e:
        logging.error(f"Invalid sensor data: {e}")
        return None
```

## Network Security

### Network Segmentation

#### Recommended Topology
```
┌─────────────────────────────────────────────────────┐
│ Office Network (IT)                                  │
│ - HMI Clients                                       │
│ - Monitoring Dashboards                             │
│ - Corporate Systems                                 │
└────────────────┬────────────────────────────────────┘
                 │ Firewall (DMZ)
                 │ - Allow: HTTPS (8000, 8001)
                 │ - Block: MQTT, SSH
┌────────────────┴────────────────────────────────────┐
│ Control Network (OT)                                 │
│ - Control Layer                                     │
│ - AI Layer                                          │
│ - MQTT Broker                                       │
│ - Time-series Database                              │
└────────────────┬────────────────────────────────────┘
                 │ Industrial Firewall
                 │ - Allow: MQTT (ESP32 → Broker)
                 │ - Block: Internet access
┌────────────────┴────────────────────────────────────┐
│ Field Network (Isolated OT)                         │
│ - ESP32 Devices                                     │
│ - Industrial Sensors                                │
│ - Safety PLCs                                       │
└─────────────────────────────────────────────────────┘
```

#### Firewall Rules (iptables)
```bash
# Control Network → Field Network (MQTT only)
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.0/24 -p tcp --dport 8883 -j ACCEPT
iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.0/24 -j DROP

# Office Network → Control Network (HTTPS API only)
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.1.0/24 -p tcp --dport 8000 -j ACCEPT
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.1.0/24 -p tcp --dport 8001 -j ACCEPT
iptables -A FORWARD -s 192.168.1.0/24 -d 10.0.1.0/24 -j DROP

# Block all from Field Network to Internet
iptables -A FORWARD -s 10.0.2.0/24 ! -d 10.0.0.0/8 -j DROP
```

### VPN Access
For remote maintenance:
```yaml
# WireGuard Configuration
[Interface]
PrivateKey = <admin-private-key>
Address = 10.0.3.2/24

[Peer]
PublicKey = <modax-server-public-key>
Endpoint = modax-gateway.company.com:51820
AllowedIPs = 10.0.1.0/24, 10.0.2.0/24
PersistentKeepalive = 25
```

## Vulnerability Management

### Dependency Scanning

#### Python Dependencies
```bash
# Check for known vulnerabilities
pip-audit

# Continuous monitoring
safety check --json
snyk test --all-projects
```

#### Container Scanning
```bash
# Scan Docker images
trivy image modax-control-layer:latest
grype modax-ai-layer:latest
```

#### Static Code Analysis
```bash
# Python security linting
bandit -r python-control-layer/
semgrep --config=p/security-audit python-ai-layer/

# C# security analysis
dotnet tool install --global security-scan
security-scan csharp-hmi-layer/
```

### Patch Management
- **Critical vulnerabilities**: Patch within 24 hours
- **High severity**: Patch within 7 days
- **Medium severity**: Patch within 30 days
- **Low severity**: Patch during regular maintenance

### CVE Monitoring
- Subscribe to security advisories for all dependencies
- Automated vulnerability scanning in CI/CD pipeline
- Regular security reviews (quarterly)

## Incident Response

### Security Incident Classification

#### Critical (P1)
- Unauthorized control command execution
- Safety system compromise
- Data exfiltration detected
- Ransomware/malware infection
**Response Time**: Immediate (< 15 minutes)

#### High (P2)
- Authentication bypass attempt
- Privilege escalation detected
- DDoS attack
- Multiple failed login attempts
**Response Time**: < 1 hour

#### Medium (P3)
- Suspicious network traffic
- Policy violation
- Outdated certificates
**Response Time**: < 4 hours

#### Low (P4)
- Failed login (single)
- Configuration drift
- Log anomalies
**Response Time**: < 24 hours

### Incident Response Procedures

#### 1. Detection & Analysis
- Automated alerts from SIEM
- Manual reports from operators
- Anomaly detection systems
- Log correlation

#### 2. Containment
- Isolate affected systems
- Block compromised accounts
- Revoke certificates/keys
- Enable enhanced logging

#### 3. Eradication
- Remove malware/backdoors
- Close security gaps
- Update affected systems
- Reset compromised credentials

#### 4. Recovery
- Restore from clean backups
- Verify system integrity
- Resume normal operations
- Enhanced monitoring period

#### 5. Post-Incident
- Document incident details
- Root cause analysis
- Update security controls
- Team debriefing

### Emergency Contacts
```yaml
Security Team:
  Primary: security@company.com
  Phone: +1-XXX-XXX-XXXX (24/7)

System Administrator:
  Primary: sysadmin@company.com
  Phone: +1-XXX-XXX-XXXX

Management:
  CTO: cto@company.com
  CISO: ciso@company.com
```

## Compliance & Standards

### Applicable Standards
- **IEC 62443**: Industrial automation and control systems security
- **NIST SP 800-82**: Guide to Industrial Control Systems Security
- **ISO/IEC 27001**: Information security management
- **GDPR**: Data protection (if applicable)

### Compliance Checklist

#### IEC 62443 Requirements
- [ ] Security level assessment completed
- [ ] Risk assessment documented
- [ ] Security policies defined
- [ ] Access control implemented
- [ ] Data integrity protection
- [ ] Audit logging enabled
- [ ] Incident response plan
- [ ] Security testing performed

#### NIST SP 800-82 Guidelines
- [ ] Asset inventory maintained
- [ ] Network segmentation implemented
- [ ] Security monitoring active
- [ ] Patch management process
- [ ] Backup and recovery tested
- [ ] Personnel security training
- [ ] Vendor security assessment

## Security Roadmap

### Phase 1: Foundation (Priority 1)
- [ ] Implement MQTT over TLS
- [ ] Enable HTTPS for all APIs
- [ ] Add MQTT authentication
- [ ] Implement audit logging
- [ ] Set up secrets management
- [ ] Basic input validation

**Timeline**: 2-4 weeks
**Effort**: 40-60 hours

### Phase 2: Enhanced Controls
- [ ] Role-based access control
- [ ] API authentication (OAuth2)
- [ ] Network segmentation
- [ ] Vulnerability scanning automation
- [ ] Security monitoring dashboard
- [ ] Incident response procedures

**Timeline**: 4-6 weeks
**Effort**: 60-80 hours

### Phase 3: Advanced Security
- [ ] Web Application Firewall (WAF)
- [ ] Intrusion Detection System (IDS)
- [ ] Security Information and Event Management (SIEM)
- [ ] Penetration testing
- [ ] Security certification (IEC 62443)
- [ ] Bug bounty program

**Timeline**: 8-12 weeks
**Effort**: 120+ hours

## Security Testing

### Regular Testing Schedule
- **Daily**: Automated vulnerability scanning
- **Weekly**: Security log review
- **Monthly**: Access control audit
- **Quarterly**: Penetration testing
- **Annually**: Comprehensive security audit

### Testing Tools
```bash
# Port scanning
nmap -sV -sC 10.0.1.0/24

# Web vulnerability scanning
nikto -h https://modax-api.local:8000

# API security testing
zap-cli quick-scan https://modax-api.local:8000

# TLS configuration testing
testssl.sh modax-mqtt.local:8883
```

## Security Training

### Personnel Training Requirements
1. **All Users**
   - Security awareness basics
   - Password best practices
   - Phishing recognition
   - Incident reporting

2. **Operators**
   - Safe command execution
   - Anomaly recognition
   - Emergency procedures
   - Access control procedures

3. **Administrators**
   - Secure configuration
   - Log analysis
   - Incident response
   - Compliance requirements

4. **Developers**
   - Secure coding practices
   - Threat modeling
   - Security testing
   - Vulnerability remediation

### Training Schedule
- Initial training: Before system access
- Refresher training: Annually
- Incident-specific training: As needed
- New feature training: With each major release

## Conclusion

Security is not a one-time implementation but an ongoing process. This document provides the foundation for securing the MODAX system, but must be regularly reviewed and updated as threats evolve and the system grows.

**Next Steps**:
1. Conduct security risk assessment
2. Prioritize implementation based on risk
3. Allocate resources for Phase 1 implementation
4. Establish security review process
5. Schedule regular security audits

## References
- IEC 62443-3-3: System security requirements and security levels
- NIST SP 800-82 Rev. 2: Guide to Industrial Control Systems (ICS) Security
- OWASP Top 10 for APIs
- CIS Controls for Industrial Control Systems
- MQTT Security Fundamentals (HiveMQ)
