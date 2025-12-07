# MODAX Data Persistence Strategy

## Overview
This document outlines the data persistence strategy for the MODAX industrial control system, covering time-series data storage, historical data retention, backup strategies, and database architecture.

## Current State

### Limitations
- ❌ No historical data storage (only real-time data in memory)
- ❌ Data lost on system restart
- ❌ No long-term trend analysis
- ❌ No data backup mechanism
- ❌ Limited data analytics capabilities

### Current Data Flow
```
ESP32 → MQTT → Control Layer (Memory) → HMI
                      ↓
                  AI Layer (Memory)
                      ↓
                  Analysis (Lost after use)
```

## Requirements

### Functional Requirements
1. **Time-Series Data Storage**: Store sensor data with timestamps
2. **Historical Analysis**: Query data from hours/days/months ago
3. **Data Retention**: Configurable retention policies
4. **High Write Throughput**: Handle 10Hz × N devices
5. **Fast Querying**: Sub-second response for dashboards
6. **Aggregation**: Pre-compute statistics at different time scales
7. **Backup & Recovery**: Automated backups with point-in-time recovery

### Non-Functional Requirements
- **Availability**: 99.9% uptime
- **Performance**: < 100ms query latency for recent data
- **Scalability**: Support 100+ devices
- **Data Integrity**: No data loss or corruption
- **Storage Efficiency**: Compression and optimization

## Time-Series Database Selection

### Comparison

| Feature | InfluxDB | TimescaleDB | Prometheus | MongoDB |
|---------|----------|-------------|------------|---------|
| Type | Purpose-built | PostgreSQL extension | Metrics-focused | Document DB |
| Query Language | InfluxQL/Flux | SQL | PromQL | MQL |
| Compression | ✅ Excellent | ✅ Good | ✅ Good | ⚠️ Limited |
| SQL Support | ❌ No | ✅ Yes | ❌ No | ⚠️ Limited |
| Python Client | ✅ influxdb-client | ✅ psycopg2 | ✅ prometheus-client | ✅ pymongo |
| Retention Policies | ✅ Native | ✅ Native | ✅ Native | ⚠️ Manual |
| Aggregation | ✅ Continuous queries | ✅ Materialized views | ✅ Recording rules | ✅ Aggregation pipeline |
| Learning Curve | Medium | Low (SQL) | Medium | Medium |
| License | Open source / Commercial | Apache 2.0 | Apache 2.0 | SSPL |

### Recommendation: TimescaleDB

**Rationale**:
1. **SQL Familiarity**: Standard SQL queries (easier for team)
2. **PostgreSQL Ecosystem**: Rich tooling and extensions
3. **Hybrid Workloads**: Can store relational data + time-series
4. **Cost**: Fully open-source (Apache 2.0)
5. **Python Integration**: Well-established libraries

**Alternative**: InfluxDB for pure time-series focus

## Database Architecture

### Hybrid Storage Strategy

```
┌─────────────────────────────────────────────────────┐
│ PostgreSQL + TimescaleDB                            │
│                                                     │
│ ┌─────────────────┐  ┌──────────────────────────┐ │
│ │ Relational Data │  │ Time-Series Data         │ │
│ │                 │  │ (Hypertables)            │ │
│ │ - Devices       │  │                          │ │
│ │ - Users         │  │ - sensor_data            │ │
│ │ - Config        │  │ - safety_events          │ │
│ │ - AI Models     │  │ - ai_analysis_results    │ │
│ │ - Audit Logs    │  │ - control_commands       │ │
│ └─────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Schema Design

#### Device Registry (Relational)
```sql
CREATE TABLE devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    firmware_version VARCHAR(20),
    ip_address INET,
    location VARCHAR(200),
    status VARCHAR(20),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
```

#### Sensor Data (Time-Series Hypertable)
```sql
CREATE TABLE sensor_data (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    current_a DOUBLE PRECISION,
    current_b DOUBLE PRECISION,
    current_c DOUBLE PRECISION,
    vibration DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    rpm INTEGER,
    power_kw DOUBLE PRECISION,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Convert to hypertable
SELECT create_hypertable('sensor_data', 'time');

-- Add compression policy (compress data older than 7 days)
ALTER TABLE sensor_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id'
);

SELECT add_compression_policy('sensor_data', INTERVAL '7 days');

