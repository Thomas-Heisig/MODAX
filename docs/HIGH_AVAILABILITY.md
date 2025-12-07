# MODAX High Availability & Failover Strategy

## Overview
This document describes the high availability (HA) architecture and failover strategies for the MODAX industrial control system to ensure maximum uptime and reliability in production environments.

## Availability Targets

### Service Level Objectives (SLO)
| Component | Target Availability | Max Downtime/Year | Max Downtime/Month |
|-----------|-------------------|-------------------|---------------------|
| Field Layer (ESP32) | 99.9% | 8.76 hours | 43.8 minutes |
| Control Layer | 99.95% | 4.38 hours | 21.9 minutes |
| AI Layer | 99.5% | 43.8 hours | 3.65 hours |
| Database | 99.99% | 52.6 minutes | 4.38 minutes |
| MQTT Broker | 99.99% | 52.6 minutes | 4.38 minutes |
| Overall System | 99.5% | 43.8 hours | 3.65 hours |

## High Availability Architecture

```
┌────────────────────────────────────────────────────────────┐
│ Load Balancer (HAProxy/Nginx)                              │
│ - Health checks                                            │
│ - Traffic distribution                                     │
│ - SSL termination                                          │
└──────────────┬─────────────────────┬───────────────────────┘
               │                     │
       ┌───────┴────────┐    ┌───────┴────────┐
       │ Control Layer  │    │ Control Layer  │
       │ Instance 1     │    │ Instance 2     │
       │ (Active)       │    │ (Active)       │
       └───────┬────────┘    └───────┬────────┘
               │                     │
               └──────────┬──────────┘
                          ↓
               ┌──────────────────────┐
               │ MQTT Broker Cluster  │
               │ - Node 1 (Active)    │
               │ - Node 2 (Active)    │
               │ - Node 3 (Active)    │
               └──────────┬───────────┘
                          ↓
               ┌──────────────────────┐
               │ Database Cluster     │
               │ - Primary (RW)       │
               │ - Standby 1 (RO)     │
               │ - Standby 2 (RO)     │
               └──────────────────────┘
```

## Component-Level HA Strategies

### 1. Control Layer HA

#### Active-Active Configuration
Multiple Control Layer instances run simultaneously, sharing load through a load balancer.

**Benefits:**
- No idle resources
- Better resource utilization
- Horizontal scalability
- Zero downtime updates

**Configuration:**
```yaml
# docker-compose.ha.yml
services:
  control-layer-1:
    image: modax/control-layer:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - INSTANCE_ID=control-1
      - MQTT_CLIENT_ID=control-layer-1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/status"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 40s

  haproxy:
    image: haproxy:2.8
    ports:
      - "8000:8000"
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    depends_on:
      - control-layer-1
```

#### HAProxy Configuration
```
# haproxy/haproxy.cfg
global
    maxconn 4096
    log stdout format raw local0

defaults
    mode http
    timeout connect 5s
    timeout client 50s
    timeout server 50s
    log global
    option httplog

frontend control_layer_frontend
    bind *:8000
    default_backend control_layer_backend

backend control_layer_backend
    balance roundrobin
    option httpchk GET /status
    http-check expect status 200
    
    server control1 control-layer-1:8000 check inter 2s fall 3 rise 2
    server control2 control-layer-2:8000 check inter 2s fall 3 rise 2
```

#### Session Affinity
For stateful operations, use sticky sessions:
```
backend control_layer_backend
    balance roundrobin
    cookie SERVERID insert indirect nocache
    
    server control1 control-layer-1:8000 check cookie control1
    server control2 control-layer-2:8000 check cookie control2
```

### 2. MQTT Broker Clustering

#### Mosquitto Cluster Configuration

**Limitations:** Mosquitto doesn't natively support clustering. Use EMQX or VerneMQ for true HA.

