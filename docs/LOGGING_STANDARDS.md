# MODAX - Logging Standards

This document defines logging standards and conventions for the MODAX system to ensure consistent, structured, and maintainable logs across all components.

## Overview

Consistent logging is crucial for:
- **Debugging** - Quickly identify and diagnose issues
- **Monitoring** - Track system health and performance
- **Auditing** - Review system behavior and changes
- **Analytics** - Analyze patterns and trends

## Log Levels

### Standard Levels

All MODAX components use standard Python logging levels:

| Level | Numeric Value | Usage | Examples |
|-------|--------------|-------|----------|
| **DEBUG** | 10 | Detailed diagnostic information | Raw sensor values, message payloads, internal state |
| **INFO** | 20 | Confirmation of expected operation | System startup, connection established, operation completed |
| **WARNING** | 30 | Unexpected but handled situation | Timeout with retry, deprecated API usage, high resource usage |
| **ERROR** | 40 | Error condition, operation failed | Failed API call, invalid data, connection error |
| **CRITICAL** | 50 | Critical failure, immediate action needed | Safety violation, system shutdown, data corruption |

### When to Use Each Level

#### DEBUG
**Purpose:** Detailed diagnostic information for developers

**Use cases:**
- Raw sensor data values
- MQTT message payloads
- Internal algorithm state
- Performance timing information
- Request/response details

**Example:**
```python
logger.debug(f"Received sensor data: {payload}")
logger.debug(f"Aggregation window: {window_start} to {window_end}")
logger.debug(f"AI analysis took {elapsed:.2f}s")
```

#### INFO
**Purpose:** Confirmation that things are working as expected

**Use cases:**
- Application startup/shutdown
- Configuration loaded
- Connection established
- Major operation completed
- Periodic status updates

**Example:**
```python
logger.info("MODAX Control Layer Starting")
logger.info("Connected to MQTT broker")
logger.info(f"Subscribed to topics: {topics}")
logger.info(f"Processing device {device_id}")
```

#### WARNING
**Purpose:** Something unexpected happened, but system continues

**Use cases:**
- Timeout occurred, retrying
- Deprecated functionality used
- High resource usage
- Minor data quality issues
- Fallback to default value

**Example:**
```python
logger.warning(f"Could not connect to AI layer - is it running?")
logger.warning(f"Unexpected disconnect from MQTT broker, return code: {rc}")
logger.warning(f"SAFETY ALERT from {device_id}: Emergency Stop: {status}")
```

#### ERROR
**Purpose:** Error prevented an operation from completing

**Use cases:**
- Failed network request
- Invalid data format
- File operation failed
- Database error
- Configuration error

**Example:**
```python
logger.error(f"Failed to connect to MQTT broker: {e}")
logger.error(f"Error parsing sensor data: {e}")
logger.error(f"AI layer returned error: {response.status_code}")
```

#### CRITICAL
**Purpose:** System is in critical state, requires immediate action

**Use cases:**
- Safety violation detected
- System shutdown required
- Data corruption
- Resource exhaustion
- Unrecoverable error

**Example:**
```python
logger.critical(f"SAFETY VIOLATION: Emergency stop triggered on {device_id}")
logger.critical(f"System shutdown due to critical error: {e}")
```

## Logging Format

### Standard Format

All Python components use this consistent format:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

**Output example:**
```
2025-12-07 15:30:45,123 - mqtt_handler - INFO - Connected to MQTT broker
2025-12-07 15:30:45,234 - control_layer - INFO - Started data aggregation
2025-12-07 15:30:46,567 - ai_interface - WARNING - AI layer timeout, retrying
```

### Format Components

| Component | Description | Example |
|-----------|-------------|---------|
| `%(asctime)s` | Timestamp | `2025-12-07 15:30:45,123` |
| `%(name)s` | Logger name (module) | `mqtt_handler` |
| `%(levelname)s` | Log level | `INFO`, `WARNING`, `ERROR` |
| `%(message)s` | Log message | `Connected to MQTT broker` |

### Additional Format Options (Future)

For production systems, consider structured logging:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)
```

## Logger Naming Convention

### Module-Level Loggers

Each Python module should create its own logger:

```python
import logging

