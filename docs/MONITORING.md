# MODAX Monitoring Stack

## Overview
Comprehensive monitoring is essential for maintaining system health, diagnosing issues, and optimizing performance in industrial control systems. This document outlines the complete monitoring strategy for MODAX using industry-standard tools.

## Monitoring Pillars

### The Three Pillars of Observability
1. **Metrics**: Quantitative measurements (CPU, memory, request rates)
2. **Logs**: Discrete events with context (errors, warnings, audit trails)
3. **Traces**: Request flow through distributed system

## Current State

### Limitations
- ❌ No centralized logging
- ❌ No metrics collection
- ❌ No distributed tracing
- ❌ No alerting system
- ❌ No performance dashboards
- ❌ Manual log analysis only

## Recommended Monitoring Stack

```
┌─────────────────────────────────────────────────────────┐
│ Visualization & Alerting Layer                          │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│ │ Grafana     │  │ AlertManager │  │ PagerDuty/     │  │
│ │ Dashboards  │  │              │  │ Slack/Email    │  │
│ └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
┌─────────────────────────────────────────────────────────┐
│ Data Collection & Storage Layer                         │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│ │ Prometheus  │  │ Loki         │  │ Jaeger/Tempo   │  │
│ │ (Metrics)   │  │ (Logs)       │  │ (Traces)       │  │
│ └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
┌─────────────────────────────────────────────────────────┐
│ Data Sources & Exporters                                │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│ │ Node        │  │ Promtail     │  │ OpenTelemetry  │  │
│ │ Exporter    │  │ (Log agent)  │  │ (Tracing SDK)  │  │
│ │             │  │              │  │                │  │
│ └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                         │
│ Application Components:                                 │
│ - Control Layer (Python)                                │
│ - AI Layer (Python)                                     │
│ - MQTT Broker                                           │
│ - TimescaleDB                                           │
│ - ESP32 Devices                                         │
└─────────────────────────────────────────────────────────┘
```

## Metrics Collection (Prometheus)

### Architecture

Prometheus uses a pull model to scrape metrics from targets at regular intervals.

#### Prometheus Configuration
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'modax-production'
    environment: 'prod'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Load rules