#### EMQX Cluster (Recommended)
```yaml
# docker-compose.mqtt-cluster.yml
services:
  emqx1:
    image: emqx/emqx:5.3.0
    environment:
      - EMQX_NODE_NAME=emqx@emqx1
      - EMQX_CLUSTER__DISCOVERY_STRATEGY=static
      - EMQX_CLUSTER__STATIC__SEEDS=emqx@emqx1,emqx@emqx2,emqx@emqx3
    ports:
      - "1883:1883"
      - "18083:18083"
    healthcheck:
      test: ["CMD", "emqx", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  emqx2:
    image: emqx/emqx:5.3.0
    environment:
      - EMQX_NODE_NAME=emqx@emqx2
      - EMQX_CLUSTER__DISCOVERY_STRATEGY=static
      - EMQX_CLUSTER__STATIC__SEEDS=emqx@emqx1,emqx@emqx2,emqx@emqx3
    ports:
      - "1884:1883"
  
  emqx3:
    image: emqx/emqx:5.3.0
    environment:
      - EMQX_NODE_NAME=emqx@emqx3
      - EMQX_CLUSTER__DISCOVERY_STRATEGY=static
      - EMQX_CLUSTER__STATIC__SEEDS=emqx@emqx1,emqx@emqx2,emqx@emqx3
    ports:
      - "1885:1883"
```

**Features:**
- Automatic node discovery
- Cluster-wide session sharing
- Distributed MQTT bridge
- Split-brain protection

#### Client Configuration
```python
# python-control-layer/mqtt_handler.py
import paho.mqtt.client as mqtt

# Multiple broker addresses for failover
MQTT_BROKERS = [
    ("emqx1", 1883),
    ("emqx2", 1883),
    ("emqx3", 1883)
]

class ResilientMQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id="control-layer", clean_session=False)
        self.broker_index = 0
        self.connect_to_broker()
    
    def connect_to_broker(self):
        """Connect to next available broker"""
        while self.broker_index < len(MQTT_BROKERS):
            host, port = MQTT_BROKERS[self.broker_index]
            try:
                self.client.connect(host, port, keepalive=60)
                logger.info(f"Connected to MQTT broker {host}:{port}")
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to {host}:{port}: {e}")
                self.broker_index += 1
        
        logger.error("All MQTT brokers unreachable")
        self.broker_index = 0  # Reset for retry
        return False
    
    def on_disconnect(self, client, userdata, rc):
        """Automatic reconnection on disconnect"""
        if rc != 0:
            logger.warning(f"Unexpected disconnect: {rc}")
            self.broker_index = (self.broker_index + 1) % len(MQTT_BROKERS)
            self.connect_to_broker()
```

### 3. Database HA (TimescaleDB/PostgreSQL)

#### Streaming Replication

##### Primary Server Configuration
```bash
# postgresql.conf (Primary)
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB
synchronous_commit = on
synchronous_standby_names = 'standby1'

# Enable hot standby (for read replicas)
hot_standby = on
```

##### Standby Server Configuration
```bash
# Create standby from primary
pg_basebackup -h primary-db -D /var/lib/postgresql/data -U replicator -P -v -R

# standby.signal file is created automatically by -R flag
# postgresql.auto.conf contains:
primary_conninfo = 'host=primary-db port=5432 user=replicator password=xxx'
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
```

##### Docker Compose HA Database
```yaml
# docker-compose.db-ha.yml
services:
  postgres-primary:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: modax
      POSTGRES_USER: modax_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-primary-data:/var/lib/postgresql/data
      - ./postgres/primary.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U modax_user"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  postgres-standby1:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: modax
      POSTGRES_USER: modax_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      PGDATA: /var/lib/postgresql/data
    volumes:
      - postgres-standby1-data:/var/lib/postgresql/data
    command: >
      bash -c "
      if [ ! -f /var/lib/postgresql/data/standby.signal ]; then
        pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -P -R
      fi
      postgres -c hot_standby=on
      "
    depends_on:
      - postgres-primary
    ports:
      - "5433:5432"

volumes:
  postgres-primary-data:
  postgres-standby1-data:
```

#### Automatic Failover with Patroni
```yaml
# patroni.yml
scope: modax-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: node1:8008

etcd:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1:5432
  data_dir: /var/lib/postgresql/data
  authentication:
    replication:
      username: replicator
      password: rep_password
    superuser:
      username: postgres
      password: postgres_password
```

### 4. AI Layer HA

#### Stateless Design
AI Layer is designed to be stateless, making HA simple:

**Configuration:**
```yaml
services:
  ai-layer:
    image: modax/ai-layer:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    environment:
      - INSTANCE_ID=${HOSTNAME}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/models/info"]
      interval: 10s
      timeout: 5s
      retries: 3
```

