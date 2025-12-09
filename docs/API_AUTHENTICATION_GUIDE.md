# MODAX API Authentication Guide

This guide explains how to enable, configure, and use authentication for MODAX REST APIs.

**Last Updated:** 2025-12-09  
**Version:** 0.2.0  
**Status:** Production Ready

## Overview

MODAX supports API Key authentication for securing REST endpoints. Authentication is **optional** but **highly recommended** for production deployments.

### Features

- ✅ API Key-based authentication
- ✅ Multiple API keys with different permissions
- ✅ Role-based access control (read, write, control, admin)
- ✅ Per-key rate limiting
- ✅ Audit logging of API access
- ✅ Easy to enable/disable

---

## Quick Start

### 1. Enable Authentication

Set environment variable:

```bash
# Control Layer
export API_KEY_ENABLED=true

# Generate strong API keys
export HMI_API_KEY="your-secret-hmi-key-here"
export MONITORING_API_KEY="your-secret-monitoring-key-here"
export ADMIN_API_KEY="your-secret-admin-key-here"
```

### 2. Use API Key in Requests

Include API key in request header:

```bash
curl -H "X-API-Key: your-secret-hmi-key-here" \
  https://api.modax.example.com/api/v1/status
```

### 3. Verify Authentication

Test without API key (should fail):
```bash
curl https://api.modax.example.com/api/v1/status
# Response: {"error": "API key is missing", "status_code": 401}
```

Test with valid API key (should succeed):
```bash
curl -H "X-API-Key: your-secret-hmi-key-here" \
  https://api.modax.example.com/api/v1/status
# Response: {"status": "ok", ...}
```

---

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `API_KEY_ENABLED` | No | Enable/disable authentication | `false` |
| `HMI_API_KEY` | If enabled | API key for HMI clients | - |
| `MONITORING_API_KEY` | If enabled | API key for monitoring (read-only) | - |
| `ADMIN_API_KEY` | If enabled | API key for admin operations | - |

### Docker Compose

```yaml
services:
  control-layer:
    environment:
      - API_KEY_ENABLED=true
      - HMI_API_KEY=${HMI_API_KEY}
      - MONITORING_API_KEY=${MONITORING_API_KEY}
      - ADMIN_API_KEY=${ADMIN_API_KEY}
```

Store keys in `.env` file:

```bash
# .env file
API_KEY_ENABLED=true
HMI_API_KEY=hmi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MONITORING_API_KEY=mon_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_API_KEY=adm_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Kubernetes

Create secret:

```bash
kubectl create secret generic modax-api-keys \
  --from-literal=hmi-api-key='hmi_xxxxx...' \
  --from-literal=monitoring-api-key='mon_xxxxx...' \
  --from-literal=admin-api-key='adm_xxxxx...' \
  -n modax
```

Reference in deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-layer
spec:
  template:
    spec:
      containers:
      - name: control-layer
        env:
        - name: API_KEY_ENABLED
          value: "true"
        - name: HMI_API_KEY
          valueFrom:
            secretKeyRef:
              name: modax-api-keys
              key: hmi-api-key
        - name: MONITORING_API_KEY
          valueFrom:
            secretKeyRef:
              name: modax-api-keys
              key: monitoring-api-key
        - name: ADMIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: modax-api-keys
              key: admin-api-key
```

---

## Permission Model

### Permission Levels

| Permission | Description | Typical Use |
|------------|-------------|-------------|
| `read` | View data, no modifications | Monitoring, dashboards, BI tools |
| `write` | Modify data, configurations | HMI, admin tools |
| `control` | Send control commands, emergency stop | HMI, automation systems |
| `admin` | Full access, administrative functions | System administrators |

### API Key Types

#### 1. HMI API Key

**Permissions:** `read`, `write`, `control`

**Use Cases:**
- Human-Machine Interface applications
- Operator consoles
- Control panels

**Endpoints Access:**
- ✅ GET `/api/v1/status`
- ✅ GET `/api/v1/devices`
- ✅ POST `/api/v1/control/command`
- ✅ POST `/api/v1/cnc/emergency-stop`
- ❌ POST `/api/v1/admin/*` (admin only)

#### 2. Monitoring API Key

**Permissions:** `read` only

**Use Cases:**
- Prometheus scraping
- Grafana dashboards
- External monitoring systems
- Business intelligence tools

**Endpoints Access:**
- ✅ GET `/api/v1/status`
- ✅ GET `/api/v1/devices`
- ✅ GET `/metrics`
- ❌ POST endpoints (read-only)

**Rate Limit:** 1000 requests/minute (higher than standard)

#### 3. Admin API Key

**Permissions:** `read`, `write`, `control`, `admin`

**Use Cases:**
- System administration
- Configuration changes
- User management (future)