rule_files:
  - "alerts/*.yml"

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Control Layer
  - job_name: 'control-layer'
    static_configs:
      - targets: ['control-layer:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # AI Layer
  - job_name: 'ai-layer'
    static_configs:
      - targets: ['ai-layer:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Node Exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # MQTT Broker
  - job_name: 'mosquitto'
    static_configs:
      - targets: ['mosquitto-exporter:9234']

  # PostgreSQL/TimescaleDB
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

### Application Metrics (Python)

#### Control Layer Metrics
```python
# python-control-layer/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# MQTT metrics
mqtt_messages_received = Counter(
    'mqtt_messages_received_total',
    'Total MQTT messages received',
    ['topic', 'device_id']
)

mqtt_connection_status = Gauge(
    'mqtt_connection_status',
    'MQTT connection status (1=connected, 0=disconnected)'
)

# Device metrics
devices_connected = Gauge(
    'devices_connected',
    'Number of connected devices'
)

sensor_data_age_seconds = Gauge(
    'sensor_data_age_seconds',
    'Age of last sensor data',
    ['device_id']
)

# AI Layer metrics
ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI analysis request duration'
)

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI analysis requests',
    ['status']
)

# System info
system_info = Info(
    'modax_system',
    'MODAX system information'
)
system_info.info({
    'version': '1.0.0',
    'component': 'control-layer'
})
```

#### FastAPI Integration
```python
# python-control-layer/control_api.py
from fastapi import FastAPI, Request
from prometheus_client import make_asgi_app
import time

app = FastAPI()

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record metrics for each request"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/status")
async def status():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
```

#### AI Layer Metrics
```python
# python-ai-layer/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Analysis metrics
ai_analysis_duration_seconds = Histogram(
    'ai_analysis_duration_seconds',
    'Time taken for AI analysis',
    ['analysis_type']
)

ai_anomalies_detected = Counter(
    'ai_anomalies_detected_total',
    'Total anomalies detected',
    ['device_id', 'severity']
)

ai_model_confidence = Histogram(
    'ai_model_confidence',
    'AI model confidence scores',
    ['analysis_type']
)

# Wear prediction metrics
wear_percentage = Gauge(
    'wear_percentage',
    'Current wear percentage',
    ['device_id']
)

remaining_useful_life_hours = Gauge(
    'remaining_useful_life_hours',
    'Predicted remaining useful life',
    ['device_id']
)
```

### Custom Metrics Examples

#### Recording Device Data
```python
# python-control-layer/mqtt_handler.py
def on_message(client, userdata, msg):
    """Handle incoming MQTT message"""
    try:
        data = json.loads(msg.payload)
        device_id = data['device_id']
        
        # Record MQTT metrics
        mqtt_messages_received.labels(
            topic=msg.topic,
            device_id=device_id
        ).inc()
        
        # Update sensor data age
        sensor_data_age_seconds.labels(
            device_id=device_id
        ).set(0)  # Just received
        
        # Store data
        self.sensor_data[device_id] = data
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
```

#### Recording AI Analysis
```python
# python-ai-layer/ai_service.py
@app.post("/analyze")
async def analyze(data: SensorData):
    """Analyze sensor data"""
    start_time = time.time()
    
    try:
        # Perform analysis
        result = perform_analysis(data)
        
        # Record metrics
        duration = time.time() - start_time
        ai_analysis_duration_seconds.labels(
            analysis_type='combined'
        ).observe(duration)
        
        ai_model_confidence.labels(
            analysis_type='combined'
        ).observe(result['confidence'])
        
        if result['is_anomaly']:
            ai_anomalies_detected.labels(
                device_id=data.device_id,
                severity=result['severity']
            ).inc()
        
        ai_requests_total.labels(status='success').inc()
        
        return result
        
    except Exception as e:
        ai_requests_total.labels(status='error').inc()
        raise
```

## Log Aggregation (Loki)

### Architecture

Loki stores logs efficiently and allows querying with LogQL.

#### Loki Configuration
```yaml
# loki/loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2025-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days
```

#### Promtail Configuration
```yaml
# promtail/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Control Layer logs
  - job_name: control-layer
    static_configs:
      - targets:
          - localhost
        labels:
          job: control-layer
          component: control
          __path__: /var/log/modax/control-layer/*.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            device_id: device_id
      - labels:
          level:
          device_id:
      - timestamp:
          source: timestamp
          format: RFC3339

  # AI Layer logs
  - job_name: ai-layer
    static_configs:
      - targets:
          - localhost
        labels:
          job: ai-layer
          component: ai
          __path__: /var/log/modax/ai-layer/*.log

  # Container logs
  - job_name: containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
```

### Structured Logging

#### Python Structured Logger
```python
# python-control-layer/structured_logger.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured JSON logger for Loki"""
    
    def __init__(self, name: str, component: str):
        self.logger = logging.getLogger(name)
        self.component = component
        self._setup_handler()
    
    def _setup_handler(self):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _log(self, level: str, message: str, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'component': self.component,
            'message': message,
            **kwargs
        }
        
        if level == 'ERROR':
            self.logger.error(json.dumps(log_entry))
        elif level == 'WARNING':
            self.logger.warning(json.dumps(log_entry))
        elif level == 'INFO':
            self.logger.info(json.dumps(log_entry))
        else:
            self.logger.debug(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        self._log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log('DEBUG', message, **kwargs)

class JsonFormatter(logging.Formatter):
    """Format logs as JSON"""
    
    def format(self, record):
        return record.getMessage()

# Usage
logger = StructuredLogger('control-layer', 'control')
logger.info('Device connected', device_id='esp32_001', ip='192.168.1.100')
logger.error('MQTT connection failed', error='Connection refused', retry_count=3)
```

### Log Queries (LogQL)

#### Common Queries
```logql
# All errors in last hour
{component="control"} |= "ERROR" | json | level="ERROR"

# Specific device logs
{component="control"} | json | device_id="esp32_001"

# Rate of errors per minute
rate({component=~"control|ai"} |= "ERROR" [1m])

# Top 10 error messages
topk(10, sum by (message) (rate({component="control"} |= "ERROR" [1h])))

# Slow AI requests (>1s)
{component="ai"} | json | duration > 1.0

# MQTT connection issues
{component="control"} |~ "mqtt.*connection.*failed"
```

## Distributed Tracing (Jaeger/Tempo)

### OpenTelemetry Integration

#### Python Instrumentation
```python
# python-control-layer/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def setup_tracing(service_name: str):
    """Configure OpenTelemetry tracing"""
    
    # Create tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Add span processor
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument requests library
    RequestsInstrumentor().instrument()
    
    return trace.get_tracer(service_name)

# Usage in main.py
tracer = setup_tracing("control-layer")
```

#### Manual Span Creation
```python
# python-control-layer/ai_interface.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def get_ai_analysis(device_id: str, data: dict) -> dict:
    """Get AI analysis with tracing"""
    
    with tracer.start_as_current_span("ai_analysis_request") as span:
        # Add attributes
        span.set_attribute("device_id", device_id)
        span.set_attribute("data_points", len(data))
        
        try:
            response = requests.post(
                f"{AI_LAYER_URL}/analyze",
                json=data,
                timeout=AI_LAYER_TIMEOUT
            )
            
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("ai.confidence", response.json().get('confidence'))
            
            return response.json()
            
        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
```

## Alerting (AlertManager)

### Alert Rules

#### prometheus/alerts/system.yml
```yaml
groups:
  - name: system
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for 5 minutes"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 85%"

      # Disk space low
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Available disk space is below 10%"
```

#### prometheus/alerts/application.yml
```yaml
groups:
  - name: modax-application
    interval: 30s
    rules:
      # Service down
      - alert: ServiceDown
        expr: up{job=~"control-layer|ai-layer"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 1 minute"

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is above 5% for 5 minutes"

      # MQTT disconnected
      - alert: MQTTDisconnected
        expr: mqtt_connection_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MQTT connection lost"
          description: "Control layer lost MQTT connection"

      # No recent sensor data
      - alert: StaleDataFrom Device
        expr: sensor_data_age_seconds > 60
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "No data from {{ $labels.device_id }}"
          description: "No sensor data received for over 1 minute"

      # AI analysis slow
      - alert: SlowAIAnalysis
        expr: histogram_quantile(0.95, rate(ai_analysis_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "AI analysis is slow"
          description: "95th percentile analysis time is over 2 seconds"

      # High anomaly rate
      - alert: HighAnomalyRate
        expr: rate(ai_anomalies_detected_total[10m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High anomaly detection rate"
          description: "Detecting more than 10 anomalies per minute"
```

### AlertManager Configuration

#### alertmanager/alertmanager.yml
```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@modax.local'
  smtp_auth_username: 'alerts@modax.local'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  
  routes:
    # Critical alerts to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    
    # All alerts to Slack
    - match_re:
        severity: (critical|warning)
      receiver: 'slack'
    
    # Email for all
    - receiver: 'email'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://webhook-logger:8080/alerts'

  - name: 'email'
    email_configs:
      - to: 'team@modax.local'
        headers:
          Subject: '[MODAX] {{ .GroupLabels.alertname }}'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
        channel: '#modax-alerts'
        title: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

## Grafana Dashboards

### Main System Dashboard

```json
{
  "dashboard": {
    "title": "MODAX System Overview",
    "panels": [
      {
        "title": "System Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"control-layer|ai-layer|mosquitto|timescaledb\"}",
            "legendFormat": "{{ job }}"
          }
        ]
      },
      {
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ job }} - {{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "HTTP Request Duration (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{ job }}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{ job }} - {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Connected Devices",
        "type": "stat",
        "targets": [
          {
            "expr": "devices_connected"
          }
        ]
      },
      {
        "title": "MQTT Messages Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mqtt_messages_received_total[1m])",
            "legendFormat": "{{ device_id }}"
          }
        ]
      },
      {
        "title": "AI Analysis Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "ai_analysis_duration_seconds",
            "legendFormat": "{{ analysis_type }}"
          }
        ]
      },
      {
        "title": "Anomalies Detected",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_anomalies_detected_total[5m])",
            "legendFormat": "{{ device_id }} - {{ severity }}"
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{ instance }}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "{{ instance }}"
          }
        ]
      }
    ]
  }
}
```

## Docker Compose Integration

### monitoring/docker-compose.monitoring.yml
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: modax-prometheus
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
    networks:
      - modax-network
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: modax-loki
    volumes:
      - ./loki:/etc/loki
      - loki-data:/loki
    command: -config.file=/etc/loki/loki-config.yml
    ports:
      - "3100:3100"
    networks:
      - modax-network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: modax-promtail
    volumes:
      - ./promtail:/etc/promtail
      - /var/log/modax:/var/log/modax:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: -config.file=/etc/promtail/promtail-config.yml
    networks:
      - modax-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: modax-grafana
    depends_on:
      - prometheus
      - loki
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - modax-network
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: modax-alertmanager
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - modax-network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: modax-node-exporter
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
    networks:
      - modax-network
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: modax-cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports:
      - "8080:8080"
    networks:
      - modax-network
    restart: unless-stopped

networks:
  modax-network:
    external: true

volumes:
  prometheus-data:
  loki-data:
  grafana-data:
```