logger = logging.getLogger(__name__)
```

**Benefits:**
- Identifies source of log messages
- Allows per-module log level configuration
- Follows Python best practices

### Logger Names by Layer

| Layer | Module | Logger Name |
|-------|--------|-------------|
| Control | main.py | `__main__` |
| Control | mqtt_handler.py | `mqtt_handler` |
| Control | control_layer.py | `control_layer` |
| Control | ai_interface.py | `ai_interface` |
| AI | main.py | `__main__` |
| AI | anomaly_detector.py | `anomaly_detector` |
| AI | wear_predictor.py | `wear_predictor` |
| AI | optimizer.py | `optimizer` |

## Message Content Guidelines

### Good Log Messages

✅ **Include context:**
```python
logger.info(f"Processing device {device_id}")
logger.error(f"Failed to connect to {host}:{port}")
```

✅ **Be specific:**
```python
logger.warning(f"Current imbalance: {diff:.2f}A between motors")
logger.error(f"Invalid JSON in message: {e}")
```

✅ **Use consistent terminology:**
```python
logger.info("Connected to MQTT broker")  # Not "Connected to broker"
logger.info("Subscribed to topic: {topic}")  # Not "Sub to {topic}"
```

✅ **Include units:**
```python
logger.debug(f"Temperature: {temp:.1f}°C")
logger.debug(f"Vibration: {vib:.2f} m/s²")
logger.debug(f"Timeout: {timeout}s")
```

### Poor Log Messages

❌ **Too vague:**
```python
logger.error("Error occurred")  # What error? Where?
logger.info("Done")  # What's done?
```

❌ **Too verbose:**
```python
logger.info("Now we are going to process the sensor data...")
logger.debug(f"Full payload: {huge_data_dump}")  # Consider summarizing
```

❌ **Inconsistent:**
```python
logger.info("Connected to mqtt")  # Should be "MQTT broker"
logger.info("Conn established")  # Use full words
```

## Layer-Specific Guidelines

### Field Layer (ESP32)
**Language:** C++  
**Logging:** Serial output

```cpp
Serial.println("[INFO] System initialized");
Serial.printf("[WARN] Temperature high: %.1f°C\n", temp);
Serial.printf("[ERROR] Sensor read failed: %d\n", error_code);
```

**Conventions:**
- Use `[LEVEL]` prefix
- Include units for measurements
- Keep messages concise (limited memory)

### Control Layer (Python)
**Default Level:** INFO

**Key logging points:**
- System startup/shutdown
- MQTT connection state changes
- Device registration
- Data aggregation events
- AI analysis requests
- Safety alerts

**Example:**
```python
logger.info("=" * 60)
logger.info("MODAX Control Layer Starting")
logger.info("=" * 60)
logger.info(f"Connecting to MQTT broker at {host}:{port}")
logger.info(f"API server listening on {api_host}:{api_port}")
```

### AI Layer (Python)
**Default Level:** INFO

**Key logging points:**
- Analysis requests received
- Anomaly detection results
- Wear prediction updates
- Model information
- Performance metrics

**Example:**
```python
logger.info("=" * 60)
logger.info("MODAX AI Layer Starting")
logger.info("=" * 60)
logger.info(f"Analyzing data for device {device_id}")
logger.info(f"Anomaly detected: {result.description}")
```

### HMI Layer (C#)
**Language:** C#  
**Framework:** .NET logging

```csharp
_logger.LogInformation("HMI application started");
_logger.LogWarning("Connection to Control Layer failed, retrying...");
_logger.LogError(ex, "Failed to fetch device data");
```

## Performance Considerations

### Avoid Expensive Operations in Log Statements

❌ **Bad:**
```python
logger.debug(f"Data: {json.dumps(large_object, indent=2)}")  # Expensive even if DEBUG disabled
```

✅ **Good:**
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Data: {json.dumps(large_object, indent=2)}")
```

### Rate Limiting

For frequently occurring events:

```python
import time

last_log_time = 0
LOG_INTERVAL = 10  # seconds

if time.time() - last_log_time > LOG_INTERVAL:
    logger.warning(f"High frequency event (count: {count})")
    last_log_time = time.time()
```

## Configuration

### Environment Variables

Control log level via environment variable:

```bash
export LOG_LEVEL=DEBUG
```

**In code:**
```python
import os
import logging

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level.upper()))
```

### Per-Module Configuration

```python
import logging

# Set root logger to INFO
logging.basicConfig(level=logging.INFO)

# Set specific module to DEBUG
logging.getLogger('mqtt_handler').setLevel(logging.DEBUG)
```

## Log Aggregation and Analysis

### Structured Logging (Future)

For production deployment, consider:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Graylog**
- **Splunk**
- **CloudWatch Logs** (AWS)

### Log Rotation

For file-based logging:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'modax.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Security and Privacy

### Never Log Sensitive Information

❌ **Never log:**
- Passwords
- API keys
- Authentication tokens
- Personal identification numbers
- Credit card data

❌ **Bad:**
```python
logger.debug(f"Connecting with password: {password}")
logger.info(f"API key: {api_key}")
```

✅ **Good:**
```python
logger.debug(f"Connecting with username: {username}")
logger.info("API key configured")
```

### Redact Sensitive Data

If logging is necessary:

```python
def redact_sensitive(data):
    if 'password' in data:
        data['password'] = '***REDACTED***'
    return data

logger.debug(f"Config: {redact_sensitive(config)}")
```

## Examples by Scenario

### System Startup
```python
logger.info("=" * 60)
logger.info("MODAX Control Layer Starting")
logger.info("=" * 60)
logger.info(f"Version: {version}")
logger.info(f"Config loaded from: {config_file}")
logger.info(f"MQTT Broker: {mqtt_host}:{mqtt_port}")
logger.info(f"AI Layer: {ai_url}")
```

### Normal Operation
```python
logger.debug(f"Processing {len(readings)} sensor readings")
logger.info(f"Device {device_id} registered")
logger.debug(f"Aggregated {sample_count} samples over {window}s")
```

### Error Handling
```python
try:
    result = connect_to_mqtt()
except ConnectionError as e:
    logger.error(f"Failed to connect to MQTT broker: {e}", exc_info=True)
    logger.info("Retrying connection in 5s...")
```

### Safety Events
```python
if not status.is_safe():
    logger.warning(
        f"SAFETY ALERT from {device_id}: "
        f"Emergency Stop: {status.emergency_stop}, "
        f"Door Closed: {status.door_closed}, "
        f"Overload: {status.overload_detected}"
    )
```

## Best Practices Summary

### DO:
✅ Use module-level loggers (`logger = logging.getLogger(__name__)`)  
✅ Include context in messages (device ID, operation, values)  
✅ Use appropriate log levels  
✅ Include units for measurements  
✅ Log state changes and important events  
✅ Use consistent terminology  
✅ Include exception info for errors (`exc_info=True`)  

### DON'T:
❌ Log sensitive information (passwords, tokens)  
❌ Use `print()` instead of `logger`  
❌ Log excessively at high frequency  
❌ Use overly verbose debug messages in production  
❌ Ignore log level configuration  
❌ Make expensive operations in log statements  

## References

- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [Twelve-Factor App: Logs](https://12factor.net/logs)

---

**Last Updated:** 2025-12-07  
**Maintained By:** MODAX Development Team