**Endpoints Access:**
- ✅ All endpoints
- ✅ Administrative functions

---

## API Key Management

### Generating Secure API Keys

Use cryptographically secure random generation:

```python
import secrets
import hashlib

def generate_api_key(prefix="api"):
    """Generate a secure API key"""
    # Generate 32 random bytes
    random_bytes = secrets.token_bytes(32)
    # Convert to hex
    key = random_bytes.hex()
    # Add prefix for identification
    return f"{prefix}_{key}"

# Generate keys
hmi_key = generate_api_key("hmi")
monitoring_key = generate_api_key("mon")
admin_key = generate_api_key("adm")

print(f"HMI_API_KEY={hmi_key}")
print(f"MONITORING_API_KEY={monitoring_key}")
print(f"ADMIN_API_KEY={admin_key}")
```

```bash
# Or use OpenSSL
openssl rand -hex 32
```

### Key Rotation

Rotate API keys regularly (recommended: every 90 days):

1. Generate new API keys
2. Update `.env` file or secrets
3. Restart services
4. Update client applications
5. Verify all clients working
6. Revoke old keys

**Zero-downtime rotation:**

During transition period, accept both old and new keys:

```bash
# Add new keys with _NEW suffix
HMI_API_KEY_NEW=hmi_new_key_here
MONITORING_API_KEY_NEW=mon_new_key_here

# Update clients gradually
# After all clients updated, remove old keys
```

### Revoking Keys

To revoke a compromised key:

1. Remove key from environment variables
2. Restart Control Layer service
3. Key immediately becomes invalid
4. Generate and distribute new key

---

## Client Implementation

### Python Client

```python
import requests

class ModaxAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
    
    def get_status(self):
        response = self.session.get(f"{self.base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()
    
    def get_devices(self):
        response = self.session.get(f"{self.base_url}/api/v1/devices")
        response.raise_for_status()
        return response.json()
    
    def send_command(self, device_id, command):
        response = self.session.post(
            f"{self.base_url}/api/v1/control/command",
            json={"device_id": device_id, "command": command}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ModaxAPIClient(
    "https://api.modax.example.com",
    "hmi_xxxxxxxxxxxxxxxxxxxxx"
)

status = client.get_status()
print(f"System Status: {status['system_safe']}")
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class ModaxAPIClient {
  constructor(baseUrl, apiKey) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      }
    });
  }
  
  async getStatus() {
    const response = await this.client.get('/api/v1/status');
    return response.data;
  }
  
  async getDevices() {
    const response = await this.client.get('/api/v1/devices');
    return response.data;
  }
  
  async sendCommand(deviceId, command) {
    const response = await this.client.post('/api/v1/control/command', {
      device_id: deviceId,
      command: command
    });
    return response.data;
  }
}

// Usage
const client = new ModaxAPIClient(
  'https://api.modax.example.com',
  'hmi_xxxxxxxxxxxxxxxxxxxxx'
);

client.getStatus()
  .then(status => console.log('System Status:', status.system_safe))
  .catch(error => console.error('Error:', error.message));
```

### C# Client

```csharp
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;

public class ModaxAPIClient
{
    private readonly HttpClient _httpClient;
    
    public ModaxAPIClient(string baseUrl, string apiKey)
    {
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(baseUrl)
        };
        _httpClient.DefaultRequestHeaders.Add("X-API-Key", apiKey);
        _httpClient.DefaultRequestHeaders.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/json"));
    }
    
    public async Task<SystemStatus> GetStatusAsync()
    {
        var response = await _httpClient.GetAsync("/api/v1/status");
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<SystemStatus>(content);
    }
    
    public async Task<Device[]> GetDevicesAsync()
    {
        var response = await _httpClient.GetAsync("/api/v1/devices");
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<Device[]>(content);
    }
}

// Usage
var client = new ModaxAPIClient(
    "https://api.modax.example.com",
    "hmi_xxxxxxxxxxxxxxxxxxxxx"
);

var status = await client.GetStatusAsync();
Console.WriteLine($"System Safe: {status.SystemSafe}");
```

---

## Error Handling

### Authentication Errors

#### 401 Unauthorized - Missing API Key

**Request:**
```bash
curl https://api.modax.example.com/api/v1/status
```

**Response:**
```json
{
  "error": "HTTPException",
  "message": "API key is missing",
  "status_code": 401,
  "timestamp": "2025-12-09T10:00:00.000000",
  "details": {
    "path": "/api/v1/status",
    "method": "GET"
  }
}
```

**Solution:** Include `X-API-Key` header

#### 401 Unauthorized - Invalid API Key

**Request:**
```bash
curl -H "X-API-Key: invalid_key" \
  https://api.modax.example.com/api/v1/status
```

