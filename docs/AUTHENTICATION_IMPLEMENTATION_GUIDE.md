# MODAX Authentication Implementation Guide

This guide provides step-by-step instructions for implementing authentication in MODAX for both MQTT and API layers.

**Last Updated:** 2025-12-09  
**Related Documents:** [SECURITY.md](SECURITY.md), [CONFIGURATION.md](CONFIGURATION.md)

## Overview

MODAX supports multiple authentication mechanisms:
- **MQTT Authentication:** Username/Password and TLS client certificates
- **API Authentication:** API Keys and JWT tokens (future)
- **Secrets Management:** Environment variables and secrets management systems

## MQTT Authentication Implementation

### Step 1: Configure MQTT Broker with Authentication

#### Option A: Mosquitto with Password File

1. Create a password file:
```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd modax_user

# Add additional users
sudo mosquitto_passwd /etc/mosquitto/passwd another_user
```

2. Configure Mosquitto (`/etc/mosquitto/mosquitto.conf`):
```conf
# Basic configuration
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

# ACL configuration (optional)
acl_file /etc/mosquitto/acl.conf
```

3. Create ACL file (`/etc/mosquitto/acl.conf`):
```conf
# Control layer can publish/subscribe to all topics
user modax_control
topic readwrite #

# Field devices can only publish sensor data
user modax_device
topic write modax/sensor/+
topic write modax/sensor/safety

# AI layer can subscribe to sensor data and publish analysis
user modax_ai
topic read modax/sensor/+
topic write modax/ai/analysis
```

4. Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

#### Option B: Mosquitto with TLS Client Certificates

1. Generate certificates (see [SECURITY.md](SECURITY.md) for details)

2. Configure Mosquitto with TLS:
```conf
listener 8883
protocol mqtt

# TLS configuration
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate true
use_identity_as_username true

# Optional: also use password authentication
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### Step 2: Configure MODAX Components for MQTT Authentication

#### Control Layer Configuration

Set environment variables:
```bash
# Basic authentication
export MQTT_BROKER_HOST=localhost
export MQTT_BROKER_PORT=1883
export MQTT_USERNAME=modax_control
export MQTT_PASSWORD=your_secure_password

# TLS authentication
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/modax/certs/ca.crt
export MQTT_CERTFILE=/etc/modax/certs/control-client.crt
export MQTT_KEYFILE=/etc/modax/certs/control-client.key
```

Or update `python-control-layer/config.py`:
```python
@dataclass
class MQTTConfig:
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    username: Optional[str] = os.getenv("MQTT_USERNAME")
    password: Optional[str] = os.getenv("MQTT_PASSWORD")
    use_tls: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    ca_certs: Optional[str] = os.getenv("MQTT_CA_CERTS")
    certfile: Optional[str] = os.getenv("MQTT_CERTFILE")
    keyfile: Optional[str] = os.getenv("MQTT_KEYFILE")
```

#### ESP32 Field Layer Configuration

Update `esp32-field-layer/config.h`:
```cpp
// MQTT Authentication
#define MQTT_USERNAME "modax_device"
#define MQTT_PASSWORD "your_secure_password"

// TLS Configuration (if using certificates)
#define MQTT_USE_TLS true
const char* mqtt_ca_cert = \
"-----BEGIN CERTIFICATE-----\n" \
"MIIDXTCCAkWgAwIBAgIJAK...\n" \
"-----END CERTIFICATE-----\n";
```

#### AI Layer Configuration

Set environment variables:
```bash
export MQTT_USERNAME=modax_ai
export MQTT_PASSWORD=your_secure_password
```

### Step 3: Verify MQTT Authentication

Test connectivity:
```bash
# Test with mosquitto_sub (should fail without auth)
mosquitto_sub -h localhost -t "modax/#" -v

# Test with credentials (should succeed)
mosquitto_sub -h localhost -t "modax/#" -u modax_control -P your_password -v

# Test with TLS
mosquitto_sub -h localhost -p 8883 -t "modax/#" \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /path/to/client.crt \
  --key /path/to/client.key -v
```

## API Authentication Implementation

### Step 1: Enable API Authentication

#### Control Layer API

1. Set environment variables:
```bash
export API_KEY_ENABLED=true
export API_KEY=your-secret-api-key-here-min-32-chars
```

2. The API will automatically require authentication for all endpoints

3. Test API access:
```bash
# Without API key (should fail with 401)
curl http://localhost:8000/api/v1/status

# With API key (should succeed)
curl -H "X-API-Key: your-secret-api-key-here" \
  http://localhost:8000/api/v1/status
```

#### AI Layer API

Similar configuration:
```bash
export API_KEY_ENABLED=true
export API_KEY=your-ai-api-key-here-min-32-chars
```

### Step 2: Generate Strong API Keys

Use cryptographically secure methods:

```python
# Python
import secrets
api_key = secrets.token_urlsafe(32)
print(f"API_KEY={api_key}")
```

```bash
# Linux
openssl rand -base64 32
```

### Step 3: Configure HMI to Use API Key

Update `csharp-hmi-layer/Services/ControlLayerClient.cs`:

```csharp
private readonly HttpClient _httpClient;
private readonly string _apiKey;

public ControlLayerClient()
{
    _httpClient = new HttpClient();
    _apiKey = Environment.GetEnvironmentVariable("MODAX_API_KEY") ?? "";
    
    if (!string.IsNullOrEmpty(_apiKey))
    {
        _httpClient.DefaultRequestHeaders.Add("X-API-Key", _apiKey);
    }
}
```

Set environment variable for HMI:
```bash
export MODAX_API_KEY=your-secret-api-key-here
```

### Step 4: Implement Role-Based Access Control (RBAC)

The system already has basic RBAC implemented. To use it:

1. Control commands require the "control" role:
```python
from auth import require_control