**No shared state:** Each instance maintains its own models and can serve requests independently.

## Heartbeat & Health Monitoring

### Component Health Checks

#### Control Layer Health Endpoint
```python
# python-control-layer/control_api.py
from fastapi import FastAPI, status
from datetime import datetime

@app.get("/health")
async def health_check():
    """Detailed health check for load balancer"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "mqtt": check_mqtt_connection(),
            "database": check_database_connection(),
            "ai_layer": check_ai_layer(),
        }
    }
    
    # If any check fails, return 503
    if not all(health_status["checks"].values()):
        return JSONResponse(
            content=health_status,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    return health_status

def check_mqtt_connection():
    """Check MQTT broker connectivity"""
    return mqtt_handler.is_connected()

def check_database_connection():
    """Check database connectivity"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        return False

def check_ai_layer():
    """Check AI layer availability"""
    try:
        response = requests.get(
            f"{AI_LAYER_URL}/health",
            timeout=2
        )
        return response.status_code == 200
    except Exception:
        return False
```

### Kubernetes Liveness & Readiness Probes

```yaml
# k8s/control-layer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: modax-control-layer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: control-layer
  template:
    metadata:
      labels:
        app: control-layer
    spec:
      containers:
      - name: control-layer
        image: modax/control-layer:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Failover Procedures

### Automatic Failover

#### 1. Control Layer Failover
**Detection:** Load balancer health checks (every 2 seconds)
**Action:** Remove unhealthy instance from pool
**Recovery:** Automatic when instance becomes healthy again
**Time:** < 10 seconds

#### 2. Database Failover (Patroni)
**Detection:** Patroni monitors via etcd (every 10 seconds)
**Action:** Promote standby to primary
**Recovery:** Old primary becomes standby
**Time:** < 30 seconds

```bash
# Manual failover with Patroni
patronictl -c /etc/patroni/patroni.yml failover modax-cluster

# Check cluster status
patronictl -c /etc/patroni/patroni.yml list

# Cluster: modax-cluster
# +--------+--------+-----------+--------+---------+----+-----------+
# | Member | Host   | Role      | State  | TL | Lag in MB |
# +--------+--------+-----------+--------+---------+----+-----------+
# | node1  | node1  | Leader    | running|  5 |           |
# | node2  | node2  | Replica   | running|  5 |         0 |
# +--------+--------+-----------+--------+---------+----+-----------+
```

#### 3. MQTT Broker Failover
**Detection:** Client connection timeout
**Action:** Connect to next broker in list
**Recovery:** Automatic via cluster
**Time:** < 5 seconds

### Manual Failover

#### Database Manual Switchover
```bash
# 1. Check replication lag
psql -h primary-db -U postgres -c "SELECT * FROM pg_stat_replication;"

# 2. Stop writes (optional, for clean switchover)
psql -h primary-db -U postgres -c "ALTER SYSTEM SET default_transaction_read_only = on;"
psql -h primary-db -U postgres -c "SELECT pg_reload_conf();"

# 3. Promote standby
pg_ctl promote -D /var/lib/postgresql/data

# 4. Reconfigure old primary as standby
pg_basebackup -h new-primary -D /var/lib/postgresql/data -U replicator -P -R
```

## Split-Brain Prevention

### Database Split-Brain Protection
```bash
# Use synchronous replication to prevent split-brain
synchronous_commit = on
synchronous_standby_names = 'standby1'

# Quorum-based commit (requires 2 of 3 nodes)
synchronous_standby_names = 'ANY 2 (standby1, standby2)'
```

### MQTT Cluster Split-Brain
EMQX uses distributed consensus (Raft) to prevent split-brain:
```
cluster.autoheal = on
cluster.autoclean = 5m
```

## Data Consistency

### Distributed Transactions
For operations spanning multiple components:

```python
# Pseudo-code for distributed transaction
def process_sensor_data_with_consistency(device_id, data):
    transaction_id = generate_uuid()
    
    try:
        # Phase 1: Prepare
        db_prepared = database.prepare_write(transaction_id, data)
        mqtt_prepared = mqtt.prepare_publish(transaction_id, data)
        
        # Phase 2: Commit
        if db_prepared and mqtt_prepared:
            database.commit(transaction_id)
            mqtt.commit(transaction_id)
        else:
            raise Exception("Preparation failed")
            
    except Exception as e:
        # Rollback on failure
        database.rollback(transaction_id)
        mqtt.rollback(transaction_id)
        logger.error(f"Transaction {transaction_id} failed: {e}")
