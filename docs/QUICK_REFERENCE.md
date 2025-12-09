# MODAX Quick Reference Guide

**Version:** 0.2.0  
**Last Updated:** 2025-12-09  
**Purpose:** Quick reference for developers and operators

---

## 🚀 Quick Start

### Start the System

```bash
# Using Docker Compose (Recommended)
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Points

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| Control Layer API | http://localhost:8000 | 8000 | Main API & HMI backend |
| AI Layer API | http://localhost:8001 | 8001 | AI analysis services |
| MQTT Broker | mqtt://localhost | 1883 | Device communication |
| API Documentation | http://localhost:8000/docs | 8000 | Interactive API docs |

---

## 📚 Documentation Index

### Essential Documents (Start Here)
1. **[README.md](../README.md)** - Project overview and introduction
2. **[SETUP.md](SETUP.md)** - Installation and setup instructions
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
4. **[API.md](API.md)** - API reference
5. **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration guide

### Implementation Guides
- **[SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)** - Security setup
- **[AUTHENTICATION_IMPLEMENTATION_GUIDE.md](AUTHENTICATION_IMPLEMENTATION_GUIDE.md)** - Authentication setup
- **[CONTAINERIZATION.md](CONTAINERIZATION.md)** - Docker deployment
- **[GITOPS_DEPLOYMENT.md](GITOPS_DEPLOYMENT.md)** - GitOps with ArgoCD/Flux

### Feature Documentation
- **[CNC_FEATURES.md](CNC_FEATURES.md)** - CNC machine functionality
- **[EXTENDED_GCODE_SUPPORT.md](EXTENDED_GCODE_SUPPORT.md)** - G-code interpreter
- **[HMI_ENHANCEMENTS.md](HMI_ENHANCEMENTS.md)** - HMI features (Dark mode, i18n, etc.)
- **[OPC_UA_INTEGRATION.md](OPC_UA_INTEGRATION.md)** - OPC UA integration
- **[MQTT_SPARKPLUG_B.md](MQTT_SPARKPLUG_B.md)** - MQTT Sparkplug B protocol

### Operations & Maintenance
- **[MONITORING.md](MONITORING.md)** - Monitoring with Prometheus/Grafana
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[BACKUP_RECOVERY.md](BACKUP_RECOVERY.md)** - Backup and recovery procedures
- **[HIGH_AVAILABILITY.md](HIGH_AVAILABILITY.md)** - HA deployment
- **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - Best practices

### Advanced Topics
- **[DATA_PERSISTENCE.md](DATA_PERSISTENCE.md)** - TimescaleDB integration
- **[SCHEMA_MIGRATION.md](SCHEMA_MIGRATION.md)** - Database migrations
- **[NETWORK_ARCHITECTURE.md](NETWORK_ARCHITECTURE.md)** - Network design & OT/IT separation
- **[EXTERNAL_INTEGRATIONS.md](EXTERNAL_INTEGRATIONS.md)** - Third-party integrations
- **[ADVANCED_CNC_INDUSTRY_4_0.md](ADVANCED_CNC_INDUSTRY_4_0.md)** - Industry 4.0 features

### Reference Materials
- **[GLOSSARY.md](GLOSSARY.md)** - Technical terms glossary (250+ entries)
- **[FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md)** - Function documentation
- **[INDEX.md](INDEX.md)** - Complete documentation index

---

## 🔧 Common Tasks

### Check System Status

```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8001/health

# Get detailed readiness status
curl http://localhost:8000/ready
curl http://localhost:8001/ready
```

### View System Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics

# Cache statistics
curl http://localhost:8000/api/v1/cache/stats
```

### List Connected Devices

```bash
# Get all devices
curl http://localhost:8000/api/v1/devices

# Get specific device data
curl http://localhost:8000/api/v1/devices/{device_id}/data
```

### Export Data

