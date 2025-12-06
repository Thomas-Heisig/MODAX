# MODAX Containerization Guide

## Overview
This document provides a comprehensive guide for containerizing all MODAX components using Docker and orchestrating them for development, testing, and production environments.

## Benefits of Containerization

### Development
- **Consistent Environment**: Same setup across all developer machines
- **Quick Onboarding**: New developers can start in minutes
- **Dependency Isolation**: No conflicts with host system

### Testing
- **Reproducible Tests**: Consistent test environment
- **Parallel Testing**: Run multiple test environments simultaneously
- **CI/CD Integration**: Easy integration with GitHub Actions, GitLab CI

### Production
- **Scalability**: Easy horizontal scaling
- **Resource Management**: CPU and memory limits
- **High Availability**: Automatic container restarts
- **Rolling Updates**: Zero-downtime deployments

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Docker Network: modax-network                           │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ mosquitto    │  │ timescaledb  │  │ grafana      │ │
│  │ (MQTT)       │  │ (Database)   │  │ (Monitoring) │ │
│  │ Port: 1883   │  │ Port: 5432   │  │ Port: 3000   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↑                  ↑                  ↑         │
│  ┌──────┴──────────────────┴──────────────────┴──────┐ │
│  │ control-layer                                      │ │
│  │ (Python FastAPI)                                   │ │
│  │ Port: 8000                                         │ │
│  └──────────────────┬─────────────────────────────────┘ │
│                     ↓                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ai-layer                                        │   │
│  │ (Python FastAPI)                                │   │
│  │ Port: 8001                                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↑                                         ↑
    MQTT (ESP32)                              HMI (Host)
```

## Dockerfile Specifications

### MQTT Broker (Mosquitto)

#### Dockerfile
```dockerfile
# mosquitto/Dockerfile
FROM eclipse-mosquitto:2.0

# Copy configuration
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY passwd /mosquitto/config/passwd
COPY acl /mosquitto/config/acl

# Expose ports
EXPOSE 1883 9001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD mosquitto_sub -t '$SYS/#' -C 1 -i healthcheck -W 3 || exit 1
```

#### mosquitto.conf
```conf
# mosquitto/mosquitto.conf
listener 1883
protocol mqtt

# Authentication
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest stdout
log_type error
log_type warning
log_type notice
log_timestamp true

# Connection limits
max_connections 100
max_queued_messages 1000
```

### TimescaleDB

#### Dockerfile
```dockerfile
# timescaledb/Dockerfile
FROM timescale/timescaledb:latest-pg15

# Copy initialization scripts
COPY init-db.sql /docker-entrypoint-initdb.d/01-init.sql
COPY create-schema.sql /docker-entrypoint-initdb.d/02-schema.sql

# Environment variables set in docker-compose

# Expose port
EXPOSE 5432

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U modax_user -d modax || exit 1
```

#### init-db.sql
```sql
-- timescaledb/init-db.sql
-- Create database and user
CREATE DATABASE modax;
CREATE USER modax_user WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE modax TO modax_user;

-- Connect to modax database
\c modax

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO modax_user;
```

### Python Control Layer

#### Dockerfile
```dockerfile
# python-control-layer/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 modax && chown -R modax:modax /app
USER modax

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

# Run application
CMD ["python", "main.py"]
```

#### requirements.txt (production)
```txt
# python-control-layer/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
paho-mqtt==1.6.1
requests==2.31.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

#### .dockerignore
```
# python-control-layer/.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.venv
venv
.git
.gitignore
.pytest_cache
.coverage
*.log
.env
```

### Python AI Layer

#### Dockerfile
```dockerfile
# python-ai-layer/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 modax && chown -R modax:modax /app
USER modax

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/models/info || exit 1

# Run application
CMD ["python", "main.py"]
```

## Docker Compose Configuration

### Development Environment

#### docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  # MQTT Broker
  mosquitto:
    build:
      context: ./mosquitto
      dockerfile: Dockerfile
    container_name: modax-mosquitto
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - mosquitto-data:/mosquitto/data
      - mosquitto-logs:/mosquitto/log
    networks:
      - modax-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1", "-i", "healthcheck", "-W", "3"]
      interval: 30s
      timeout: 5s
      retries: 3

  # TimescaleDB
  timescaledb:
    build:
      context: ./timescaledb
      dockerfile: Dockerfile
    container_name: modax-db
    environment:
      POSTGRES_DB: modax
      POSTGRES_USER: modax_user
      POSTGRES_PASSWORD: changeme
    ports:
      - "5432:5432"
    volumes:
      - timescaledb-data:/var/lib/postgresql/data
    networks:
      - modax-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U modax_user -d modax"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Control Layer
  control-layer:
    build:
      context: ./python-control-layer
      dockerfile: Dockerfile
    container_name: modax-control
    depends_on:
      mosquitto:
        condition: service_healthy
      timescaledb:
        condition: service_healthy
    environment:
      - MQTT_BROKER_HOST=mosquitto
      - MQTT_BROKER_PORT=1883
      - MQTT_USERNAME=control_layer
      - MQTT_PASSWORD=changeme
      - DB_HOST=timescaledb
      - DB_PORT=5432
      - DB_NAME=modax
      - DB_USER=modax_user
      - DB_PASSWORD=changeme
      - AI_LAYER_URL=http://ai-layer:8001/analyze
      - AI_LAYER_TIMEOUT=5
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    volumes:
      - ./python-control-layer:/app
      - control-logs:/app/logs
    networks:
      - modax-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/status"]
      interval: 30s
      timeout: 5s
      retries: 3

  # AI Layer
  ai-layer:
    build:
      context: ./python-ai-layer
      dockerfile: Dockerfile
    container_name: modax-ai
    environment:
      - LOG_LEVEL=INFO
    ports:
      - "8001:8001"
    volumes:
      - ./python-ai-layer:/app
      - ai-logs:/app/logs
      - ai-models:/app/models
    networks:
      - modax-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/models/info"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Grafana (Optional - for monitoring)
  grafana:
    image: grafana/grafana:10.2.2
    container_name: modax-grafana
    depends_on:
      - timescaledb
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=changeme
      - GF_INSTALL_PLUGINS=
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - modax-network
    restart: unless-stopped

networks:
  modax-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  mosquitto-data:
  mosquitto-logs:
  timescaledb-data:
  control-logs:
  ai-logs:
  ai-models:
  grafana-data:
```

### Production Environment

#### docker-compose.prod.yml
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  mosquitto:
    image: modax/mosquitto:${VERSION:-latest}
    container_name: modax-mosquitto
    ports:
      - "1883:1883"
      - "8883:8883"  # TLS port
    volumes:
      - /var/modax/mosquitto/data:/mosquitto/data
      - /var/modax/mosquitto/log:/mosquitto/log
      - /etc/modax/certs:/mosquitto/certs:ro
    environment:
      - TLS_ENABLED=true
    networks:
      - modax-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  timescaledb:
    image: modax/timescaledb:${VERSION:-latest}
    container_name: modax-db
    environment:
      POSTGRES_DB: modax
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"  # Only localhost
    volumes:
      - /var/modax/db/data:/var/lib/postgresql/data
      - /var/modax/db/backups:/backups
    networks:
      - modax-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  control-layer:
    image: modax/control-layer:${VERSION:-latest}
    container_name: modax-control
    depends_on:
      - mosquitto
      - timescaledb
    environment:
      - MQTT_BROKER_HOST=mosquitto
      - MQTT_BROKER_PORT=8883
      - MQTT_TLS_ENABLED=true
      - MQTT_USERNAME=${MQTT_CONTROL_USER}
      - MQTT_PASSWORD=${MQTT_CONTROL_PASSWORD}
      - DB_HOST=timescaledb
      - DB_PORT=5432
      - DB_NAME=modax
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - AI_LAYER_URL=http://ai-layer:8001/analyze
      - LOG_LEVEL=WARNING
    ports:
      - "8000:8000"
    volumes:
      - /var/modax/control/logs:/app/logs
      - /etc/modax/certs:/app/certs:ro
    networks:
      - modax-network
    restart: always
    deploy:
      replicas: 2  # Multiple instances for HA
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  ai-layer:
    image: modax/ai-layer:${VERSION:-latest}
    container_name: modax-ai
    environment:
      - LOG_LEVEL=WARNING
    ports:
      - "8001:8001"
    volumes:
      - /var/modax/ai/logs:/app/logs
      - /var/modax/ai/models:/app/models
    networks:
      - modax-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

networks:
  modax-network:
    driver: bridge
```

