# MODAX External System Integrations

This document describes how to integrate MODAX with external enterprise systems including ERP, MES, SCADA, and other manufacturing execution systems.

**Last Updated:** 2025-12-09  
**Version:** 0.2.0

## Overview

MODAX provides multiple integration points for external systems:

1. **REST API** - HTTP/HTTPS endpoints for data access and control
2. **MQTT Topics** - Real-time message streaming
3. **OPC UA Server** - Standard industrial automation protocol
4. **Database Access** - Direct TimescaleDB queries (read-only)
5. **WebSocket** - Real-time data streaming

## Integration Patterns

### Pattern 1: Pull Model (REST API)

External systems periodically query MODAX APIs to retrieve data.

**Use Cases:**
- ERP systems retrieving production statistics
- Business intelligence tools
- Reporting systems

**Advantages:**
- Simple to implement
- External system controls data flow
- Works with existing polling mechanisms

**Disadvantages:**
- Higher latency
- More network traffic
- May miss real-time events

### Pattern 2: Push Model (MQTT/WebSocket)

MODAX pushes data to external systems in real-time.

**Use Cases:**
- Real-time SCADA integration
- Immediate alarm notifications
- Live dashboards

**Advantages:**
- Low latency
- Efficient bandwidth usage
- Real-time updates

**Disadvantages:**
- Requires persistent connection
- External system must handle asynchronous messages

### Pattern 3: Hybrid Model

Combination of pull and push approaches.

**Use Cases:**
- MES systems (pull for historical data, push for alarms)
- Complex integrations with multiple data types

---

## ERP System Integration

### SAP Integration

#### Overview
Integration with SAP S/4HANA or SAP ECC for production data exchange.

#### Integration Points

**1. Production Orders**
- Pull production orders from SAP
- Report actual production quantities back to SAP

```python
# Example: Retrieve production order
GET /api/v1/production/orders/{order_id}

# Example: Report production completion
POST /api/v1/production/orders/{order_id}/complete
{
  "quantity_produced": 100,
  "quantity_rejected": 2,
  "completion_time": "2025-12-09T10:30:00Z",
  "device_id": "cnc-machine-01"
}
```

**2. Quality Data**
- Push quality inspection results to SAP QM module

```python
POST /api/v1/quality/inspection-lot/{lot_id}/results
{
  "device_id": "cnc-machine-01",
  "characteristics": [
    {"name": "dimension_x", "measured_value": 10.02, "target": 10.0, "tolerance": 0.05},
    {"name": "surface_roughness", "measured_value": 1.2, "target": 1.0, "tolerance": 0.3}
  ],
  "result": "passed",
  "timestamp": "2025-12-09T10:30:00Z"
}
```

**3. Equipment Status**
- Report machine downtime and availability to SAP PM

```python
POST /api/v1/equipment/status
{
  "device_id": "cnc-machine-01",
  "status": "down",
  "reason_code": "maintenance",
  "downtime_start": "2025-12-09T10:00:00Z",
  "downtime_end": "2025-12-09T11:30:00Z"
}
```

#### Implementation Example (Python)

```python
import requests
from datetime import datetime

class SAPIntegration:
    def __init__(self, modax_url, sap_url, api_key):
        self.modax_url = modax_url
        self.sap_url = sap_url
        self.headers = {"X-API-Key": api_key}
    
    def sync_production_data(self, device_id):
        """Sync production data from MODAX to SAP"""
        # Get production data from MODAX
        response = requests.get(
            f"{self.modax_url}/api/v1/devices/{device_id}/statistics",
            headers=self.headers
        )
        data = response.json()
        
        # Transform to SAP format
        sap_payload = {
            "AUFNR": data["order_id"],  # Production Order
            "GMNGA": data["quantity_produced"],  # Good quantity
            "AUSSS": data["quantity_rejected"],  # Scrap quantity
            "BUDAT": data["production_date"]
        }
        
        # Post to SAP
        sap_response = requests.post(
            f"{self.sap_url}/api/production/confirmation",
            json=sap_payload,
            auth=("user", "password")
        )
        
        return sap_response.status_code == 200
```

### Oracle ERP Integration

Similar patterns apply for Oracle ERP Cloud or Oracle E-Business Suite.