```bash
# Export as CSV
curl http://localhost:8000/api/v1/export/{device_id}/csv?start_time=...&end_time=...

# Export as JSON
curl http://localhost:8000/api/v1/export/{device_id}/json?start_time=...&end_time=...

# Get statistics
curl http://localhost:8000/api/v1/export/{device_id}/statistics?start_time=...&end_time=...
```

### CNC Operations

```bash
# Load G-code program
curl -X POST http://localhost:8000/api/v1/cnc/program \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_001", "program": "G0 X10 Y20\nG1 Z5 F100"}'

# Start CNC program
curl -X POST http://localhost:8000/api/v1/cnc/start \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_001"}'

# Emergency stop
curl -X POST http://localhost:8000/api/v1/cnc/emergency-stop \
  -H "Content-Type: application/json" \
  -d '{"device_id": "esp32_001"}'
```

---

## ⚙️ Configuration

### Essential Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
AI_HOST=0.0.0.0
AI_PORT=8001

# MQTT Configuration
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883
MQTT_USE_TLS=false

# Database (TimescaleDB)
DB_ENABLED=true
DB_HOST=timescaledb
DB_PORT=5432
DB_NAME=modax
DB_USER=modax_user

# Security
API_KEY_ENABLED=false
MQTT_USE_AUTH=false

# Features
USE_JSON_LOGS=true
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=*

# AI Layer
AI_ENABLED=true
AI_LAYER_URL=http://ai-layer:8001/api/v1/analyze
AI_LAYER_TIMEOUT=5
```

See [CONFIGURATION.md](CONFIGURATION.md) for complete list.

---

## 🔒 Security

### Production Security Checklist

- [ ] Enable MQTT authentication (`MQTT_USE_AUTH=true`)
- [ ] Enable MQTT TLS (`MQTT_USE_TLS=true`)
- [ ] Enable API authentication (`API_KEY_ENABLED=true`)
- [ ] Configure specific CORS origins (not `*`)
- [ ] Use strong database passwords
- [ ] Enable structured JSON logging
- [ ] Configure Prometheus metrics authentication
- [ ] Set up network segmentation (OT/IT separation)
- [ ] Enable audit logging
- [ ] Regular security updates

See [SECURITY.md](SECURITY.md) and [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md) for details.

---

## 📊 Monitoring

### Metrics Available

**Control Layer:**
- `control_api_requests_total` - API request counter
- `control_api_request_duration_seconds` - Request duration histogram
- `control_devices_online` - Number of connected devices
- `control_system_safe` - Safety status (1=safe, 0=unsafe)
- `control_cache_hits_total` / `control_cache_misses_total` - Cache performance

**AI Layer:**
- `ai_analysis_requests_total` - Analysis request counter
- `ai_analysis_duration_seconds` - Analysis duration histogram
- `ai_anomalies_detected_total` - Anomaly counter by type

### Grafana Dashboards

Pre-configured dashboards available in `config/grafana/dashboards/`:
- `modax-overview.json` - System overview
- `modax-control-layer.json` - Control layer metrics
- `modax-ai-layer.json` - AI layer metrics

See [MONITORING.md](MONITORING.md) for setup instructions.

---

## 🧪 Testing

### Run Tests

```bash
# Control Layer tests
cd python-control-layer
python -m pytest -v

# AI Layer tests
cd python-ai-layer
python -m pytest -v

# With coverage
cd python-control-layer
./test_with_coverage.sh

# Performance tests
python test_performance.py

# Load tests
python test_load.py
```

### Current Test Coverage
- Control Layer: **96-97%** (42+ unit tests)
- AI Layer: **96-97%** (56+ unit tests)
- End-to-End: **11 tests**
- Total: **123+ tests**

---

## 🐛 Troubleshooting

### Common Issues

**Issue: Services won't start**
- Check Docker is running: `docker ps`
- Check logs: `docker-compose logs`
- Verify ports are available: `netstat -tulpn | grep -E '8000|8001|1883'`

**Issue: No devices connecting**
- Check MQTT broker: `mosquitto_sub -t '#' -v`
- Verify ESP32 configuration
- Check network connectivity

**Issue: AI analysis not working**
- Verify AI layer is running: `curl http://localhost:8001/health`
- Check AI_LAYER_URL configuration
- Review AI layer logs