**Response:**
```json
{
  "error": "HTTPException",
  "message": "Invalid API key",
  "status_code": 401,
  "timestamp": "2025-12-09T10:00:00.000000"
}
```

**Solution:** Use valid API key

#### 403 Forbidden - Insufficient Permissions

**Request:**
```bash
curl -H "X-API-Key: monitoring_key" \
  -X POST https://api.modax.example.com/api/v1/control/command \
  -d '{"device_id": "cnc-01", "command": "start"}'
```

**Response:**
```json
{
  "error": "HTTPException",
  "message": "Insufficient permissions: 'control' required",
  "status_code": 403,
  "timestamp": "2025-12-09T10:00:00.000000"
}
```

**Solution:** Use API key with appropriate permissions (HMI or Admin key)

---

## Security Best Practices

### 1. Never Hardcode API Keys

❌ **Bad:**
```python
api_key = "hmi_12345678..."  # Hardcoded
```

✅ **Good:**
```python
import os
api_key = os.environ.get("MODAX_API_KEY")
if not api_key:
    raise ValueError("MODAX_API_KEY environment variable not set")
```

### 2. Use HTTPS in Production

❌ **Bad:**
```bash
API_URL=http://api.modax.example.com  # Unencrypted
```

✅ **Good:**
```bash
API_URL=https://api.modax.example.com  # TLS encrypted
```

### 3. Rotate Keys Regularly

Set up automated key rotation:

```python
# Example: Monthly key rotation reminder
from datetime import datetime, timedelta

KEY_CREATION_DATE = datetime(2025, 12, 1)
ROTATION_INTERVAL = timedelta(days=90)

if datetime.now() > KEY_CREATION_DATE + ROTATION_INTERVAL:
    print("WARNING: API key should be rotated!")
```

### 4. Monitor for Suspicious Activity

Enable audit logging and monitor for:
- Repeated authentication failures
- Unusual request patterns
- Access from unexpected IPs
- High request rates

### 5. Use Least Privilege

Give clients minimum necessary permissions:

| Client Type | Key Type |
|-------------|----------|
| Dashboard | Monitoring (read-only) |
| HMI Operator | HMI (read/write/control) |
| Admin Console | Admin (full access) |
| Prometheus | Monitoring (read-only) |

---

## Troubleshooting

### Authentication Not Working

**Symptom:** Requests succeed without API key even when `API_KEY_ENABLED=true`

**Possible Causes:**
1. Environment variable not loaded
2. Service not restarted after config change
3. Using old deployment

**Solution:**
```bash
# Verify environment variable is set
kubectl exec -it <pod-name> -- env | grep API_KEY_ENABLED

# Restart service
kubectl rollout restart deployment/control-layer
```

### Monitoring API Key Has Wrong Permissions

**Symptom:** Monitoring key can send control commands

**Solution:** Verify key is loaded correctly:
```python
# In control_api.py, add logging
logger.info(f"Loaded API keys: {list(api_key_manager.api_keys.keys())[:3]}...")
```

### Performance Impact

**Q:** Does authentication add latency?

**A:** Minimal impact (~1-2ms per request). Use connection pooling to amortize overhead.

---

## Migration Guide

### Enabling Authentication on Existing Deployment

1. **Generate API keys:**
```bash
./scripts/generate-api-keys.sh > .env.production
```

2. **Distribute keys to clients:**
```bash
# Update HMI configuration
# Update monitoring tools
# Update integration systems
```

3. **Enable authentication in canary deployment:**
```bash
# Deploy to 10% of pods first
kubectl set env deployment/control-layer \
  API_KEY_ENABLED=true \
  -n modax
kubectl scale deployment/control-layer --replicas=1
```

4. **Monitor for errors:**
```bash
kubectl logs -f deployment/control-layer | grep "401\|403"
```

5. **Roll out to all pods:**
```bash
kubectl scale deployment/control-layer --replicas=10
```

6. **Verify all clients working:**
```bash
# Check Grafana dashboards
# Verify HMI connectivity
# Test integrations
```

---

## API Reference

### Authentication Endpoints

All endpoints except `/health` require authentication when `API_KEY_ENABLED=true`.

**Excluded endpoints (no auth required):**
- `GET /health`
- `GET /ready`

**Included endpoints (auth required):**
- `GET /api/v1/*`
- `POST /api/v1/*`
- `GET /metrics` (recommended to require auth)

---

## Support

For issues with authentication:

1. Check logs: `kubectl logs -f deployment/control-layer`
2. Verify configuration: Review environment variables
3. Test with curl: Try requests manually
4. GitHub Issues: https://github.com/Thomas-Heisig/MODAX/issues

## Related Documentation

- [API Documentation](API.md)
- [Security Concept](SECURITY.md)
- [Configuration Guide](CONFIGURATION.md)
- [External Integrations](EXTERNAL_INTEGRATIONS.md)