**Key Endpoints:**
- Work Order Management API
- Quality Management API
- Asset Management API

---

## MES (Manufacturing Execution System) Integration

### Siemens Opcenter

#### Real-time Data Exchange via MQTT

```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    """Handle MODAX sensor data"""
    data = json.loads(msg.payload)
    
    # Send to Opcenter API
    opcenter_update = {
        "machine_id": data["device_id"],
        "status": "producing" if data["is_safe"] else "alarm",
        "speed": data["spindle_speed"],
        "timestamp": data["timestamp"]
    }
    
    # Post to Opcenter
    requests.post(
        "http://opcenter.example.com/api/machine-data",
        json=opcenter_update
    )

# Connect to MODAX MQTT broker
client = mqtt.Client()
client.on_message = on_message
client.username_pw_set("mes-integration", "password")
client.connect("mqtt.modax.example.com", 8883)
client.subscribe("modax/sensor/data/#")
client.loop_forever()
```

### Rockwell FactoryTalk

**Integration via OPC UA:**

```xml
<!-- FactoryTalk Gateway Configuration -->
<OpcUaEndpoint>
  <EndpointUrl>opc.tcp://modax.example.com:4840</EndpointUrl>
  <SecurityMode>SignAndEncrypt</SecurityMode>
  <SecurityPolicy>Basic256Sha256</SecurityPolicy>
  <UserIdentity>
    <Username>factorytalk</Username>
    <Password>***</Password>
  </UserIdentity>
</OpcUaEndpoint>
```

---

## SCADA System Integration

### Wonderware System Platform

#### Real-time Data via MQTT

Configure Wonderware to subscribe to MODAX MQTT topics:

```
Topic: modax/sensor/data/+
QoS: 1
Username: scada-client
Password: ***
```

**Tag Mapping:**

| MODAX Topic | Wonderware Tag | Data Type |
|-------------|----------------|-----------|
| modax/sensor/data/cnc-01 | CNC01.Temperature | Real |
| modax/sensor/data/cnc-01 | CNC01.Vibration | Real |
| modax/sensor/safety/cnc-01 | CNC01.SafetyStatus | Boolean |

#### Alarm Integration

```python
# Subscribe to AI analysis for anomaly detection
mqtt_client.subscribe("modax/ai/analysis/#")

def on_ai_analysis(client, userdata, msg):
    analysis = json.loads(msg.payload)
    
    if analysis.get("has_anomaly"):
        # Trigger Wonderware alarm
        alarm_payload = {
            "alarm_name": f"MODAX_{analysis['device_id']}_ANOMALY",
            "severity": "high" if analysis["anomaly_score"] > 0.8 else "medium",
            "message": f"Anomaly detected: {analysis['anomaly_type']}",
            "timestamp": analysis["timestamp"]
        }
        # Send to Wonderware alarm API
        post_alarm(alarm_payload)
```

### Siemens WinCC

**OPC UA Integration:**

1. Add new OPC UA Server in WinCC
2. Browse MODAX OPC UA server
3. Map variables to WinCC tags

**Example Variable Mapping:**
```
MODAX.Devices.CNC-01.Temperature -> @CNC01_TEMP
MODAX.Devices.CNC-01.Status -> @CNC01_STATUS
MODAX.AI.Anomalies.CNC-01 -> @CNC01_ANOMALY
```

---

## Database Integration (TimescaleDB)

### Read-Only Access for BI Tools

Create a read-only database user for external systems:

```sql
-- Create read-only user
CREATE USER bi_readonly WITH PASSWORD 'secure_password';

-- Grant read access
GRANT CONNECT ON DATABASE modax TO bi_readonly;
GRANT USAGE ON SCHEMA public TO bi_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT SELECT ON TABLES TO bi_readonly;
```

### Power BI Integration

**Connection String:**
```
Host: timescaledb.modax.example.com
Port: 5432
Database: modax
Username: bi_readonly
Password: ***
SSL Mode: require
```

**Example Query:**
```sql
-- Production statistics by device
SELECT 
  time_bucket('1 hour', time) AS hour,
  device_id,
  AVG(temperature) as avg_temp,
  AVG(current) as avg_current,
  COUNT(*) as sample_count
FROM sensor_data
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY hour, device_id
ORDER BY hour DESC;
```