**Issue: High CPU usage**
- Check cache hit rate: `curl http://localhost:8000/api/v1/cache/stats`
- Review Prometheus metrics
- Adjust update intervals

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete troubleshooting guide.

---

## 📝 Development

### Code Structure

```
MODAX/
├── esp32-field-layer/       # ESP32 firmware (C++)
├── python-control-layer/    # Control Layer (FastAPI)
├── python-ai-layer/         # AI Layer (FastAPI)
├── csharp-hmi-layer/        # HMI (C# WinForms)
├── docs/                    # Documentation
├── config/                  # Configuration files
├── k8s/                     # Kubernetes manifests
├── helm/                    # Helm charts
└── protobuf/               # Protocol definitions
```

### Coding Standards

- **Python:** PEP 8, type hints, docstrings
- **C++:** Google C++ Style Guide
- **C#:** Microsoft C# Coding Conventions
- **Git:** Conventional Commits

### Linting & Formatting

```bash
# Python
cd python-control-layer
./lint.sh

# Run all linters
flake8 .
pylint *.py
mypy .
```

---

## 🚢 Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Using kubectl
kubectl apply -k k8s/overlays/production/

# Using Helm
helm install modax helm/modax/ -f helm/modax/values-prod.yaml
```

### GitOps (ArgoCD)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Deploy MODAX application
kubectl apply -f k8s/argocd/application.yaml
```

See [CONTAINERIZATION.md](CONTAINERIZATION.md) and [GITOPS_DEPLOYMENT.md](GITOPS_DEPLOYMENT.md) for details.

---

## 📦 Key Features

### ✅ Implemented Features

- ✅ **Multi-layer architecture** (Field, Control, AI, HMI)
- ✅ **Real-time data processing** (MQTT pub/sub)
- ✅ **AI-powered analysis** (Anomaly detection, wear prediction, optimization)
- ✅ **CNC machine control** (G-code interpreter, motion control, tool management)
- ✅ **WebSocket support** (Real-time HMI updates)
- ✅ **TimescaleDB integration** (Historical data storage)
- ✅ **Prometheus metrics** (System monitoring)
- ✅ **Health checks** (/health, /ready endpoints)
- ✅ **API versioning** (/api/v1/...)
- ✅ **Rate limiting** (Configurable per endpoint)
- ✅ **CORS support** (Configurable origins)
- ✅ **Structured logging** (JSON format)
- ✅ **Docker containers** (All layers)
- ✅ **Kubernetes support** (Manifests + Helm charts)
- ✅ **CI/CD pipeline** (GitHub Actions)
- ✅ **Authentication** (API keys, MQTT auth)
- ✅ **TLS/SSL support** (Production security)
- ✅ **Cache system** (TTL-based, thread-safe)
- ✅ **Data export** (CSV, JSON, statistics)

### 📋 Planned Features

See [TODO.md](../TODO.md) for roadmap and [ISSUES.md](../ISSUES.md) for known issues.

---

## 🆘 Getting Help

1. **Check documentation:** Start with [INDEX.md](INDEX.md)
2. **Search issues:** See [ISSUES.md](../ISSUES.md)
3. **Troubleshooting guide:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Best practices:** See [BEST_PRACTICES.md](BEST_PRACTICES.md)
5. **GitHub Issues:** Open an issue on GitHub
6. **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 📄 License & Contributing

- **License:** See [LICENSE](../LICENSE)
- **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Changelog:** See [CHANGELOG.md](../CHANGELOG.md)

---

**Quick Links:**
- [Main README](../README.md)
- [Documentation Index](INDEX.md)
- [TODO List](../TODO.md)
- [Known Issues](../ISSUES.md)
- [Changelog](../CHANGELOG.md)