-- Create indexes
CREATE INDEX idx_sensor_device_time ON sensor_data (device_id, time DESC);
```

#### Safety Events (Time-Series)
```sql
CREATE TABLE safety_events (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50),
    is_safe BOOLEAN,
    emergency_stop BOOLEAN,
    door_open BOOLEAN,
    overload_detected BOOLEAN,
    temperature_alarm BOOLEAN,
    description TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

SELECT create_hypertable('safety_events', 'time');

CREATE INDEX idx_safety_device_time ON safety_events (device_id, time DESC);
CREATE INDEX idx_safety_type ON safety_events (event_type, time DESC);
```

#### AI Analysis Results (Time-Series)
```sql
CREATE TABLE ai_analysis (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(50), -- 'anomaly', 'wear', 'optimization'
    confidence DOUBLE PRECISION,
    is_anomaly BOOLEAN,
    anomaly_score DOUBLE PRECISION,
    wear_percentage DOUBLE PRECISION,
    remaining_hours INTEGER,
    recommendations JSONB,
    model_version VARCHAR(20),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

SELECT create_hypertable('ai_analysis', 'time');

CREATE INDEX idx_ai_device_time ON ai_analysis (device_id, time DESC);
CREATE INDEX idx_ai_type ON ai_analysis (analysis_type, time DESC);
```

#### Control Commands (Audit Trail)
```sql
CREATE TABLE control_commands (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    command VARCHAR(100),
    parameters JSONB,
    user_id VARCHAR(50),
    source VARCHAR(50), -- 'hmi', 'api', 'automation'
    status VARCHAR(20), -- 'executed', 'blocked', 'failed'
    reason TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

SELECT create_hypertable('control_commands', 'time');

CREATE INDEX idx_commands_device_time ON control_commands (device_id, time DESC);
CREATE INDEX idx_commands_user ON control_commands (user_id, time DESC);
```

### Continuous Aggregates (Pre-computed Statistics)

#### Hourly Aggregates
```sql
CREATE MATERIALIZED VIEW sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    device_id,
    AVG(current_a) AS avg_current_a,
    MAX(current_a) AS max_current_a,
    MIN(current_a) AS min_current_a,
    AVG(vibration) AS avg_vibration,
    MAX(vibration) AS max_vibration,
    AVG(temperature) AS avg_temperature,
    MAX(temperature) AS max_temperature,
    COUNT(*) AS sample_count
FROM sensor_data
GROUP BY hour, device_id;

-- Refresh policy
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

#### Daily Aggregates
```sql
CREATE MATERIALIZED VIEW sensor_data_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    device_id,
    AVG(current_a) AS avg_current_a,
    MAX(current_a) AS max_current_a,
    MIN(current_a) AS min_current_a,
    STDDEV(current_a) AS stddev_current_a,
    AVG(vibration) AS avg_vibration,
    MAX(vibration) AS max_vibration,
    AVG(temperature) AS avg_temperature,
    MAX(temperature) AS max_temperature,
    COUNT(*) AS sample_count
FROM sensor_data
GROUP BY day, device_id;

SELECT add_continuous_aggregate_policy('sensor_data_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');
```

## Data Retention Policy

### Strategy: Tiered Storage

```
Raw Data:        7 days  (full resolution, 10Hz)
Hourly Agg:      90 days (1-hour buckets)
Daily Agg:       2 years (1-day buckets)
Monthly Agg:     10 years (1-month buckets)
Archived:        Forever (cold storage, compliance)
```

### Implementation
```sql
-- Retention policy for raw sensor data (7 days)
SELECT add_retention_policy('sensor_data', INTERVAL '7 days');

-- Retention policy for AI analysis (30 days)
SELECT add_retention_policy('ai_analysis', INTERVAL '30 days');

-- Safety events kept for 1 year (compliance)
SELECT add_retention_policy('safety_events', INTERVAL '1 year');

-- Control commands kept for 1 year (audit)
SELECT add_retention_policy('control_commands', INTERVAL '1 year');
```

### Monthly Aggregates (Manual Table)
```sql
CREATE TABLE sensor_data_monthly (
    month DATE PRIMARY KEY,
    device_id VARCHAR(50),
    avg_current_a DOUBLE PRECISION,
    avg_vibration DOUBLE PRECISION,
    avg_temperature DOUBLE PRECISION,
    max_current_a DOUBLE PRECISION,
    max_vibration DOUBLE PRECISION,
    max_temperature DOUBLE PRECISION,
    operating_hours INTEGER,
    sample_count BIGINT
);

-- Monthly batch job to populate
INSERT INTO sensor_data_monthly
SELECT
    DATE_TRUNC('month', day) AS month,
    device_id,
    AVG(avg_current_a),
    AVG(avg_vibration),
    AVG(avg_temperature),
    MAX(max_current_a),
    MAX(max_vibration),
    MAX(max_temperature),
    SUM(sample_count) / 36000 AS operating_hours, -- 10Hz = 36000 samples/hour
    SUM(sample_count)
FROM sensor_data_daily
WHERE day >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND day < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY month, device_id;
```

## Python Integration

### Database Connection
```python
# db_config.py
import os
import psycopg2
from psycopg2 import pool

class DatabaseConfig:
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "5432"))
    DATABASE = os.getenv("DB_NAME", "modax")
    USER = os.getenv("DB_USER", "modax_user")
    PASSWORD = os.getenv("DB_PASSWORD", "")
    MIN_CONNECTIONS = int(os.getenv("DB_POOL_MIN", "2"))
    MAX_CONNECTIONS = int(os.getenv("DB_POOL_MAX", "10"))

# db_connection.py
import psycopg2.pool as pool
from contextlib import contextmanager

connection_pool = None

def initialize_pool():
    global connection_pool
    connection_pool = pool.ThreadedConnectionPool(
        DatabaseConfig.MIN_CONNECTIONS,
        DatabaseConfig.MAX_CONNECTIONS,
        host=DatabaseConfig.HOST,
        port=DatabaseConfig.PORT,
        database=DatabaseConfig.DATABASE,
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD
    )

@contextmanager
def get_db_connection():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
```

### Data Writer Service
```python
# data_writer.py
import logging
from datetime import datetime
from typing import Dict, List
import psycopg2.extras
from db_connection import get_db_cursor

logger = logging.getLogger(__name__)

class DataWriter:
    """Service for writing data to TimescaleDB"""
    
    def write_sensor_data(self, device_id: str, data: Dict) -> bool:
        """Write single sensor reading"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO sensor_data (
                        time, device_id, current_a, current_b, current_c,
                        vibration, temperature, rpm, power_kw
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.fromtimestamp(data['timestamp']),
                    device_id,
                    data.get('current_a'),
                    data.get('current_b'),
                    data.get('current_c'),
                    data.get('vibration'),
                    data.get('temperature'),
                    data.get('rpm'),
                    data.get('power_kw')
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write sensor data: {e}")
            return False
    
    def write_sensor_data_batch(self, records: List[tuple]) -> bool:
        """Write multiple sensor readings efficiently"""
        try:
            with get_db_cursor(commit=True) as cursor:
                psycopg2.extras.execute_batch(cursor, """
                    INSERT INTO sensor_data (
                        time, device_id, current_a, current_b, current_c,
                        vibration, temperature, rpm, power_kw
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, records, page_size=1000)
            logger.info(f"Wrote {len(records)} sensor records")
            return True
        except Exception as e:
            logger.error(f"Failed to write batch sensor data: {e}")
            return False
    
    def write_safety_event(self, device_id: str, event: Dict) -> bool:
        """Write safety event"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO safety_events (
                        time, device_id, event_type, is_safe,
                        emergency_stop, door_open, overload_detected,
                        temperature_alarm, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    device_id,
                    event['type'],
                    event['is_safe'],
                    event.get('emergency_stop', False),
                    event.get('door_open', False),
                    event.get('overload_detected', False),
                    event.get('temperature_alarm', False),
                    event.get('description', '')
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write safety event: {e}")
            return False
    
    def write_ai_analysis(self, device_id: str, analysis: Dict) -> bool:
        """Write AI analysis result"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO ai_analysis (
                        time, device_id, analysis_type, confidence,
                        is_anomaly, anomaly_score, wear_percentage,
                        remaining_hours, recommendations, model_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    device_id,
                    'combined',
                    analysis['confidence'],
                    analysis.get('is_anomaly', False),
                    analysis.get('anomaly_score', 0.0),
                    analysis.get('wear_percentage', 0.0),
                    analysis.get('remaining_hours', 0),
                    psycopg2.extras.Json(analysis.get('recommendations', [])),
                    '1.0.0'
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write AI analysis: {e}")
            return False
```

### Data Query Service
```python
# data_reader.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db_connection import get_db_cursor

class DataReader:
    """Service for querying historical data"""
    
    def get_recent_sensor_data(
        self,
        device_id: str,
        minutes: int = 5
    ) -> List[Dict]:
        """Get recent sensor data for a device"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT time, current_a, vibration, temperature
                FROM sensor_data
                WHERE device_id = %s
                  AND time > NOW() - INTERVAL '%s minutes'
                ORDER BY time DESC
            """, (device_id, minutes))
            
            return [
                {
                    'timestamp': row[0].timestamp(),
                    'current': row[1],
                    'vibration': row[2],
                    'temperature': row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def get_hourly_statistics(
        self,
        device_id: str,
        hours: int = 24
    ) -> List[Dict]:
        """Get hourly aggregated statistics"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT
                    hour,
                    avg_current_a,
                    max_current_a,
                    avg_vibration,
                    max_vibration,
                    avg_temperature,
                    sample_count
                FROM sensor_data_hourly
                WHERE device_id = %s
                  AND hour > NOW() - INTERVAL '%s hours'
                ORDER BY hour DESC
            """, (device_id, hours))
            
            return [
                {
                    'hour': row[0],
                    'avg_current': row[1],
                    'max_current': row[2],
                    'avg_vibration': row[3],
                    'max_vibration': row[4],
                    'avg_temperature': row[5],
                    'sample_count': row[6]
                }
                for row in cursor.fetchall()
            ]
    
    def get_safety_events(
        self,
        device_id: Optional[str] = None,
        hours: int = 24,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """Get safety events with optional filters"""
        query = """
            SELECT time, device_id, event_type, is_safe, description
            FROM safety_events
            WHERE time > NOW() - INTERVAL %s
        """
        params = [f'{hours} hours']
        
        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)
        
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)
        
        query += " ORDER BY time DESC LIMIT 100"
        
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            return [
                {
                    'timestamp': row[0],
                    'device_id': row[1],
                    'event_type': row[2],
                    'is_safe': row[3],
                    'description': row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def get_device_uptime(self, device_id: str, days: int = 7) -> Dict:
        """Calculate device uptime statistics"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_samples,
                    COUNT(*) * 0.1 / 3600 as operating_hours,
                    MIN(time) as first_seen,
                    MAX(time) as last_seen
                FROM sensor_data
                WHERE device_id = %s
                  AND time > NOW() - INTERVAL '%s days'
            """, (device_id, days))
            
            row = cursor.fetchone()
            return {
                'total_samples': row[0],
                'operating_hours': row[1],
                'first_seen': row[2],
                'last_seen': row[3]
            }
```

## Backup & Recovery

### Backup Strategy

#### Full Backup (Daily)
```bash
#!/bin/bash
# backup_daily.sh
BACKUP_DIR="/var/backups/modax"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

# PostgreSQL dump with compression
pg_dump -h localhost -U modax_user -d modax \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_DIR}/modax_full_${DATE}.dump"

# Cleanup old backups
find ${BACKUP_DIR} -name "modax_full_*.dump" -mtime +${RETENTION_DAYS} -delete

# Upload to S3 (optional)
aws s3 cp "${BACKUP_DIR}/modax_full_${DATE}.dump" \
    s3://modax-backups/daily/
```

#### Incremental Backup (WAL Archiving)
```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
archive_timeout = 300  # 5 minutes

# Continuous archiving to remote storage
archive_command = 'aws s3 cp %p s3://modax-backups/wal/%f'
```

#### Point-in-Time Recovery (PITR)
```bash
#!/bin/bash
# restore_pitr.sh
RESTORE_TIME="2025-12-07 20:00:00"
BACKUP_FILE="/var/backups/modax/modax_full_20241206.dump"

# Stop PostgreSQL
systemctl stop postgresql

# Restore base backup
pg_restore -h localhost -U modax_user -d modax \
    --clean --if-exists \
    ${BACKUP_FILE}

# Configure recovery
cat > /var/lib/postgresql/recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '${RESTORE_TIME}'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL (will replay WAL logs)
systemctl start postgresql
```

### Disaster Recovery

#### Recovery Time Objective (RTO)
- **Critical**: < 1 hour (system back online)
- **Data**: < 4 hours (full data restoration)

#### Recovery Point Objective (RPO)
- **Maximum data loss**: 5 minutes (WAL archiving interval)
- **Ideal**: 0 data loss with streaming replication

#### Replication Setup
```bash
# Primary Server (postgresql.conf)
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB

# Standby Server
primary_conninfo = 'host=primary-db port=5432 user=replicator password=xxx'
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
hot_standby = on
```

## Monitoring & Alerting

### Key Metrics
```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('modax'));

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Write throughput
SELECT
    COUNT(*) / 60 as inserts_per_second
FROM sensor_data
WHERE time > NOW() - INTERVAL '1 minute';

-- Query performance
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Alerts
- Database size > 80% capacity
- Write throughput < expected (data loss?)
- Slow queries > 1 second
- Replication lag > 10 seconds
- Backup failure
- Connection pool exhausted

## Data Migration

### From In-Memory to Database
```python
# migration_script.py
from datetime import datetime
from data_writer import DataWriter

def migrate_mqtt_handler():
    """Update MQTT handler to write to database"""
    
    # Before: Data only in memory
    def on_message_old(client, userdata, msg):
        data = json.loads(msg.payload)
        self.sensor_data[data['device_id']] = data  # Memory only
    
    # After: Write to database
    def on_message_new(client, userdata, msg):
        data = json.loads(msg.payload)
        # Keep in memory for real-time access
        self.sensor_data[data['device_id']] = data
        # Write to database for history
        self.data_writer.write_sensor_data(
            device_id=data['device_id'],
            data=data
        )
```

## Performance Optimization

### Best Practices
1. **Batch Writes**: Group multiple inserts
2. **Compression**: Enable for old data
3. **Partitioning**: Automatic with TimescaleDB
4. **Indexes**: On frequently queried columns
5. **Connection Pooling**: Reuse connections
6. **Prepared Statements**: Better performance

### Example: Batch Writer
```python
from queue import Queue
from threading import Thread
import time

class BatchWriter:
    def __init__(self, batch_size=1000, flush_interval=1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.buffer = []
        self.writer = DataWriter()
        self.running = False
    
    def start(self):
        self.running = True
        self.worker = Thread(target=self._worker)
        self.worker.start()
    
    def stop(self):
        self.running = False
        self.worker.join()
        self._flush()
    
    def write(self, record):
        self.queue.put(record)
    
    def _worker(self):
        last_flush = time.time()
        
        while self.running or not self.queue.empty():
            try:
                # Get record with timeout
                record = self.queue.get(timeout=0.1)
                self.buffer.append(record)
                
                # Flush if batch size reached
                if len(self.buffer) >= self.batch_size:
                    self._flush()
                    last_flush = time.time()
            except:
                # Timeout - check if flush interval reached
                if time.time() - last_flush >= self.flush_interval:
                    self._flush()
                    last_flush = time.time()
    
    def _flush(self):
        if self.buffer:
            self.writer.write_sensor_data_batch(self.buffer)
            self.buffer = []
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Install and configure TimescaleDB
- [ ] Create database schema
- [ ] Implement data writer service
- [ ] Update MQTT handler to write to database
- [ ] Basic queries for HMI

### Phase 2: Historical Access (Weeks 3-4)
- [ ] Implement data reader service
- [ ] Add continuous aggregates
- [ ] Update API endpoints for historical data
- [ ] HMI charts with historical data

### Phase 3: Backup & Recovery (Weeks 5-6)
- [ ] Automated daily backups
- [ ] WAL archiving setup
- [ ] Test recovery procedures
- [ ] Documentation for operations

### Phase 4: Optimization (Weeks 7-8)
- [ ] Batch writing implementation
- [ ] Compression policies
- [ ] Retention policies
- [ ] Performance tuning
- [ ] Monitoring dashboard

## Conclusion

Implementing a proper data persistence strategy transforms MODAX from a real-time monitoring system to a comprehensive industrial analytics platform. TimescaleDB provides the foundation for long-term data storage, historical analysis, and predictive maintenance capabilities.

**Next Steps**:
1. Set up TimescaleDB instance
2. Implement schema and basic writer
3. Test with single device
4. Gradually migrate all data flows
5. Implement backup procedures

## References
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Time-Series Database Best Practices](https://www.timescale.com/blog/time-series-database-postgresql-10-vs-timescaledb-816/)
- [Industrial Data Historian Design Patterns](https://opcfoundation.org/about/opc-technologies/opc-ua/)