@app.post("/api/v1/cnc/start")
async def start_cnc(api_key: str = Depends(require_control)):
    # Only users with 'control' role can access this
    ...
```

2. Read-only access uses `get_api_key`:
```python
from auth import get_api_key

@app.get("/api/v1/status")
async def get_status(api_key: str = Depends(get_api_key)):
    # Any authenticated user can access this
    ...
```

## Secrets Management

### Option 1: Environment Variables (Simple)

For development and simple deployments:
```bash
# .env file (DO NOT COMMIT!)
MQTT_USERNAME=modax_control
MQTT_PASSWORD=secure_password
API_KEY=your-api-key-here
```

Load in Docker Compose:
```yaml
services:
  control-layer:
    env_file:
      - .env
```

### Option 2: Docker Secrets (Recommended for Production)

1. Create secrets:
```bash
echo "modax_control" | docker secret create mqtt_username -
echo "secure_password" | docker secret create mqtt_password -
echo "your-api-key" | docker secret create api_key -
```

2. Use in Docker Compose:
```yaml
services:
  control-layer:
    secrets:
      - mqtt_username
      - mqtt_password
      - api_key
    environment:
      - MQTT_USERNAME_FILE=/run/secrets/mqtt_username
      - MQTT_PASSWORD_FILE=/run/secrets/mqtt_password
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  mqtt_username:
    external: true
  mqtt_password:
    external: true
  api_key:
    external: true
```

3. Update code to read from files:
```python
def read_secret(env_var_name: str, default: str = "") -> str:
    """Read secret from file if *_FILE env var exists, otherwise from env var"""
    file_path = os.getenv(f"{env_var_name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()
    return os.getenv(env_var_name, default)

# Usage
mqtt_username = read_secret("MQTT_USERNAME")
mqtt_password = read_secret("MQTT_PASSWORD")
api_key = read_secret("API_KEY")
```

### Option 3: HashiCorp Vault (Enterprise)

For large-scale deployments with centralized secrets management:

1. Configure Vault:
```bash
vault secrets enable -path=modax kv-v2
vault kv put modax/mqtt username=modax_control password=secure_password
vault kv put modax/api key=your-api-key
```

2. Integrate with MODAX:
```python
import hvac

client = hvac.Client(url='http://vault:8200', token=os.getenv('VAULT_TOKEN'))
mqtt_secrets = client.secrets.kv.v2.read_secret_version(path='mqtt', mount_point='modax')
mqtt_username = mqtt_secrets['data']['data']['username']
mqtt_password = mqtt_secrets['data']['data']['password']
```

## Security Best Practices

### 1. Credential Rotation

Regularly rotate credentials:
- MQTT passwords: Every 90 days
- API keys: Every 180 days
- TLS certificates: Before expiration

### 2. Strong Passwords

Requirements:
- Minimum 16 characters
- Mix of upper/lowercase, numbers, symbols
- No dictionary words
- Unique per service

### 3. Audit Logging

Monitor authentication events:
```python
from security_audit import get_security_audit_logger

audit_logger = get_security_audit_logger()

# Log authentication attempts
audit_logger.log_auth_attempt(username, success=True)
audit_logger.log_auth_attempt(username, success=False, reason="Invalid password")
```

### 4. Rate Limiting

Protect against brute force:
- API rate limiting already implemented (slowapi)
- MQTT connection limits in broker config
- Automatic blocking after failed attempts

### 5. Network Segmentation

- Separate OT and IT networks
- Firewall rules between layers
- VLANs for different components

## Testing Authentication

### Automated Tests

Run security tests:
```bash
cd python-control-layer
python -m pytest test_auth.py -v
python -m pytest test_security_audit.py -v
```

### Manual Testing

#### Test MQTT Authentication
```bash
# Should fail without credentials
mosquitto_pub -h localhost -t test -m "hello"

# Should succeed with credentials
mosquitto_pub -h localhost -t test -m "hello" -u modax_control -P password

# Should fail with wrong credentials
mosquitto_pub -h localhost -t test -m "hello" -u wrong -P wrong
```

#### Test API Authentication
```bash
# Should return 401 without API key
curl -v http://localhost:8000/api/v1/status

# Should return 200 with valid API key
curl -v -H "X-API-Key: your-key" http://localhost:8000/api/v1/status

# Should return 401 with invalid API key
curl -v -H "X-API-Key: wrong-key" http://localhost:8000/api/v1/status
```

## Troubleshooting

### Common Issues

#### MQTT Connection Refused
- Check username/password are correct
- Verify user exists in password file
- Check ACL permissions
- Review Mosquitto logs: `sudo journalctl -u mosquitto -f`

#### API Authentication Failures
- Verify API_KEY_ENABLED=true
- Check API key length (minimum 32 characters)
- Ensure X-API-Key header is sent
- Check for typos in environment variables

#### TLS Certificate Errors
- Verify certificate paths are correct
- Check certificate validity: `openssl x509 -in cert.crt -text -noout`
- Ensure CA certificate is trusted
- Check file permissions (readable by application)

#### Permission Denied Errors
- Review ACL configuration
- Check user has required permissions
- Verify topic patterns match

## References

- [SECURITY.md](SECURITY.md) - Comprehensive security concept
- [CONFIGURATION.md](CONFIGURATION.md) - All configuration options
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting
- [Mosquitto Authentication](https://mosquitto.org/man/mosquitto-conf-5.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Support

For security issues or questions:
- Review existing documentation
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open a GitHub issue (non-security)
- Contact security team for vulnerabilities (private disclosure)
