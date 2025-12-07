# MODAX System Improvements

This document describes the immediate improvements implemented in the MODAX system to enhance production readiness, observability, and operational excellence.

## Overview

The following improvements have been implemented across both the Control Layer and AI Layer:

1. ✅ Health-Check Endpoints (/health, /ready)
2. ✅ API Versioning (/api/v1/...)
3. ✅ Standardized Error Response Structure
4. ✅ Rate Limiting for Public API Endpoints
5. ✅ Configurable CORS Headers
6. ✅ Graceful Shutdown for All Services
7. ✅ Environment Variable Validation at Startup
8. ✅ Structured JSON Logs
9. ✅ Prometheus Metrics Endpoints
10. ✅ Docker Health-Checks in Dockerfiles

## 1. Health-Check Endpoints

### Control Layer (Port 8000)

- **`GET /health`**: Basic health check - returns 200 if service is running
- **`GET /ready`**: Readiness check - returns 200 if service is ready to accept requests
  - Checks if control layer is initialized
  - Reports number of devices online
  - Reports system safety status

### AI Layer (Port 8001)

- **`GET /health`**: Basic health check - returns 200 if service is running
- **`GET /ready`**: Readiness check - returns 200 if models are loaded and service is ready

### Example Response:

```json
{
  "status": "healthy",
  "service": "modax-control-layer",
  "version": "1.0.0",
  "timestamp": "2025-12-07T14:00:00.000000"
}
```

## 2. API Versioning

All API endpoints are now versioned under `/api/v1/` prefix:

### Control Layer Endpoints:
- `/api/v1/status` - System status
- `/api/v1/devices` - List connected devices
- `/api/v1/devices/{id}/data` - Device data
- `/api/v1/devices/{id}/history` - Device history
- `/api/v1/devices/{id}/ai-analysis` - AI analysis results
- `/api/v1/control/command` - Send control commands
- `/api/v1/ai/status` - AI layer status
- `/api/v1/export/{id}/csv` - Export data as CSV
- `/api/v1/export/{id}/json` - Export data as JSON
- `/api/v1/export/{id}/statistics` - Export statistics

### AI Layer Endpoints:
- `/api/v1/analyze` - Analyze sensor data
- `/api/v1/models/info` - Model information
- `/api/v1/reset-wear/{device_id}` - Reset wear counter

**Note:** API documentation is automatically available at:
- Control Layer: http://localhost:8000/api/v1/docs
- AI Layer: http://localhost:8001/api/v1/docs

## 3. Standardized Error Response Structure

All errors now return a consistent format:

```json
{
  "error": "HTTPException",
  "message": "Device not found",
  "status_code": 404,
  "timestamp": "2025-12-07T14:00:00.000000",
  "details": {
    "path": "/api/v1/devices/unknown",
    "method": "GET"
  }
}
```

## 4. Rate Limiting

### Configuration

Rate limiting is configurable via environment variables:

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Default rate limit (applies to most endpoints)
RATE_LIMIT_DEFAULT=100/minute
```

### Endpoint-Specific Limits

- **Standard endpoints**: 100 requests/minute (configurable)
- **Control commands**: 10 requests/minute (stricter)
- **Data exports**: 10 requests/minute (stricter)
- **Maintenance operations**: 10 requests/minute (stricter)

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1702134000
```

## 5. Configurable CORS Headers

CORS configuration is now environment-driven:

```bash
# Comma-separated list of allowed origins (* for all)
CORS_ORIGINS=http://localhost:3000,https://example.com

# Allow credentials
CORS_ALLOW_CREDENTIALS=true

# Allowed methods (comma-separated or *)
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE

# Allowed headers (comma-separated or *)
CORS_ALLOW_HEADERS=*
```

**Default**: All origins allowed (`*`) for development convenience.
**Production**: Configure specific origins for security.

## 6. Graceful Shutdown

Both services now handle shutdown signals (SIGINT, SIGTERM) gracefully:

- Clean disconnection from MQTT broker
- Proper resource cleanup
- Logs shutdown events

Example:
```bash
# Services respond to Ctrl+C or docker stop
docker stop modax-control-layer
# Logs: "Received shutdown signal, exiting gracefully..."
```

## 7. Environment Variable Validation

Configuration is validated at startup. Services exit with error if invalid:

### Control Layer Validation:
- `API_PORT` must be 1-65535
- `API_KEY` must be set if `API_KEY_ENABLED=true`
- `AI_LAYER_TIMEOUT` must be >= 1 second
- `MQTT_BROKER_PORT` must be 1-65535
- `MQTT_CA_CERTS` must be set if `MQTT_USE_TLS=true`

### AI Layer Validation:
- `AI_PORT` must be 1-65535

Invalid configuration example:
```bash
API_PORT=99999 python main.py
# Output:
# Configuration validation failed:
#   - Invalid API_PORT: 99999 (must be 1-65535)
```

## 8. Structured JSON Logs

Logs are now output in JSON format for easy parsing and analysis:

### Configuration:
```bash
# Enable JSON logging (default: true)
USE_JSON_LOGS=true
```

