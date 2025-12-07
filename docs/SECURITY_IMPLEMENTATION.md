# MODAX Security Implementation Guide

This document describes the implementation of security features in the MODAX Control Layer, including authentication, authorization, audit logging, and secrets management.

## Implemented Features

### 1. MQTT Authentication and TLS/SSL

The MQTT handler now supports secure connections with authentication and encryption.

#### Configuration

Set these environment variables in your `.env` file:

```bash
# Enable TLS
MQTT_USE_TLS=true

# Certificate paths
MQTT_CA_CERTS=/etc/modax/certs/ca.crt
MQTT_CERTFILE=/etc/modax/certs/client.crt
MQTT_KEYFILE=/etc/modax/certs/client.key

# Authentication
MQTT_USERNAME=control_layer
MQTT_PASSWORD=your_secure_password
```

#### Certificate Setup

1. **Generate CA Certificate:**
   ```bash
   openssl genrsa -out ca.key 4096
   openssl req -new -x509 -days 365 -key ca.key -out ca.crt
   ```

2. **Generate Server Certificate:**
   ```bash
   openssl genrsa -out server.key 2048
   openssl req -new -key server.key -out server.csr
   openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365
   ```

3. **Generate Client Certificate:**
   ```bash
   openssl genrsa -out client.key 2048
   openssl req -new -key client.key -out client.csr
   openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365
   ```

#### Mosquitto Configuration

Update `mosquitto.conf`:

```
# Enable TLS
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key

# Require client certificates
require_certificate true
use_identity_as_username true

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# ACL
acl_file /etc/mosquitto/acl
```

Create password file:
```bash
mosquitto_passwd -c /etc/mosquitto/passwd control_layer
```

### 2. API Authentication

The Control Layer API now supports API key authentication.

#### Enabling Authentication

Set in `.env`:
```bash
API_KEY_ENABLED=true
HMI_API_KEY=your_hmi_api_key
MONITORING_API_KEY=your_monitoring_api_key
ADMIN_API_KEY=your_admin_api_key
```

#### Generating API Keys

Use a secure random generator:
```bash
openssl rand -hex 32
```

#### Using API Keys

Include the API key in the request header:
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/status
```

#### Permissions

- **HMI Client**: read, write, control
- **Monitoring**: read only
- **Admin**: read, write, control, admin

### 3. Security Audit Logging

All security events are logged to a dedicated audit log file.

#### Log Location

- **Development**: `./logs/security_audit.log`
- **Production**: `/var/log/modax/security_audit.log`

#### Event Types

1. **Authentication Events**
   - Login success/failure
   - API key validation

2. **Authorization Events**
   - Access denied
   - Permission violations

3. **Control Commands**
   - Executed commands
   - Blocked commands
   - Failed commands

4. **Configuration Changes**
   - Parameter updates
   - Settings modifications

#### Log Format

Logs are in JSON format for easy parsing:
```json
{
  "timestamp": "2025-12-07T13:51:07.731Z",
  "event_type": "authentication",
  "severity": "INFO",
  "user": "operator1",
  "action": "login_success",
  "source_ip": "192.168.1.100",
  "metadata": {
    "method": "api_key"
  }
}
```

### 4. Secrets Management

Supports both environment variables and HashiCorp Vault.

#### Environment Variables (Default)

Store secrets in `.env` file:
```bash
MQTT_PASSWORD=your_password
DB_PASSWORD=your_db_password
HMI_API_KEY=your_api_key
```

#### HashiCorp Vault (Recommended for Production)

1. **Enable Vault:**
   ```bash
   USE_VAULT=true
   VAULT_ADDR=http://vault:8200
   VAULT_TOKEN=your_vault_token
   ```

2. **Store Secrets in Vault:**
   ```bash
   vault kv put modax/secrets \
     MQTT_USERNAME=control_layer \
     MQTT_PASSWORD=secure_password \
     DB_PASSWORD=db_password \
     HMI_API_KEY=api_key
   ```

3. **Automatic Secret Retrieval:**
   The secrets manager will automatically fetch secrets from Vault.

### 5. WebSocket Support

Real-time updates via WebSocket connections.

#### Endpoints

- `/ws` - All devices
- `/ws/device/{device_id}` - Specific device

#### Connection Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

#### Message Types

- `sensor_data` - Real-time sensor readings
- `safety_status` - Safety status updates
- `ai_analysis` - AI analysis results
- `system_status` - Overall system status

### 6. TimescaleDB Integration

Time-series database for historical data storage.

#### Database Setup

1. **Install TimescaleDB:**
   ```bash
   # Docker
   docker run -d --name timescaledb \
     -p 5432:5432 \
     -e POSTGRES_PASSWORD=password \
     timescale/timescaledb:latest-pg16
   ```

2. **Create Database:**
   ```bash
   psql -h localhost -U postgres -c "CREATE DATABASE modax;"
   psql -h localhost -U postgres -c "CREATE USER modax_user WITH PASSWORD 'password';"
   psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE modax TO modax_user;"
   ```

3. **Run Schema:**
   ```bash
   psql -h localhost -U modax_user -d modax -f python-control-layer/schema.sql
   ```

#### Configuration

```bash
DB_ENABLED=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=modax
DB_USER=modax_user
DB_PASSWORD=your_db_password
```

### 7. Data Export

Export sensor data in CSV or JSON format.

#### Endpoints

- `/export/{device_id}/csv?hours=24` - CSV export
- `/export/{device_id}/json?hours=24` - JSON export
- `/export/{device_id}/statistics?hours=24` - Statistics JSON

#### Example

```bash
curl -H "X-API-Key: your_api_key" \
  http://localhost:8000/export/esp32_001/csv?hours=24 \
  -o data.csv
