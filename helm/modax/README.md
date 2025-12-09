# MODAX Helm Chart

This Helm chart deploys the MODAX (Machine Operations Data Analysis and eXecution) system on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (for persistent volumes)
- cert-manager (optional, for TLS certificate management)

## Components

This chart deploys the following components:

- **MQTT Broker** (Eclipse Mosquitto) - Message broker for IoT devices
- **Control Layer** - Main API and control service
- **AI Layer** - AI/ML analysis service
- **TimescaleDB** - Time-series database for historical data
- **Prometheus** (optional) - Metrics collection
- **Grafana** (optional) - Visualization and dashboards

## Installing the Chart

### Quick Start

```bash
# Add the repository (if published)
helm repo add modax https://thomas-heisig.github.io/MODAX/helm

# Install with default values
helm install modax modax/modax

# Install from local directory
helm install modax ./helm/modax
```

### Installing with Custom Values

Create a `values-prod.yaml` file:

```yaml
ingress:
  enabled: true
  hosts:
    - host: api.modax.yourcompany.com
      paths:
        - path: /
          pathType: Prefix
          service: control-layer
          port: 8000

timescaledb:
  persistence:
    size: 100Gi
    storageClass: fast-ssd

controlLayer:
  replicas: 3
  resources:
    limits:
      cpu: 2000m
      memory: 1Gi

prometheus:
  enabled: true

grafana:
  enabled: true
```

Install with custom values:

```bash
helm install modax ./helm/modax -f values-prod.yaml
```

## Configuration

The following table lists the configurable parameters of the MODAX chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imagePullSecrets` | Global Docker registry secret names | `[]` |
| `global.timezone` | Timezone for all containers | `UTC` |

### MQTT Broker Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mqtt.enabled` | Enable MQTT broker | `true` |
| `mqtt.image.repository` | MQTT broker image repository | `eclipse-mosquitto` |
| `mqtt.image.tag` | MQTT broker image tag | `2.0` |
| `mqtt.replicas` | Number of MQTT broker replicas | `1` |
| `mqtt.service.type` | Kubernetes service type | `LoadBalancer` |
| `mqtt.service.port` | MQTT service port | `8883` |
| `mqtt.persistence.enabled` | Enable persistence | `true` |
| `mqtt.persistence.size` | Persistent volume size | `5Gi` |
| `mqtt.tls.enabled` | Enable TLS | `true` |
| `mqtt.auth.enabled` | Enable authentication | `true` |

### Control Layer Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `controlLayer.enabled` | Enable Control Layer | `true` |
| `controlLayer.image.repository` | Control Layer image | `ghcr.io/thomas-heisig/modax-control-layer` |
| `controlLayer.replicas` | Number of replicas | `2` |
| `controlLayer.service.port` | Service port | `8000` |
| `controlLayer.autoscaling.enabled` | Enable HPA | `true` |
| `controlLayer.autoscaling.minReplicas` | Min replicas | `2` |
| `controlLayer.autoscaling.maxReplicas` | Max replicas | `10` |

### AI Layer Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `aiLayer.enabled` | Enable AI Layer | `true` |
| `aiLayer.image.repository` | AI Layer image | `ghcr.io/thomas-heisig/modax-ai-layer` |
| `aiLayer.replicas` | Number of replicas | `2` |
| `aiLayer.service.port` | Service port | `8001` |
| `aiLayer.autoscaling.enabled` | Enable HPA | `true` |

### TimescaleDB Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `timescaledb.enabled` | Enable TimescaleDB | `true` |
| `timescaledb.image.repository` | TimescaleDB image | `timescale/timescaledb` |
| `timescaledb.persistence.enabled` | Enable persistence | `true` |
| `timescaledb.persistence.size` | PVC size | `50Gi` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts` | Ingress hosts configuration | See values.yaml |
| `ingress.tls` | TLS configuration | See values.yaml |

## Upgrading

To upgrade an existing release:

```bash
helm upgrade modax ./helm/modax -f values-prod.yaml
```

## Uninstalling

To uninstall/delete the `modax` release:

```bash
helm uninstall modax
```

This will remove all Kubernetes resources associated with the chart, except for PersistentVolumeClaims.

To also remove PVCs:

```bash
kubectl delete pvc -l app.kubernetes.io/name=modax
```

## Production Deployment Checklist

Before deploying to production:

- [ ] Configure secrets in `modax-secrets`
- [ ] Set appropriate resource limits
- [ ] Configure ingress with proper domain names
- [ ] Enable TLS/SSL certificates (cert-manager)
- [ ] Configure persistent storage classes
- [ ] Enable monitoring (Prometheus + Grafana)
- [ ] Set up backup procedures for TimescaleDB
- [ ] Configure network policies
- [ ] Review security contexts
- [ ] Configure authentication and authorization
- [ ] Set up log aggregation
- [ ] Configure alerting

## Secrets Management

Create secrets before installation:

```bash
# Create MQTT TLS certificates
kubectl create secret generic mqtt-tls-certs \
  --from-file=ca.crt=./certs/ca.crt \
  --from-file=server.crt=./certs/server.crt \
  --from-file=server.key=./certs/server.key \
  -n modax

# Create application secrets
kubectl create secret generic modax-secrets \
  --from-literal=mqtt-username=control-layer \
  --from-literal=mqtt-password=CHANGE_ME \
  --from-literal=hmi-api-key=CHANGE_ME \
  --from-literal=admin-api-key=CHANGE_ME \
  --from-literal=db-username=modax \
  --from-literal=db-password=CHANGE_ME \
  -n modax
```

## Monitoring

Enable Prometheus and Grafana:

```yaml
prometheus:
  enabled: true

grafana:
  enabled: true
```

Access Grafana:

```bash
kubectl port-forward svc/grafana 3000:3000 -n modax
```

Default username: `admin`
Password: Stored in `modax-secrets`

## Troubleshooting

### Check pod status

```bash
kubectl get pods -n modax
```

### View logs

```bash
# Control Layer
kubectl logs -l app.kubernetes.io/component=control-layer -n modax

# AI Layer
kubectl logs -l app.kubernetes.io/component=ai-layer -n modax

# MQTT Broker
kubectl logs -l app.kubernetes.io/component=mqtt-broker -n modax
```

### Check service endpoints

```bash
kubectl get svc -n modax
kubectl get ingress -n modax
```

### Debug connection issues

```bash
# Port forward to control layer
kubectl port-forward svc/control-layer 8000:8000 -n modax

# Test health endpoint
curl http://localhost:8000/health
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/Thomas-Heisig/MODAX/issues
- Documentation: https://github.com/Thomas-Heisig/MODAX/tree/main/docs