### Example Log Output:
```json
{
  "timestamp": "2025-12-07T14:00:00.123456",
  "logger": "control_layer",
  "level": "INFO",
  "message": "MQTT connected",
  "component": "mqtt_handler",
  "broker": "localhost:1883"
}
```

### Benefits:
- Easy integration with log aggregation tools (ELK, Loki, etc.)
- Structured querying and filtering
- Better correlation between events
- Machine-readable format

## 9. Prometheus Metrics Endpoints

Both services expose metrics at `/metrics` for Prometheus scraping:

### Control Layer Metrics:
- `control_api_requests_total` - Total API requests (by method, endpoint, status)
- `control_api_request_duration_seconds` - Request duration histogram
- `control_devices_online` - Number of devices currently online
- `control_system_safe` - System safety status (1=safe, 0=unsafe)

### AI Layer Metrics:
- `ai_analysis_requests_total` - Total analysis requests (by status)
- `ai_analysis_duration_seconds` - Analysis duration histogram
- `ai_anomalies_detected_total` - Total anomalies detected (by type)

### Prometheus Configuration:

A sample Prometheus configuration is provided at `config/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'modax-control-layer'
    static_configs:
      - targets: ['control-layer:8000']
    metrics_path: '/metrics'

  - job_name: 'modax-ai-layer'
    static_configs:
      - targets: ['ai-layer:8001']
    metrics_path: '/metrics'
```

### Example Queries:

```promql
# Request rate per second
rate(control_api_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, control_api_request_duration_seconds_bucket)

# Number of devices online
control_devices_online

# Anomaly detection rate
rate(ai_anomalies_detected_total[1h])
```

## 10. Docker Health-Checks

Dockerfiles now include health check configurations:

### Control Layer Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"
```

### AI Layer Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()"
```

### Docker Compose Integration:

The `docker-compose.yml` includes health checks for all services:

```yaml
services:
  mqtt:
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1"]
      interval: 30s
      timeout: 10s
      retries: 3

  control-layer:
    # Health check automatically used from Dockerfile
    depends_on:
      - mqtt
      - ai-layer

  ai-layer:
    # Health check automatically used from Dockerfile
```

### Health Status Commands:

```bash
# Check health status
docker ps

# View health logs
docker inspect --format='{{json .State.Health}}' modax-control-layer | jq

# Wait for healthy status
docker-compose up -d
docker-compose ps  # Wait until all show "healthy"
```

## Deployment

### Quick Start with Docker Compose:

```bash
# Start all services
docker-compose up -d

# Check health status
docker-compose ps

# View logs
docker-compose logs -f

# Start with monitoring stack
docker-compose --profile monitoring up -d

# Stop all services
docker-compose down
```

### Environment Variables:

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
AI_HOST=0.0.0.0
AI_PORT=8001

# MQTT Configuration
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883

# Logging
USE_JSON_LOGS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute

# CORS (configure for production)
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# AI Layer
AI_ENABLED=true
AI_LAYER_URL=http://ai-layer:8001/api/v1/analyze
AI_LAYER_TIMEOUT=5
```

### Production Considerations:

1. **Security**:
   - Configure specific CORS origins
   - Enable API authentication (`API_KEY_ENABLED=true`)
   - Use TLS for MQTT (`MQTT_USE_TLS=true`)

2. **Monitoring**:
   - Deploy Prometheus for metrics collection
   - Deploy Grafana for visualization
   - Configure Loki for log aggregation

3. **Rate Limiting**:
   - Adjust limits based on expected load
   - Consider per-client rate limiting

4. **Health Checks**:
   - Configure load balancer to use `/ready` endpoint
   - Set appropriate timeouts and retries

## Testing

All improvements are covered by tests:

### Run Tests:
```bash
# Control Layer
cd python-control-layer
python -m pytest -v

# AI Layer
cd python-ai-layer
python -m pytest -v
```

### Test Coverage:
- 69 tests passing in Control Layer
- 57 tests passing in AI Layer
- 126 total tests

## Backward Compatibility

- Old endpoint paths (e.g., `/analyze`) still work but are not documented
- Recommended to migrate to `/api/v1/` endpoints
- JSON logging can be disabled with `USE_JSON_LOGS=false`
- Rate limiting can be disabled with `RATE_LIMIT_ENABLED=false`

## Migration Guide

### For HMI/Client Applications:

Update endpoint URLs to use `/api/v1/` prefix:

```python
# Old
response = requests.get("http://localhost:8000/status")

# New
response = requests.get("http://localhost:8000/api/v1/status")
```

### For Monitoring:

Add Prometheus scrape configurations:

```yaml
- job_name: 'modax'
  static_configs:
    - targets: 
        - 'control-layer:8000'
        - 'ai-layer:8001'
  metrics_path: '/metrics'
```

### For Deployment:

Use the provided Dockerfiles and docker-compose.yml:

```bash
# Build and start
docker-compose build
docker-compose up -d

# Monitor health
watch docker-compose ps
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Configuration](docs/CONFIGURATION.md)
- [Monitoring](docs/MONITORING.md)
- [Containerization](docs/CONTAINERIZATION.md)

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review component-specific READMEs