```

## Security Best Practices

### 1. Development vs Production

**Development:**
- Use self-signed certificates
- API authentication optional
- Debug logging enabled

**Production:**
- Valid CA-signed certificates
- API authentication required
- TLS/SSL mandatory
- Vault for secrets
- Audit logging enabled

### 2. Network Security

Implement network segmentation:
```
Office Network (IT)
     ↓ (HTTPS only)
Control Network (OT)
     ↓ (MQTT TLS only)
Field Network (Devices)
```

### 3. Access Control

Implement least privilege:
- HMI: Read/write sensor data, execute safe commands
- Monitoring: Read-only access
- Admin: Full system access

### 4. Monitoring

Monitor for:
- Failed authentication attempts
- Authorization violations
- Unusual command patterns
- Certificate expiration

### 5. Incident Response

1. **Detection**: Audit logs, alerts
2. **Containment**: Block compromised keys
3. **Eradication**: Rotate credentials
4. **Recovery**: Restore from backups
5. **Lessons Learned**: Update procedures

## Testing

Run security tests:
```bash
cd python-control-layer
pytest test_auth.py test_security_audit.py test_secrets_manager.py -v
```

## Migration Guide

### From Unsecured to Secured

1. **Generate Certificates**
   ```bash
   ./scripts/generate_certs.sh
   ```

2. **Update Configuration**
   ```bash
   cp config/control-layer-security.env.example .env
   # Edit .env with your values
   ```

3. **Enable Features Gradually**
   - Week 1: MQTT TLS
   - Week 2: API Authentication
   - Week 3: Audit Logging
   - Week 4: Vault Integration

4. **Test Each Feature**
   - Run integration tests
   - Monitor logs
   - Verify functionality

## Troubleshooting

### MQTT Connection Fails

1. Check certificate paths
2. Verify certificate validity
3. Check mosquitto logs
4. Test with `mosquitto_pub`

### API Authentication Fails

1. Verify API key is set
2. Check header format
3. Review audit logs
4. Test with curl

### Database Connection Fails

1. Verify PostgreSQL is running
2. Check credentials
3. Verify network connectivity
4. Review database logs

## References

- [SECURITY.md](SECURITY.md) - Security concept
- [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md) - Database architecture
- [API.md](API.md) - API documentation
- [MQTT Security Best Practices](https://mqtt.org/mqtt-specification/)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
