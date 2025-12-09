# MODAX Best Practices Guide

**Last Updated:** 2025-12-09  
**Version:** 0.3.0

This document provides best practices for developing, deploying, and maintaining MODAX systems.

## Table of Contents

- [Architecture & Design](#architecture--design)
- [Development Practices](#development-practices)
- [Security Best Practices](#security-best-practices)
- [Performance Optimization](#performance-optimization)
- [Testing Strategies](#testing-strategies)
- [Deployment & Operations](#deployment--operations)
- [Monitoring & Observability](#monitoring--observability)
- [Data Management](#data-management)
- [Error Handling](#error-handling)
- [Documentation](#documentation)

## Architecture & Design

### Separation of Concerns

**✅ DO:**
- Keep safety-critical code in the Control Layer
- Use AI Layer only for advisory functions
- Maintain clear boundaries between layers
- Use MQTT for asynchronous device communication
- Use REST APIs for synchronous HMI requests

**❌ DON'T:**
- Put safety decisions in AI Layer
- Mix business logic with presentation logic
- Create circular dependencies between layers
- Use AI for real-time control decisions

**Example:**
```python
# ✅ GOOD: AI provides recommendations, Control decides
ai_recommendation = await ai_layer.get_recommendation(device_data)
if control_layer.validate_safety(ai_recommendation):
    control_layer.apply_optimization(ai_recommendation)

# ❌ BAD: AI directly controls device
ai_layer.set_motor_speed(device_id, speed)  # NEVER DO THIS
```

### Layered Communication

**Communication Flow:**
```
Field Layer (ESP32) → MQTT → Control Layer → REST → HMI Layer
                              ↓ ↑
                          AI Layer (Advisory)
```

**Best Practice:**
- ESP32 publishes sensor data to MQTT topics
- Control Layer subscribes and aggregates data
- HMI polls Control Layer via REST API
- AI Layer is called asynchronously for analysis

### Scalability Considerations

**Design for Scale:**
- Use stateless API endpoints where possible
- Implement horizontal scaling for Python layers
- Use message queues for high-throughput scenarios
- Partition data by device ID or time

**Example Configuration:**
```yaml
# docker-compose.yml
services:
  control-layer:
    deploy:
      replicas: 3
    environment:
      - LOAD_BALANCER=true
```

## Development Practices

### Code Organization

**Directory Structure:**
```
modax/
├── python-control-layer/
│   ├── main.py              # Entry point
│   ├── config/              # Configuration
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   └── tests/               # Unit tests
```

**Naming Conventions:**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

### Configuration Management

**✅ DO:**
- Use environment variables for configuration
- Provide sensible defaults
- Validate configuration at startup
- Document all configuration options
- Use different configs for dev/test/prod

**❌ DON'T:**
- Hardcode configuration values
- Commit secrets to repository
- Use production credentials in development
- Change configuration without documentation

**Example:**
```python
# config.py
import os
from typing import Optional

class Config:
    """Application configuration with validation."""
    
    # Required settings
    MQTT_HOST: str = os.getenv("MQTT_HOST")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    
    # Optional with defaults
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> None:
        """Validate required configuration."""
        if not self.MQTT_HOST:
            raise ValueError("MQTT_HOST is required")
        if not 1 <= self.MQTT_PORT <= 65535:
            raise ValueError("MQTT_PORT must be between 1 and 65535")

config = Config()
config.validate()
```

### Error Handling

**✅ DO:**
- Use specific exception types
- Log errors with context
- Provide actionable error messages
- Handle errors at appropriate level
- Clean up resources in finally blocks

**❌ DON'T:**
- Use bare `except:` clauses
- Suppress errors silently
- Return None on error without logging
- Raise generic Exception types

**Example:**
```python
# ✅ GOOD
class SensorReadError(Exception):
    """Raised when sensor reading fails."""
    pass

def read_sensor(device_id: str) -> float:
    """Read sensor value with proper error handling."""
    try:
        value = sensor.read()
        if value < 0:
            raise SensorReadError(f"Invalid sensor value: {value}")
        return value
    except ConnectionError as e:
        logger.error(f"Connection failed for {device_id}: {e}")
        raise SensorReadError(f"Cannot connect to sensor {device_id}") from e
    except Exception as e:
        logger.exception(f"Unexpected error reading sensor {device_id}")
        raise

# ❌ BAD
def read_sensor(device_id):
    try:
        return sensor.read()
    except:
        return None  # What went wrong? Why?
```

### Logging Standards

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational events
- `WARNING`: Unexpected but handled situations
- `ERROR`: Errors that need attention
- `CRITICAL`: System-critical failures

**Structured Logging:**
```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Structured with context
logger.info(
    "Sensor data received",
    extra={
        "device_id": device_id,
        "temperature": temp,
        "current": current,
        "timestamp": timestamp
    }
)

# ❌ BAD: Unstructured string
logger.info(f"Got data from {device_id}: temp={temp}, current={current}")
```

### Type Safety

**Use Type Hints:**
```python
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class SensorData:
    """Sensor reading with type safety."""
    device_id: str
    temperature: float
    current: float
    timestamp: float
    
    def is_valid(self) -> bool:
        """Check if reading is within valid range."""
        return (
            0 <= self.temperature <= 100 and
            0 <= self.current <= 10
        )

def aggregate_readings(
    readings: List[SensorData],
    window_size: int = 10
) -> Optional[Dict[str, float]]:
    """
    Aggregate sensor readings over time window.
    
    Args:
        readings: List of sensor data points
        window_size: Number of readings to aggregate
        
    Returns:
        Dictionary with aggregated values or None if insufficient data
    """
    if len(readings) < window_size:
        return None
        
    recent = readings[-window_size:]
    return {
        "avg_temperature": sum(r.temperature for r in recent) / window_size,
        "avg_current": sum(r.current for r in recent) / window_size,
        "max_temperature": max(r.temperature for r in recent),
        "max_current": max(r.current for r in recent),
    }
```

## Security Best Practices

### Authentication & Authorization

**✅ DO:**
- Always use authentication in production
- Use strong passwords (min 12 characters)
- Implement API key rotation
- Use different keys for different environments
- Log authentication attempts
- Implement rate limiting

**❌ DON'T:**
- Use default passwords
- Share API keys between services
- Store passwords in plain text
- Allow anonymous access in production

**Implementation:**
```python
# auth.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header."""
    if api_key != CONFIGURED_API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

# Use in endpoints
@app.get("/api/v1/devices", dependencies=[Security(verify_api_key)])
async def get_devices():
    return device_manager.get_all()
```

### TLS/SSL Encryption

**Always Use TLS in Production:**
```python
# MQTT with TLS
mqtt_client.tls_set(
    ca_certs="ca.crt",
    certfile="client.crt",
    keyfile="client.key",
    tls_version=ssl.PROTOCOL_TLSv1_2
)

# API with HTTPS
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="server.key",
    ssl_certfile="server.crt"
)
```

### Secrets Management

**✅ DO:**
- Use environment variables or secret stores
- Rotate secrets regularly
- Use different secrets per environment
- Encrypt secrets at rest
- Limit secret access to necessary services

**❌ DON'T:**
- Commit secrets to git
- Hardcode credentials
- Log sensitive data
- Share secrets via email/chat

**Example with Vault:**
```python
from secrets_manager import SecretsManager

secrets = SecretsManager(vault_url=VAULT_URL)
mqtt_password = secrets.get("mqtt/password")
api_key = secrets.get("api/key")
```

### Input Validation

**Always Validate Input:**
```python
from pydantic import BaseModel, Field, validator

class SensorDataInput(BaseModel):
    """Validated sensor data input."""
    device_id: str = Field(..., min_length=1, max_length=50)
    temperature: float = Field(..., ge=-40, le=125)
    current: float = Field(..., ge=0, le=10)
    
    @validator("device_id")
    def validate_device_id(cls, v):
        """Ensure device_id is alphanumeric."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("device_id must be alphanumeric")
        return v

@app.post("/api/v1/sensor-data")
async def receive_sensor_data(data: SensorDataInput):
    """Endpoint with validated input."""
    return process_sensor_data(data)
```

## Performance Optimization

### Data Aggregation

**Use Efficient Data Structures:**
```python
from collections import deque
import numpy as np

class SensorBuffer:
    """Efficient ring buffer for sensor data."""
    
    def __init__(self, max_size: int = 1000):
        self.temps = deque(maxlen=max_size)
        self.currents = deque(maxlen=max_size)
        
    def add(self, temp: float, current: float):
        """Add reading to buffer."""
        self.temps.append(temp)
        self.currents.append(current)
        
    def get_statistics(self) -> dict:
        """Calculate statistics efficiently."""
        temps_array = np.array(self.temps)
        currents_array = np.array(self.currents)
        
        return {
            "temp_mean": np.mean(temps_array),
            "temp_std": np.std(temps_array),
            "current_mean": np.mean(currents_array),
            "current_std": np.std(currents_array),
        }
```

### Asynchronous Operations

**Use Async for I/O:**
```python
import asyncio
import aiohttp

async def fetch_ai_analysis(device_data: dict) -> dict:
    """Async AI layer request."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{AI_LAYER_URL}/analyze",
            json=device_data,
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            return await response.json()

async def process_multiple_devices(device_ids: List[str]):
    """Process multiple devices concurrently."""
    tasks = [
        fetch_ai_analysis(get_device_data(device_id))
        for device_id in device_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Caching

**Cache Expensive Operations:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAnalyzer:
    """Analyzer with result caching."""
    
    def __init__(self):
        self._cache = {}
        self._cache_duration = timedelta(seconds=30)
    
    def get_analysis(self, device_id: str) -> dict:
        """Get analysis with caching."""
        now = datetime.now()
        
        # Check cache
        if device_id in self._cache:
            cached_time, cached_result = self._cache[device_id]
            if now - cached_time < self._cache_duration:
                return cached_result
        
        # Compute and cache
        result = self._compute_analysis(device_id)
        self._cache[device_id] = (now, result)
        return result
    
    def _compute_analysis(self, device_id: str) -> dict:
        """Expensive analysis computation."""
        # ... complex calculations ...
        pass
```

### Database Optimization

**Use Indexes and Queries Efficiently:**
```sql
-- Create indexes for common queries
CREATE INDEX idx_device_time ON sensor_data(device_id, timestamp DESC);
CREATE INDEX idx_timestamp ON sensor_data(timestamp DESC);

-- Use continuous aggregates (TimescaleDB)
CREATE MATERIALIZED VIEW sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT 
    device_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    AVG(current) AS avg_current,
    MAX(current) AS max_current
FROM sensor_data
GROUP BY device_id, hour;
```

## Testing Strategies

### Unit Testing

**Test Individual Components:**
```python
import pytest
from unittest.mock import Mock, patch

def test_anomaly_detection_normal():
    """Test normal values don't trigger anomaly."""
    detector = AnomalyDetector()
    result = detector.analyze(temperature=25.0, current=1.5)
    
    assert not result.is_anomaly
    assert result.confidence > 0.8

def test_anomaly_detection_high_temp():
    """Test high temperature triggers anomaly."""
    detector = AnomalyDetector()
    result = detector.analyze(temperature=95.0, current=1.5)
    
    assert result.is_anomaly
    assert "temperature" in result.anomaly_types

@patch('mqtt_handler.MQTTClient')
def test_mqtt_reconnect(mock_mqtt):
    """Test MQTT reconnection logic."""
    mock_mqtt.return_value.connect.side_effect = ConnectionError()
    
    handler = MQTTHandler()
    with pytest.raises(ConnectionError):
        handler.connect()
    
    assert mock_mqtt.return_value.connect.call_count > 1
```

### Integration Testing

**Test Component Interactions:**
```python
@pytest.mark.integration
async def test_full_data_flow():
    """Test complete data flow from MQTT to API."""
    # Setup
    mqtt_client = create_mqtt_client()
    api_client = create_api_client()
    
    # Publish sensor data
    test_data = {"device_id": "test1", "temperature": 25.0}
    mqtt_client.publish("modax/devices/test1/sensors", json.dumps(test_data))
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Verify data available via API
    response = await api_client.get("/api/v1/devices/test1/recent")
    assert response.status_code == 200
    assert response.json()["temperature"] == 25.0
```

### Load Testing

**Test Under Load:**
```python
import locust

class ModaxUser(locust.HttpUser):
    """Load test user behavior."""
    
    wait_time = locust.between(1, 3)
    
    @locust.task(3)
    def get_devices(self):
        """Frequently accessed endpoint."""
        self.client.get("/api/v1/devices")
    
    @locust.task(1)
    def get_device_details(self):
        """Less frequent but heavier endpoint."""
        device_id = random.choice(self.device_ids)
        self.client.get(f"/api/v1/devices/{device_id}/history")
```

## Deployment & Operations

### Container Best Practices

**Dockerfile Optimization:**
```dockerfile
# Use specific versions
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 modax
USER modax

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=modax:modax . /app
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Use exec form
ENTRYPOINT ["python", "main.py"]
```

### Docker Compose Setup

**Production-Ready Compose:**
```yaml
version: '3.8'

services:
  mqtt-broker:
    image: eclipse-mosquitto:2
    volumes:
      - ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - mqtt-data:/mosquitto/data
      - mqtt-logs:/mosquitto/log
    ports:
      - "1883:1883"
      - "8883:8883"
    restart: unless-stopped
    
  control-layer:
    build: ./python-control-layer
    depends_on:
      - mqtt-broker
    environment:
      - MQTT_HOST=mqtt-broker
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3

volumes:
  mqtt-data:
  mqtt-logs:
```

### Environment-Specific Configuration

**Use Different Configs:**
```bash
# .env.development
LOG_LEVEL=DEBUG
MQTT_HOST=localhost
API_KEY=dev-key-not-for-production

# .env.production
LOG_LEVEL=INFO
MQTT_HOST=mqtt.production.internal
MQTT_USE_TLS=true
API_KEY_FILE=/run/secrets/api_key
```

### Graceful Shutdown

**Handle Shutdown Signals:**
```python
import signal
import sys

class Application:
    """Application with graceful shutdown."""
    
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
        
        # Clean up resources
        self.mqtt_client.disconnect()
        self.db_connection.close()
        
        logger.info("Shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Main application loop."""
        while self.running:
            # Process work
            pass
```

## Monitoring & Observability

### Metrics Collection

**Export Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
sensor_readings_total = Counter(
    'sensor_readings_total',
    'Total sensor readings received',
    ['device_id', 'sensor_type']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method']
)

active_devices = Gauge(
    'active_devices',
    'Number of active devices'
)

# Use metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Collect request metrics."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_request_duration.labels(
        endpoint=request.url.path,
        method=request.method
    ).observe(duration)
    
    return response
```

### Health Checks

**Implement Comprehensive Health Checks:**
```python
from fastapi import APIRouter, Response
from typing import Dict

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness_check(response: Response) -> Dict:
    """Comprehensive readiness check."""
    checks = {
        "mqtt": await check_mqtt_connection(),
        "database": await check_database_connection(),
        "ai_layer": await check_ai_layer_connection(),
    }
    
    all_healthy = all(check["status"] == "ok" for check in checks.values())
    
    if not all_healthy:
        response.status_code = 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }
```

### Logging Best Practices

**Structured Logging:**
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """JSON structured logger."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log(self, level: str, message: str, **kwargs):
        """Log structured message."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            **kwargs
        }
        
        log_line = json.dumps(log_entry)
        
        if level == "DEBUG":
            self.logger.debug(log_line)
        elif level == "INFO":
            self.logger.info(log_line)
        elif level == "WARNING":
            self.logger.warning(log_line)
        elif level == "ERROR":
            self.logger.error(log_line)
        elif level == "CRITICAL":
            self.logger.critical(log_line)

# Usage
logger = StructuredLogger(__name__)
logger.log(
    "INFO",
    "Sensor data processed",
    device_id="device1",
    temperature=25.0,
    processing_time_ms=15
)
```

## Data Management

### Data Retention

**Implement Retention Policies:**
```sql
-- TimescaleDB retention policy
SELECT add_retention_policy('sensor_data', INTERVAL '90 days');

-- Manual cleanup
DELETE FROM sensor_data 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

### Data Archival

**Archive Old Data:**
```python
async def archive_old_data(cutoff_date: datetime):
    """Archive data older than cutoff date."""
    # Export to archive format
    data = await db.fetch_old_data(cutoff_date)
    
    # Compress and store
    archive_file = f"archive_{cutoff_date.strftime('%Y%m%d')}.json.gz"
    with gzip.open(archive_file, 'wt') as f:
        json.dump(data, f)
    
    # Upload to object storage
    await storage.upload(archive_file, "archives/")
    
    # Delete from active database
    await db.delete_old_data(cutoff_date)
    
    logger.info(f"Archived data before {cutoff_date}")
```

### Backup Strategy

**Regular Backups:**
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump modax_db | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Configuration backup
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" config/

# Retain last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

## Documentation

### Code Documentation

**Document Public APIs:**
```python
def calculate_wear_prediction(
    device_id: str,
    historical_data: List[SensorData],
    prediction_horizon: int = 24
) -> WearPrediction:
    """
    Predict equipment wear for the specified time horizon.
    
    This function uses historical sensor data to estimate the remaining
    useful life of the equipment based on stress accumulation and
    temperature patterns.
    
    Args:
        device_id: Unique identifier for the device
        historical_data: List of historical sensor readings, minimum 100 points
        prediction_horizon: Hours ahead to predict, default 24 hours
        
    Returns:
        WearPrediction object containing:
            - estimated_remaining_life: Hours until maintenance needed
            - confidence: Prediction confidence (0-1)
            - risk_factors: List of contributing factors
            
    Raises:
        ValueError: If historical_data has fewer than 100 points
        DeviceNotFoundError: If device_id is not registered
        
    Example:
        >>> data = get_sensor_data("device1", hours=48)
        >>> prediction = calculate_wear_prediction("device1", data)
        >>> print(f"Maintenance in {prediction.estimated_remaining_life} hours")
        Maintenance in 156 hours
        
    Note:
        Predictions are advisory only and should not be used for
        automated safety decisions.
    """
    if len(historical_data) < 100:
        raise ValueError("Minimum 100 data points required")
    
    # Implementation...
```

### Changelog Management

**Maintain CHANGELOG.md:**
```markdown
# Changelog

All notable changes to MODAX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New feature X

### Changed
- Improved Y

### Deprecated
- Feature Z will be removed in v1.0

### Removed
- Old API endpoint

### Fixed
- Bug in wear prediction

### Security
- Updated dependency X to fix CVE-YYYY-NNNNN

## [0.3.0] - 2025-12-09

### Added
- CONTRIBUTING.md with contribution guidelines
- TROUBLESHOOTING.md with comprehensive guide
- BEST_PRACTICES.md for development standards
```

## Summary

Following these best practices will help you:
- Build robust and maintainable systems
- Prevent common security vulnerabilities
- Optimize performance and scalability
- Ensure reliable operations
- Maintain high code quality

Remember: **Safety first, then security, then features.**

---

For questions or suggestions about these best practices, please open an issue or discussion on GitHub.

Last Updated: 2025-12-09