## Implementation Roadmap

### Phase 1: Metrics (Weeks 1-2)
- [ ] Set up Prometheus
- [ ] Add metrics to Python applications
- [ ] Configure Node Exporter
- [ ] Create basic Grafana dashboards
- [ ] Test metrics collection

### Phase 2: Logging (Weeks 3-4)
- [ ] Deploy Loki and Promtail
- [ ] Implement structured logging
- [ ] Configure log aggregation
- [ ] Create log dashboards
- [ ] Test log queries

### Phase 3: Alerting (Weeks 5-6)
- [ ] Configure AlertManager
- [ ] Define alert rules
- [ ] Set up notification channels
- [ ] Test alerting workflow
- [ ] Document runbooks

### Phase 4: Tracing (Optional, Weeks 7-8)
- [ ] Deploy Jaeger/Tempo
- [ ] Instrument applications with OpenTelemetry
- [ ] Create trace dashboards
- [ ] Test distributed tracing
- [ ] Performance optimization

## Best Practices

### Metrics
- Use appropriate metric types (Counter, Gauge, Histogram)
- Add meaningful labels (but not too many)
- Use consistent naming conventions
- Document custom metrics
- Set up metric retention policies

### Logging
- Use structured logging (JSON)
- Include context (device_id, user_id, etc.)
- Use appropriate log levels
- Avoid logging sensitive data
- Implement log sampling for high-volume logs

### Alerting
- Define clear alert criteria
- Avoid alert fatigue (tune thresholds)
- Create runbooks for each alert
- Test alerts regularly
- Review and adjust alerts based on false positives

## Conclusion

A comprehensive monitoring stack is essential for maintaining the health and performance of MODAX. By implementing metrics, logging, and tracing, operators can quickly identify and resolve issues, optimize performance, and ensure system reliability.

## References
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