## Build and Deployment Scripts

### Build Script
```bash
#!/bin/bash
# build.sh
set -e

VERSION=${1:-latest}
REGISTRY=${REGISTRY:-modax}

echo "Building MODAX containers version: ${VERSION}"

# Build mosquitto
docker build -t ${REGISTRY}/mosquitto:${VERSION} ./mosquitto

# Build timescaledb
docker build -t ${REGISTRY}/timescaledb:${VERSION} ./timescaledb

# Build control layer
docker build -t ${REGISTRY}/control-layer:${VERSION} ./python-control-layer

# Build AI layer
docker build -t ${REGISTRY}/ai-layer:${VERSION} ./python-ai-layer

echo "Build complete!"
echo "Images:"
docker images | grep ${REGISTRY}
```

### Deployment Script
```bash
#!/bin/bash
# deploy.sh
set -e

ENVIRONMENT=${1:-dev}
VERSION=${2:-latest}

echo "Deploying MODAX to ${ENVIRONMENT} environment"

case $ENVIRONMENT in
  dev)
    docker-compose up -d
    ;;
  prod)
    docker-compose -f docker-compose.prod.yml up -d
    ;;
  *)
    echo "Unknown environment: ${ENVIRONMENT}"
    echo "Usage: ./deploy.sh [dev|prod] [version]"
    exit 1
    ;;
esac

echo "Waiting for services to be healthy..."
sleep 10

docker-compose ps

echo "Deployment complete!"
```

### Update Script (Zero-Downtime)
```bash
#!/bin/bash
# update.sh - Rolling update for production
set -e

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: ./update.sh <version>"
    exit 1
fi

echo "Updating MODAX to version ${NEW_VERSION}"

# Pull new images
docker pull modax/control-layer:${NEW_VERSION}
docker pull modax/ai-layer:${NEW_VERSION}

# Update control-layer with rolling update
echo "Updating control-layer..."
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale control-layer=3 control-layer
sleep 10
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale control-layer=2 control-layer

# Update ai-layer
echo "Updating ai-layer..."
docker-compose -f docker-compose.prod.yml up -d --no-deps ai-layer

# Verify
docker-compose -f docker-compose.prod.yml ps

echo "Update complete!"
```

## Development Workflow

### Quick Start
```bash
# Clone repository
git clone https://github.com/Thomas-Heisig/MODAX.git
cd MODAX

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access services
# Control API: http://localhost:8000
# AI API: http://localhost:8001
# Grafana: http://localhost:3000

# Stop services
docker-compose down
```

### Development with Live Reload
The development docker-compose.yml mounts source code as volumes, enabling live reload:

```bash
# Start services
docker-compose up -d

# Edit code in python-control-layer/
# uvicorn auto-reloads on file changes

# View control-layer logs
docker-compose logs -f control-layer
```

### Running Tests in Containers
```bash
# Run unit tests
docker-compose exec control-layer pytest tests/

# Run with coverage
docker-compose exec control-layer pytest --cov=. tests/

# Run linting
docker-compose exec control-layer flake8 .
docker-compose exec ai-layer flake8 .
```