### Tableau Integration

Use PostgreSQL connector with TimescaleDB connection details.

**Custom SQL Example:**
```sql
-- Anomaly trends over time
SELECT 
  time_bucket('1 day', time) as date,
  anomaly_type,
  COUNT(*) as anomaly_count,
  AVG(anomaly_score) as avg_score
FROM ai_analysis
WHERE has_anomaly = true
  AND time > NOW() - INTERVAL '30 days'
GROUP BY date, anomaly_type
ORDER BY date DESC;
```

---

## Custom Integration Development

### REST API Client Example

```python
class ModaxClient:
    """Python client for MODAX REST API"""
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_device_status(self, device_id):
        """Get current device status"""
        response = requests.get(
            f"{self.base_url}/api/v1/devices/{device_id}/data",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_ai_analysis(self, device_id):
        """Get AI analysis results"""
        response = requests.get(
            f"{self.base_url}/api/v1/devices/{device_id}/ai-analysis",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def export_data(self, device_id, format="csv", start_time=None, end_time=None):
        """Export historical data"""
        params = {}
        if start_time:
            params["start"] = start_time.isoformat()
        if end_time:
            params["end"] = end_time.isoformat()
        
        response = requests.get(
            f"{self.base_url}/api/v1/export/{device_id}/{format}",
            headers=self.headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.content

# Usage
client = ModaxClient("https://api.modax.example.com", "your-api-key")
status = client.get_device_status("cnc-machine-01")
print(f"Temperature: {status['temperature']}°C")
```

### MQTT Client Example

```python
import paho.mqtt.client as mqtt
import ssl

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to all sensor data
    client.subscribe("modax/sensor/data/#")
    client.subscribe("modax/ai/analysis/#")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Payload: {msg.payload.decode()}")
    
    # Process message
    data = json.loads(msg.payload)
    # Your integration logic here

# Setup TLS
client = mqtt.Client()
client.username_pw_set("integration-client", "password")
client.tls_set(
    ca_certs="/path/to/ca.crt",
    certfile="/path/to/client.crt",
    keyfile="/path/to/client.key",
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.on_connect = on_connect
client.on_message = on_message

# Connect
client.connect("mqtt.modax.example.com", 8883, 60)
client.loop_forever()
```

---

## Security Considerations

### Authentication

All external integrations must use one of:

1. **API Keys** (for REST API)
   - Request key from MODAX administrator
   - Include in `X-API-Key` header
   - Rotate keys every 90 days

2. **Username/Password** (for MQTT)
   - Use dedicated integration users
   - Never share credentials between systems

3. **Certificate-based** (for OPC UA)
   - Generate client certificates
   - Register with MODAX OPC UA server

### Network Security

- Use TLS/SSL for all connections
- Implement firewall rules
- Consider VPN for cross-site integrations
- Use OT/IT network segmentation

### Data Access Control

- Request minimum necessary permissions
- Use read-only access where possible
- Log all external system access
- Monitor for unusual patterns

---

## Testing Integration

### Development Environment

Use MODAX test instance for integration development:

```
API URL: https://api-dev.modax.example.com
MQTT Broker: mqtt-dev.modax.example.com:8883
Test Device ID: test-device-01
```

### Integration Testing Checklist

- [ ] Authentication working correctly
- [ ] Data format validation
- [ ] Error handling for network failures
- [ ] Retry logic for temporary failures
- [ ] Rate limiting compliance
- [ ] Logging and monitoring in place
- [ ] Performance meets requirements
- [ ] Security audit passed

---

## Support and Resources

### Documentation
- API Reference: `/docs/API.md`
- MQTT Topics: `/docs/MQTT_TOPICS.md`
- OPC UA Guide: `/docs/OPC_UA_INTEGRATION.md`

### Example Code
- Python client library: `/examples/python-client/`
- Node.js examples: `/examples/nodejs-client/`
- C# integration: `/examples/csharp-client/`

### Getting Help
- GitHub Issues: https://github.com/Thomas-Heisig/MODAX/issues
- Email: support@modax.example.com
- Documentation: https://docs.modax.example.com