```

### Eventual Consistency
For non-critical data, use eventual consistency:
- AI analysis results can be slightly stale
- Cached metrics updated every 10 seconds
- Historical data synchronized in batches

## Disaster Recovery

### Backup Strategy
- **Database:** Automated daily backups + WAL archiving
- **Configuration:** Version controlled in Git
- **Secrets:** Stored in HashiCorp Vault with backups
- **Logs:** Retained for 30 days, archived for 1 year

### Recovery Time Objectives (RTO)
| Scenario | RTO | RPO |
|----------|-----|-----|
| Single component failure | < 1 minute | 0 (HA) |
| Database failure | < 5 minutes | < 5 minutes |
| Site failure | < 1 hour | < 15 minutes |
| Complete disaster | < 4 hours | < 1 hour |

### Recovery Procedures
See [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) for detailed procedures.

## Testing HA

### Chaos Engineering

#### Test Scenarios
```bash
# 1. Kill random Control Layer instance
docker kill modax-control-layer-1

# 2. Simulate network partition
iptables -A INPUT -s emqx2 -j DROP

# 3. Overload system
ab -n 10000 -c 100 http://localhost:8000/status

# 4. Database failover
docker stop postgres-primary

# 5. Partial failure (degraded mode)
docker pause ai-layer
```

#### Automated Chaos Testing
```yaml
# chaos-test.yml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: control-layer-kill
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - modax
    labelSelectors:
      app: control-layer
  scheduler:
    cron: '@every 1h'
```

## Monitoring HA

### Key Metrics
- Instance availability percentage
- Failover frequency
- Time to detect failure (TTD)
- Time to recover (TTR)
- Replication lag (database)
- Split-brain incidents

### Alerts
```yaml
# prometheus/alerts/ha.yml
groups:
  - name: high-availability
    rules:
      - alert: InstanceDown
        expr: up{job=~"control-layer|ai-layer"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
      
      - alert: DatabaseReplicationLag
        expr: pg_replication_lag_seconds > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database replication lag is {{ $value }} seconds"
      
      - alert: NoHealthyInstances
        expr: count(up{job="control-layer"} == 1) < 1
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "No healthy Control Layer instances available"
```

## Implementation Roadmap

### Phase 1: Basic HA (Weeks 1-2)
- [ ] Deploy multiple Control Layer instances
- [ ] Configure load balancer
- [ ] Set up health checks
- [ ] Test automatic failover

### Phase 2: Database HA (Weeks 3-4)
- [ ] Configure streaming replication
- [ ] Set up Patroni for automatic failover
- [ ] Test manual and automatic failover
- [ ] Implement backup verification

### Phase 3: MQTT Clustering (Weeks 5-6)
- [ ] Deploy EMQX cluster
- [ ] Configure cluster discovery
- [ ] Update clients for failover
- [ ] Test split-brain scenarios

### Phase 4: Testing & Monitoring (Weeks 7-8)
- [ ] Implement chaos engineering tests
- [ ] Set up HA monitoring dashboards
- [ ] Configure alerting
- [ ] Document runbooks

## Best Practices

### DO:
✅ Test failover procedures regularly  
✅ Monitor replication lag  
✅ Use health checks everywhere  
✅ Document all procedures  
✅ Implement graceful degradation  
✅ Use idempotent operations  

### DON'T:
❌ Rely on single points of failure  
❌ Skip testing disaster recovery  
❌ Ignore split-brain scenarios  
❌ Hardcode instance IDs  
❌ Forget to monitor HA metrics  
❌ Assume HA is "set and forget"  

## References
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
- [Patroni Documentation](https://patroni.readthedocs.io/)
- [EMQX Clustering](https://www.emqx.io/docs/en/v5.0/deploy/cluster/introduction.html)
- [HAProxy Configuration Manual](http://www.haproxy.org/)

---
**Last Updated:** 2025-12-07  
**Maintained By:** MODAX Infrastructure Team