## CI/CD Integration

### GitHub Actions

#### .github/workflows/docker-build.yml
```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [mosquitto, timescaledb, control-layer, ai-layer]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: modax/${{ matrix.component }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.component }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Monitoring and Logging

### Container Logs
```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f control-layer

# Last 100 lines
docker-compose logs --tail=100 ai-layer

# Export logs
docker-compose logs > modax-logs.txt
```

### Resource Monitoring
```bash
# Container stats
docker stats

# Specific container
docker stats modax-control

# Export metrics
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Health Checks
```bash
# Check service health
docker-compose ps

# Inspect specific container
docker inspect --format='{{.State.Health.Status}}' modax-control

# Run health check manually
docker-compose exec control-layer curl http://localhost:8000/status
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart <service-name>

# Rebuild container
docker-compose up -d --build <service-name>
```

#### Network Issues
```bash
# Check network
docker network ls
docker network inspect modax_modax-network

# Test connectivity
docker-compose exec control-layer ping mosquitto
docker-compose exec control-layer curl http://ai-layer:8001/models/info
```

#### Volume Issues
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect modax_timescaledb-data

# Remove all volumes (WARNING: deletes data)
docker-compose down -v
```

#### Database Connection Issues
```bash
# Connect to database
docker-compose exec timescaledb psql -U modax_user -d modax

# Check database logs
docker-compose logs timescaledb

# Reset database (WARNING: deletes data)
docker-compose down
docker volume rm modax_timescaledb-data
docker-compose up -d
```

## Security Best Practices

### Production Security Checklist
- [ ] Use secrets management (Docker Secrets, Vault)
- [ ] Run containers as non-root users
- [ ] Use read-only filesystems where possible
- [ ] Scan images for vulnerabilities
- [ ] Keep base images updated
- [ ] Use specific image tags (not :latest)
- [ ] Limit container resources
- [ ] Enable TLS for all connections
- [ ] Use private registry for production images
- [ ] Implement network policies

### Secrets Management
```yaml
# docker-compose.prod.yml with secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt
  mqtt_password:
    file: ./secrets/mqtt_password.txt

services:
  control-layer:
    secrets:
      - db_password
      - mqtt_password
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - MQTT_PASSWORD_FILE=/run/secrets/mqtt_password
```

## Backup and Recovery

### Database Backup
```bash
# Backup database
docker-compose exec timescaledb pg_dump -U modax_user modax > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20241206.sql | docker-compose exec -T timescaledb psql -U modax_user -d modax
```

### Volume Backup
```bash
# Backup volume
docker run --rm -v modax_timescaledb-data:/data -v $(pwd):/backup \
    alpine tar czf /backup/db-backup.tar.gz /data

# Restore volume
docker run --rm -v modax_timescaledb-data:/data -v $(pwd):/backup \
    alpine tar xzf /backup/db-backup.tar.gz -C /
```

## Next Steps

### Phase 1: Development (Weeks 1-2)
- [ ] Create Dockerfiles for all components
- [ ] Create docker-compose.yml for development
- [ ] Test local development workflow
- [ ] Document development procedures

### Phase 2: CI/CD (Weeks 3-4)
- [ ] Set up GitHub Actions
- [ ] Automated testing in containers
- [ ] Image scanning and vulnerability checks
- [ ] Automated builds on commit

### Phase 3: Production (Weeks 5-6)
- [ ] Create production docker-compose
- [ ] Implement secrets management
- [ ] Set up monitoring and logging
- [ ] Test deployment procedures
- [ ] Documentation for operations team

## Conclusion

Containerization with Docker provides a solid foundation for developing, testing, and deploying MODAX. This approach ensures consistency across environments, simplifies dependency management, and enables modern DevOps practices.

## References
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices for Writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
