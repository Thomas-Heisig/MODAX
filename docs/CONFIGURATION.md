# MODAX Configuration Reference

This document provides comprehensive configuration reference for all MODAX system components.

## Table of Contents
- [Control Layer Configuration](#control-layer-configuration)
- [AI Layer Configuration](#ai-layer-configuration)
- [Field Layer Configuration](#field-layer-configuration)
- [HMI Layer Configuration](#hmi-layer-configuration)
- [MQTT Broker Configuration](#mqtt-broker-configuration)
- [Production Deployment](#production-deployment)

---

## Control Layer Configuration

### Environment Variables

The Control Layer supports configuration via environment variables or `.env` file.

#### MQTT Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MQTT_BROKER_HOST` | string | `localhost` | MQTT broker hostname or IP address |
| `MQTT_BROKER_PORT` | integer | `1883` | MQTT broker port number |
| `MQTT_USERNAME` | string | `None` | MQTT authentication username (optional) |
| `MQTT_PASSWORD` | string | `None` | MQTT authentication password (optional) |

#### API Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_HOST` | string | `0.0.0.0` | API server bind address (0.0.0.0 = all interfaces) |
| `API_PORT` | integer | `8000` | API server port number |

#### AI Integration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AI_ENABLED` | boolean | `true` | Enable AI layer integration |
| `AI_LAYER_URL` | string | `http://localhost:8001/analyze` | AI layer analysis endpoint URL |
| `AI_LAYER_TIMEOUT` | integer | `5` | Timeout for AI layer requests (seconds) |

### Configuration File (config.py)

Internal configuration parameters not exposed as environment variables:

#### MQTT Topics
- `topic_sensor_data`: `"modax/sensor/data"` - Field layer sensor data
- `topic_safety`: `"modax/sensor/safety"` - Safety status updates
- `topic_ai_analysis`: `"modax/ai/analysis"` - AI analysis results
- `topic_control_commands`: `"modax/control/commands"` - Control commands

#### Data Aggregation
- `aggregation_window_seconds`: `10` - Time window for data aggregation (seconds)
- `max_data_points`: `1000` - Maximum data points to store per device

#### AI Analysis
- `ai_analysis_interval_seconds`: `60` - Interval between AI analysis requests (seconds)

### Example .env File

Create `python-control-layer/.env`:

```bash
# MQTT Broker Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
# MQTT_USERNAME=modax_user
# MQTT_PASSWORD=secure_password

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AI Layer Integration
AI_ENABLED=true
AI_LAYER_URL=http://localhost:8001/analyze
AI_LAYER_TIMEOUT=5
```

---

## AI Layer Configuration

The AI Layer currently has minimal configurable parameters as it's a stateless analysis service.

### Hard-coded Parameters (ai_service.py, main.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `host` | `0.0.0.0` | API server bind address |
| `port` | `8001` | API server port |
| `log_level` | `info` | Logging verbosity |

### Anomaly Detection Parameters (anomaly_detector.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `z_threshold` | `3.0` | Z-score threshold for anomaly detection |
| `current_max_threshold` | `12.0` A | Absolute maximum current threshold |
| `current_imbalance_threshold` | `2.0` A | Maximum acceptable current difference between motors |
| `vibration_magnitude_threshold` | `5.0` m/s² | Maximum acceptable vibration magnitude |
| `temperature_threshold` | `75.0` °C | Temperature warning threshold |

### Wear Prediction Parameters (wear_predictor.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nominal_lifetime` | `10000` hours | Baseline component lifetime |
| `high_current_threshold` | `5.0` A | Current threshold for increased wear |
| `current_spike_threshold` | `8.0` A | Current spike threshold |
| `high_vibration_threshold` | `3.0` m/s² | Vibration threshold for wear increase |
| `high_temperature_threshold` | `60.0` °C | Temperature threshold for wear increase |

### Future Enhancement: Environment Variable Support

**Recommendation:** Move these parameters to environment variables or configuration file for easier tuning.

Example future `.env` file:
```bash
AI_PORT=8001
AI_LOG_LEVEL=info

# Anomaly Detection
ANOMALY_Z_THRESHOLD=3.0
ANOMALY_CURRENT_MAX=12.0
ANOMALY_CURRENT_IMBALANCE=2.0

# Wear Prediction
WEAR_NOMINAL_LIFETIME=10000
WEAR_HIGH_CURRENT_THRESHOLD=5.0
```

---

## Field Layer Configuration

### WiFi Configuration (main.cpp)

```cpp
// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

**Security Note:** In production, consider using WiFi Protected Setup (WPS) or storing credentials in secure flash memory.

### MQTT Configuration (main.cpp)

```cpp
// MQTT Broker
const char* mqtt_server = "192.168.1.100";  // Broker IP address
const int mqtt_port = 1883;                 // Broker port
const char* device_id = "ESP32_FIELD_001";  // Unique device identifier
```

### Sensor Configuration (main.cpp)

```cpp
// Sampling rates
#define SENSOR_SAMPLE_RATE_MS 100   // 10Hz sensor data
#define SAFETY_CHECK_RATE_MS 50     // 20Hz safety checks

// Calibration values
#define ACS712_SENSITIVITY 0.185    // 5A module: 185mV/A
#define ACS712_ZERO_CURRENT 2.5     // Zero current voltage
#define TEMP_BETA 3950                // NTC thermistor beta value
```

### Safety Thresholds (main.cpp)

```cpp
// Safety limits (AI-free zone)
#define MAX_CURRENT_THRESHOLD 10.0  // Amperes
#define MAX_TEMPERATURE_THRESHOLD 85.0  // Celsius
```

### Pin Configuration (main.cpp)

```cpp
// GPIO Pin assignments
#define CURRENT_SENSOR_1_PIN 34     // ADC pin for motor 1 current
#define CURRENT_SENSOR_2_PIN 35     // ADC pin for motor 2 current
#define TEMP_SENSOR_1_PIN 32        // ADC pin for temperature 1
#define EMERGENCY_STOP_PIN 25       // Digital input with pullup
#define DOOR_SENSOR_PIN 26          // Digital input with pullup
#define I2C_SDA_PIN 21              // I2C data for MPU6050
#define I2C_SCL_PIN 22              // I2C clock for MPU6050
```

### Example Configuration Header

Create `esp32-field-layer/src/config.h`:

```cpp
#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID "YourNetworkName"
#define WIFI_PASSWORD "YourPassword"

// MQTT Configuration
#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883
#define DEVICE_ID "ESP32_FIELD_001"

// Safety Thresholds
#define MAX_CURRENT 10.0
#define MAX_TEMPERATURE 85.0

// Sensor Calibration
#define CURRENT_CALIBRATION 0.185
#define TEMP_BETA 3950

#endif
```

---

## HMI Layer Configuration

### API Endpoint Configuration (ControlLayerClient.cs)

```csharp
// Control Layer endpoint
private const string BASE_URL = "http://localhost:8000";

// Or configure in constructor
public ControlLayerClient(string baseUrl = "http://localhost:8000")
{
    _baseUrl = baseUrl;
}
```

### Update Interval Configuration (MainForm.cs)

```csharp
// Update timer interval (milliseconds)
private const int UPDATE_INTERVAL = 2000;  // 2 seconds
```

### Future Enhancement: Settings File

**Recommendation:** Add application settings file for user-configurable options.

Example `appsettings.json`:
```json
{
  "ControlLayer": {
    "BaseUrl": "http://localhost:8000",
    "TimeoutSeconds": 5
  },
  "UI": {
    "UpdateIntervalMs": 2000,
    "Theme": "Light",
    "DefaultDevice": "ESP32_FIELD_001"
  }
}
```

Usage in Program.cs:
```csharp
var configuration = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json", optional: false)
    .Build();
```

---

## MQTT Broker Configuration

### Mosquitto Configuration

Create `/etc/mosquitto/conf.d/modax.conf`:

#### Basic Configuration (Development)
```conf
# Listen on all interfaces
listener 1883
allow_anonymous true

# Performance settings
max_queued_messages 1000
max_inflight_messages 20
max_connections 100

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_timestamp true
```

#### Secure Configuration (Production)
```conf
# Listen with authentication
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

# TLS/SSL (recommended for production)
listener 8883
cafile /etc/mosquitto/ca_certificates/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate false

# Access control
acl_file /etc/mosquitto/acl

# Performance
max_queued_messages 10000
max_inflight_messages 50
persistence true
persistence_location /var/lib/mosquitto/
```

### Creating Password File
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd modax_user
# Enter password when prompted
```

### Access Control List (ACL)

Create `/etc/mosquitto/acl`:
```conf
# Field layer devices (read/write sensor topics)
user esp32_user
topic write modax/sensor/data
topic write modax/sensor/safety
topic read modax/control/commands

# Control layer (read all, write control/AI)
user control_layer
topic read modax/sensor/#
topic write modax/control/commands
topic write modax/ai/analysis

# HMI layer (read-only)
user hmi_user
topic read modax/#
```

### Restart Mosquitto
```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

---

## Production Deployment

### Security Checklist

#### Authentication
- [ ] Enable MQTT authentication with strong passwords
- [ ] Implement API key authentication for REST APIs
- [ ] Use JWT tokens for HMI sessions
- [ ] Change all default credentials

#### Encryption
- [ ] Enable TLS/SSL for MQTT (port 8883)
- [ ] Enable HTTPS for Control Layer API
- [ ] Enable HTTPS for AI Layer API
- [ ] Use certificate-based authentication for devices

#### Network Security
- [ ] Implement network segmentation (field/control/office networks)
- [ ] Configure firewall rules per layer
- [ ] Disable unnecessary ports
- [ ] Use VPN for remote access

#### Application Security
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Add audit logging
- [ ] Regular security updates

### Performance Tuning

#### MQTT Broker
```conf
# High-performance settings
max_queued_messages 100000
max_inflight_messages 100
max_connections 1000
memory_limit 128MB
```

#### Control Layer
```python
# config.py adjustments for production
aggregation_window_seconds = 30  # Longer window for less frequent AI analysis
max_data_points = 10000  # More history
```

#### Database Integration (Future)
```python
# Time-series database for historical data
TIMESERIES_DB_URL = "influxdb://localhost:8086"
DATA_RETENTION_DAYS = 365
```

### Monitoring Configuration

#### Prometheus Metrics (Future)
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'modax_control_layer'
    static_configs:
      - targets: ['localhost:8000']
  
  - job_name: 'modax_ai_layer'
    static_configs:
      - targets: ['localhost:8001']
```

#### Logging Configuration
```python
# Enhanced logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/modax/control_layer.log'),
        logging.StreamHandler()
    ]
)

# Log rotation
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    '/var/log/modax/control_layer.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## Configuration Templates

All configuration templates are available in the `config/` directory:

- `control-layer.env.example` - Control Layer environment variables
- `esp32-config.h.example` - ESP32 Field Layer configuration
- `mosquitto.conf.example` - MQTT Broker configuration

### Using Templates

```bash
# Control Layer
cd python-control-layer
cp ../config/control-layer.env.example .env
# Edit .env with your settings
nano .env

# ESP32 Field Layer
cd esp32-field-layer
cp ../config/esp32-config.h.example src/config.h
# Edit config.h with your settings
nano src/config.h

# MQTT Broker
sudo cp config/mosquitto.conf.example /etc/mosquitto/conf.d/modax.conf
# Edit configuration
sudo nano /etc/mosquitto/conf.d/modax.conf
sudo systemctl restart mosquitto
```

---

## Troubleshooting Configuration Issues

### MQTT Connection Problems
```bash
# Test MQTT connection
mosquitto_sub -h localhost -p 1883 -t "modax/#" -v

# Test with authentication
mosquitto_sub -h localhost -p 1883 -t "modax/#" -u modax_user -P password -v
```

### Control Layer Not Starting
```bash
# Check environment variables
env | grep MQTT
env | grep API

# Verify Python dependencies
pip list | grep -E "paho-mqtt|fastapi|uvicorn"
```

### ESP32 Not Connecting
1. Verify WiFi credentials in code
2. Check ESP32 can reach MQTT broker (same network/VLAN)
3. Ensure MQTT port is not blocked by firewall
4. Check ESP32 serial monitor for error messages

### HMI Connection Errors
1. Verify Control Layer is running: `curl http://localhost:8000/health`
2. Check firewall allows port 8000
3. Ensure correct URL in ControlLayerClient.cs
4. Check network connectivity from HMI machine

---

## Best Practices

### Development Environment
- Use default ports (1883, 8000, 8001)
- Allow anonymous MQTT for easier testing
- Use localhost for all connections
- Enable debug logging

### Production Environment
- Change all default ports
- Require authentication everywhere
- Use TLS/SSL for all connections
- Use structured logging with log aggregation
- Implement monitoring and alerting
- Regular backups of configuration and data
- Document all customizations

### Configuration Management
- Store configurations in version control (without secrets)
- Use environment-specific configurations
- Document all non-default settings
- Maintain configuration change log
- Test configuration changes in staging first

---

## Support

For configuration help:
- Check [SETUP.md](SETUP.md) for setup instructions
- Review [ISSUES.md](../ISSUES.md) for known configuration problems
- Check application logs for configuration errors
- Verify all prerequisites are installed

---

**Last Updated:** 2024-12-06  
**Documentation Version:** 1.0
