# MODAX API Documentation

This document provides comprehensive API documentation for the MODAX system REST endpoints.

## Table of Contents
- [Control Layer API (Port 8000)](#control-layer-api-port-8000)
- [AI Layer API (Port 8001)](#ai-layer-api-port-8001)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Control Layer API (Port 8000)

Base URL: `http://localhost:8000`

### Health & Status Endpoints

#### GET /health
Health check endpoint for monitoring and load balancers.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "version": "0.1.0"
}
```

#### GET /status
Get overall system status including connected devices and safety state.

**Response (200 OK):**
```json
{
  "is_safe": true,
  "devices_online": ["ESP32_FIELD_001", "ESP32_FIELD_002"],
  "last_update": 1234567890.123,
  "ai_enabled": true,
  "ai_last_analysis": 1234567880.0
}
```

**Response Fields:**
- `is_safe` (boolean): Overall safety status of the system
- `devices_online` (array): List of currently connected device IDs
- `last_update` (float): Unix timestamp of last data reception
- `ai_enabled` (boolean): Whether AI analysis is enabled
- `ai_last_analysis` (float): Unix timestamp of last AI analysis

#### GET /ai/status
Get AI layer connectivity and status.

**Response (200 OK):**
```json
{
  "ai_layer_reachable": true,
  "last_analysis_time": 1234567880.0,
  "analysis_count": 42
}
```

**Response (503 Service Unavailable):**
```json
{
  "error": "AI layer not reachable",
  "details": "Connection refused at http://localhost:8001"
}
```

---

### Device Endpoints

#### GET /devices
List all connected field devices.

**Response (200 OK):**
```json
{
  "devices": [
    {
      "device_id": "ESP32_FIELD_001",
      "last_seen": 1234567890.123,
      "data_points": 1523,
      "is_safe": true
    }
  ]
}
```

**Response Fields:**
- `device_id` (string): Unique device identifier
- `last_seen` (float): Unix timestamp of last data reception
- `data_points` (int): Number of data points stored for this device
- `is_safe` (boolean): Current safety status of this device

#### GET /devices/{device_id}/data
Get latest sensor data from a specific device.

**Path Parameters:**
- `device_id` (string, required): Device identifier

**Response (200 OK):**
```json
{
  "timestamp": 1234567890.123,
  "device_id": "ESP32_FIELD_001",
  "motor_currents": [4.5, 4.3],
  "vibration": {
    "x": 1.2,
    "y": 1.1,
    "z": 1.3,
    "magnitude": 2.1
  },
  "temperatures": [45.5, 46.2],
  "safety_status": {
    "emergency_stop": false,
    "door_closed": true,
    "overload_detected": false,
    "temperature_ok": true,
    "is_safe": true
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

#### GET /devices/{device_id}/history
Get historical aggregated data for a device.

**Path Parameters:**
- `device_id` (string, required): Device identifier

**Query Parameters:**
- `limit` (int, optional): Maximum number of data points (default: 100, max: 1000)

**Response (200 OK):**
```json
{
  "device_id": "ESP32_FIELD_001",
  "data_points": [
    {
      "timestamp": 1234567890.123,
      "motor_currents": [4.5, 4.3],
      "vibration_magnitude": 2.1,
      "temperatures": [45.5, 46.2]
    }
  ]
}
```

#### GET /devices/{device_id}/ai-analysis
Get latest AI analysis results for a device.

**Path Parameters:**
- `device_id` (string, required): Device identifier

**Response (200 OK):**
```json
{
  "timestamp": 1234567890000,
  "device_id": "ESP32_FIELD_001",
  "anomaly_detected": false,
  "anomaly_score": 0.15,
  "anomaly_description": "Current levels slightly elevated",
  "predicted_wear_level": 0.12,
  "estimated_remaining_hours": 8800,
  "recommendations": [
    "System operating within normal parameters",
    "Schedule maintenance in ~8800 hours"
  ],
  "confidence": 0.85
}
```

**Response Fields:**
- `timestamp` (int): Unix timestamp in milliseconds
- `device_id` (string): Device identifier
- `anomaly_detected` (boolean): Whether an anomaly was detected
- `anomaly_score` (float): Anomaly severity (0.0 = none, 1.0 = critical)
- `anomaly_description` (string): Human-readable anomaly description
- `predicted_wear_level` (float): Wear level (0.0 = new, 1.0 = end of life)
- `estimated_remaining_hours` (int): Estimated hours until maintenance needed
- `recommendations` (array): List of actionable recommendations
- `confidence` (float): AI confidence in the analysis (0.0 - 1.0)

**Response (404 Not Found):**
```json
{
  "detail": "No AI analysis available for this device"
}
```

---

### Control Command Endpoints

#### POST /control/command
Send a control command to a field device.

**Request Body:**
```json
{
  "device_id": "ESP32_FIELD_001",
  "command_type": "start",
  "parameters": {
    "speed": "100",
    "mode": "auto"
  }
}
```

**Request Fields:**
- `device_id` (string, required): Target device identifier
- `command_type` (string, required): Command type (e.g., "start", "stop", "reset")
- `parameters` (object, optional): Command-specific parameters

**Response (200 OK):**
```json
{
  "status": "command_sent",
  "device_id": "ESP32_FIELD_001",
  "command_type": "start",
  "timestamp": 1234567890.123
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "System is not in safe state. Command blocked for safety."
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

**Safety Note:** Commands are only executed if the system is in a safe state. This is verified at the control layer level.

---

## AI Layer API (Port 8001)

Base URL: `http://localhost:8001`

### Health Endpoints

#### GET /
API information and available endpoints.

**Response (200 OK):**
```json
{
  "service": "MODAX AI Layer",
  "version": "0.1.0",
  "status": "operational",
  "models": {
    "anomaly_detection": "Statistical",
    "wear_prediction": "Empirical",
    "optimizer": "Rule-based"
  }
}
```

#### GET /health
Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123
}
```

#### GET /models/info
Get information about loaded AI models.

**Response (200 OK):**
```json
{
  "anomaly_detection": {
    "type": "statistical",
    "method": "z-score",
    "z_threshold": 3.0
  },
  "wear_prediction": {
    "type": "empirical",
    "nominal_lifetime_hours": 10000
  },
  "optimizer": {
    "type": "rule-based",
    "rules_count": 12
  }
}
```

---

### Analysis Endpoints

#### POST /analyze
Analyze aggregated sensor data and provide insights.

**Request Body:**
```json
{
  "device_id": "ESP32_FIELD_001",
  "time_window_start": 1234567890.0,
  "time_window_end": 1234567900.0,
  "current_mean": [4.5, 4.3],
  "current_std": [0.5, 0.4],
  "current_max": [6.2, 5.8],
  "vibration_mean": {
    "x": 1.2,
    "y": 1.1,
    "z": 1.3,
    "magnitude": 2.1
  },
  "vibration_std": {
    "x": 0.3,
    "y": 0.3,
    "z": 0.4,
    "magnitude": 0.5
  },
  "vibration_max": {
    "x": 2.5,
    "y": 2.3,
    "z": 2.8,
    "magnitude": 4.2
  },
  "temperature_mean": [45.5],
  "temperature_max": [52.3],
  "sample_count": 100
}
```

**Request Fields:**
- `device_id` (string, required): Device identifier
- `time_window_start` (float, required): Unix timestamp of analysis window start
- `time_window_end` (float, required): Unix timestamp of analysis window end
- `current_mean` (array, required): Mean current values for each motor (Amperes)
- `current_std` (array, required): Standard deviation of currents
- `current_max` (array, required): Maximum current values
- `vibration_mean` (object, required): Mean vibration (x, y, z, magnitude in m/s²)
- `vibration_std` (object, required): Vibration standard deviation
- `vibration_max` (object, required): Maximum vibration values
- `temperature_mean` (array, required): Mean temperatures (°C)
- `temperature_max` (array, required): Maximum temperatures (°C)
- `sample_count` (int, required): Number of samples in aggregation

**Response (200 OK):**
```json
{
  "timestamp": 1234567900000,
  "device_id": "ESP32_FIELD_001",
  "anomaly_detected": false,
  "anomaly_score": 0.0,
  "anomaly_description": "No anomalies detected",
  "predicted_wear_level": 0.15,
  "estimated_remaining_hours": 8500,
  "recommendations": [
    "System operating within normal parameters",
    "Wear accumulation progressing normally",
    "Next maintenance recommended in 8500 hours"
  ],
  "confidence": 0.82
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "current_mean"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### POST /reset-wear/{device_id}
Reset wear accumulation counter after maintenance.

**Path Parameters:**
- `device_id` (string, required): Device identifier

**Request Body:**
```json
{
  "maintenance_performed": "bearing replacement",
  "timestamp": 1234567890.0
}
```

**Response (200 OK):**
```json
{
  "status": "wear_reset",
  "device_id": "ESP32_FIELD_001",
  "timestamp": 1234567890.0
}
```

---

## Error Handling

All endpoints follow standard HTTP status codes:

### Success Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully

### Client Error Codes
- **400 Bad Request**: Invalid request parameters or body
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error

### Server Error Codes
- **500 Internal Server Error**: Unexpected server error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Response Format
```json
{
  "detail": "Human-readable error message",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": 1234567890.123
}
```

---

## Rate Limiting

### Control Layer
- **Default Limit**: 100 requests/second per client
- **Burst Limit**: 200 requests/second (short term)
- **Response Header**: `X-RateLimit-Remaining`

### AI Layer
- **Default Limit**: 50 requests/second per client
- **Analysis Timeout**: 5 seconds maximum per request

### Rate Limit Exceeded Response (429)
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

---

## Authentication

**Current Status:** None (Development Mode)

**Production Recommendations:**
1. Implement API key authentication
2. Use JWT tokens for session management
3. Enable TLS/SSL for all connections
4. Implement role-based access control (RBAC)

Example future authentication header:
```
Authorization: Bearer <token>
```

---

## MQTT Topics

While not REST APIs, the following MQTT topics are relevant for system integration:

### Published by Field Layer
- `modax/sensor/data` - Sensor readings (QoS 0, 10Hz)
- `modax/sensor/safety` - Safety status (QoS 1, 20Hz+)

### Published by Control Layer
- `modax/ai/analysis` - AI analysis results (QoS 1, ~1/min)
- `modax/control/commands` - Control commands (QoS 1, on-demand)

### Message Format
All MQTT messages use JSON format:
```json
{
  "timestamp": 1234567890.123,
  "device_id": "ESP32_FIELD_001",
  // ... topic-specific fields
}
```

---

## Versioning

**Current Version:** 0.1.0

API versioning strategy (future):
- URL-based: `/v1/devices`, `/v2/devices`
- Header-based: `Accept: application/vnd.modax.v1+json`

---

## Examples

### Python Example
```python
import requests

# Get system status
response = requests.get("http://localhost:8000/status")
status = response.json()
print(f"System safe: {status['is_safe']}")

# Get device data
device_id = "ESP32_FIELD_001"
response = requests.get(f"http://localhost:8000/devices/{device_id}/data")
data = response.json()
print(f"Motor currents: {data['motor_currents']}")

# Send control command (only if safe)
if status['is_safe']:
    command = {
        "device_id": device_id,
        "command_type": "start",
        "parameters": {"speed": "100"}
    }
    response = requests.post("http://localhost:8000/control/command", json=command)
    print(f"Command status: {response.json()['status']}")
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Get all devices
curl http://localhost:8000/devices

# Get device data
curl http://localhost:8000/devices/ESP32_FIELD_001/data

# Send command
curl -X POST http://localhost:8000/control/command \
  -H "Content-Type: application/json" \
  -d '{"device_id":"ESP32_FIELD_001","command_type":"start"}'

# Get AI analysis
curl http://localhost:8000/devices/ESP32_FIELD_001/ai-analysis

# Request AI layer analysis directly
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @sensor_data.json

# WebSocket connection (all devices)
wscat -c ws://localhost:8000/ws

# WebSocket connection (specific device)
wscat -c ws://localhost:8000/ws/device/ESP32_FIELD_001

# Export data as CSV
curl -H "X-API-Key: your_api_key" \
  http://localhost:8000/export/ESP32_FIELD_001/csv?hours=24 \
  -o data.csv

# Export data as JSON
curl -H "X-API-Key: your_api_key" \
  http://localhost:8000/export/ESP32_FIELD_001/json?hours=24 \
  -o data.json
```

---

## WebSocket Endpoints (Real-Time Updates)

### WS /ws
Connect to receive real-time updates from all devices.

**Message Types:**
- `sensor_data` - Real-time sensor readings
- `safety_status` - Safety status changes
- `ai_analysis` - AI analysis results
- `system_status` - System status updates

**Example Message:**
```json
{
  "type": "sensor_data",
  "device_id": "ESP32_FIELD_001",
  "data": {
    "timestamp": 1234567890.123,
    "current": 5.2,
    "vibration": 100.5,
    "temperature": 45.3
  }
}
```

### WS /ws/device/{device_id}
Connect to receive real-time updates from a specific device.

**Parameters:**
- `device_id` (string, required): Device identifier

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/device/ESP32_FIELD_001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

## Data Export Endpoints

### GET /export/{device_id}/csv
Export sensor data in CSV format.

**Parameters:**
- `device_id` (string, required): Device identifier
- `hours` (int, optional): Number of hours to export (default: 24)

**Headers:**
- `X-API-Key` (required if authentication enabled): API key

**Response (200 OK):**
Returns CSV file with headers:
```csv
timestamp,device_id,current_a,current_b,current_c,vibration,temperature,rpm,power_kw
2025-12-07T12:00:00Z,ESP32_FIELD_001,5.2,5.1,5.3,100.5,45.3,1500,7.8
```

**Response (404 Not Found):**
```json
{
  "detail": "No data available for device ESP32_FIELD_001"
}
```

### GET /export/{device_id}/json
Export sensor data in JSON format.

**Parameters:**
- `device_id` (string, required): Device identifier
- `hours` (int, optional): Number of hours to export (default: 24)

**Headers:**
- `X-API-Key` (required if authentication enabled): API key

**Response (200 OK):**
```json
[
  {
    "timestamp": "2025-12-07T12:00:00Z",
    "device_id": "ESP32_FIELD_001",
    "current_a": 5.2,
    "current_b": 5.1,
    "current_c": 5.3,
    "vibration": 100.5,
    "temperature": 45.3,
    "rpm": 1500,
    "power_kw": 7.8
  }
]
```

### GET /export/{device_id}/statistics
Export hourly statistics in JSON format.

**Parameters:**
- `device_id` (string, required): Device identifier
- `hours` (int, optional): Number of hours of statistics (default: 24)

**Headers:**
- `X-API-Key` (required if authentication enabled): API key

**Response (200 OK):**
```json
[
  {
    "hour": "2025-12-07T12:00:00Z",
    "avg_current": 5.2,
    "max_current": 6.1,
    "avg_vibration": 102.3,
    "max_vibration": 150.2,
    "avg_temperature": 45.0,
    "sample_count": 36000
  }
]
```

---

## Authentication

API authentication can be enabled using API keys.

### Configuration

Set in environment variables:
```bash
API_KEY_ENABLED=true
HMI_API_KEY=your_hmi_api_key
MONITORING_API_KEY=your_monitoring_api_key
ADMIN_API_KEY=your_admin_api_key
```

### Using API Keys

Include the API key in the request header:
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/status
```

### Permissions

Different API keys have different permission levels:

| Key Type | Permissions | Rate Limit |
|----------|-------------|------------|
| HMI Client | read, write, control | 100 req/min |
| Monitoring | read | 1000 req/min |
| Admin | read, write, control, admin | 1000 req/min |

### Error Responses

**401 Unauthorized (Missing API Key):**
```json
{
  "detail": "API key is missing"
}
```

**401 Unauthorized (Invalid API Key):**
```json
{
  "detail": "Invalid API key"
}
```

**403 Forbidden (Insufficient Permissions):**
```json
{
  "detail": "Insufficient permissions: 'control' required"
}
```

---

## Network Scanner Endpoints

### POST /api/v1/network/scan
Scan network for active devices.

**Query Parameters:**
- `network` (string, optional): CIDR notation (e.g., "192.168.1.0/24"). If not provided, scans local subnet.

**Response (200 OK):**
```json
{
  "status": "success",
  "scan_time": "2025-12-17T10:20:00.000Z",
  "network": "192.168.1.0/24",
  "devices_found": 5,
  "devices": [
    {
      "ip": "192.168.1.1",
      "hostname": "router.local",
      "mac": null,
      "open_ports": [80, 443],
      "device_type": "Web Server",
      "vendor": null,
      "discovered_at": "2025-12-17T10:20:00.000Z"
    }
  ]
}
```

**Rate Limit:** 5 requests/minute

### POST /api/v1/network/scan/quick
Quick scan of specific hosts.

**Request Body:**
```json
{
  "hosts": ["192.168.1.1", "192.168.1.2", "192.168.1.100"]
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "scan_time": "2025-12-17T10:20:00.000Z",
  "hosts_scanned": 3,
  "devices_found": 2,
  "devices": [...]
}
```

**Rate Limit:** 10 requests/minute  
**Maximum:** 100 hosts per request

### POST /api/v1/port/scan
Scan ports on a specific host.

**Query Parameters:**
- `host` (string, required): IP address or hostname
- `common_ports` (boolean, default: true): Scan common ports (22, 80, 443, 502, 8000, 8001, etc.)
- `ports` (array, optional): List of specific ports to scan

**Response (200 OK):**
```json
{
  "status": "success",
  "scan_time": "2025-12-17T10:20:00.000Z",
  "host": "192.168.1.100",
  "ports_scanned": 24,
  "open_ports": 3,
  "results": [
    {
      "port": 22,
      "open": true,
      "service": "SSH"
    },
    {
      "port": 80,
      "open": true,
      "service": "HTTP"
    },
    {
      "port": 8000,
      "open": true,
      "service": "HTTP Alt (Control Layer)"
    }
  ]
}
```

**Rate Limit:** 10 requests/minute  
**Maximum:** 1000 ports per request

### POST /api/v1/port/scan/range
Scan a range of ports on a host.

**Query Parameters:**
- `host` (string, required): IP address or hostname
- `start_port` (integer, required): Starting port number (1-65535)
- `end_port` (integer, required): Ending port number (1-65535)

**Response (200 OK):**
```json
{
  "status": "success",
  "scan_time": "2025-12-17T10:20:00.000Z",
  "host": "192.168.1.100",
  "port_range": "8000-8100",
  "ports_scanned": 101,
  "open_ports": 2,
  "results": [
    {
      "port": 8000,
      "service": "HTTP Alt (Control Layer)"
    },
    {
      "port": 8001,
      "service": "HTTP Alt (AI Layer)"
    }
  ]
}
```

**Rate Limit:** 5 requests/minute  
**Maximum:** 1000 ports per scan

### Device Type Detection

The network scanner automatically identifies device types based on open ports:

| Device Type | Detected Ports |
|------------|----------------|
| Modbus Device | 502 |
| OPC UA Device | 44818, 4840 |
| MODAX Control System | 8000 and 8001 |
| MODAX Control Layer | 8000 |
| MODAX AI Layer | 8001 |
| Web Server | 80, 443 |
| SSH Device | 22 |
| Telnet Device | 23 |

---

## Support

For API issues or questions:
- Check this documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review [MDI_INTERFACE.md](MDI_INTERFACE.md) for HMI interface
- Review [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md) for security setup
- See [ISSUES.md](../ISSUES.md) for known problems
- Check application logs for detailed error messages

---

**Last Updated:** 2025-12-17  
**Documentation Version:** 1.2
