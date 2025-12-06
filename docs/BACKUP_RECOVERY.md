# MODAX Backup & Recovery Procedures

## Overview
This document describes comprehensive backup and recovery procedures for the MODAX industrial control system, ensuring data protection and business continuity.

## Backup Strategy

### 3-2-1 Backup Rule
- **3** copies of data
- **2** different media types
- **1** off-site backup

```
┌─────────────────────────────────────────────────────────┐
│ Primary Data (Production)                               │
│ - TimescaleDB                                           │
│ - Configuration files                                   │
│ - AI models                                             │
│ - Application code                                      │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
┌───────────────┐  ┌──────────────┐
│ Backup Copy 1 │  │ Backup Copy 2│
│ (Local NAS)   │  │ (Remote NAS) │
│ - Daily       │  │ - Weekly     │
│ - Incremental │  │ - Full       │
└───────────────┘  └──────┬───────┘
                          ↓
                   ┌──────────────┐
                   │ Backup Copy 3│
                   │ (Cloud S3)   │
                   │ - Monthly    │
                   │ - Archive    │
                   └──────────────┘
```

## What to Backup

### Critical Data (Daily)
1. **Database (TimescaleDB)**
   - All sensor data tables
   - Configuration tables
   - User tables
   - AI analysis results
   - Retention: 30 days

2. **Configuration Files**
   - docker-compose.yml
   - .env files (encrypted)
   - nginx/haproxy configs
   - MQTT broker configs
   - Retention: 90 days

3. **Application State**
   - AI model weights
   - Calibration data
   - Device registrations
   - Retention: 30 days

### Important Data (Weekly)
1. **Application Logs**
   - Last 7 days of logs
   - Retention: 90 days

2. **System State**
   - Docker images (tagged releases)
   - Container configurations
   - Retention: 12 weeks

### Archival Data (Monthly)
1. **Historical Data**
   - Aggregated sensor data (> 30 days)
   - Monthly reports
   - Retention: 7 years (compliance)

2. **Audit Logs**
   - Security events
   - Configuration changes
   - Retention: 7 years (compliance)

## Backup Schedules

### Automated Backup Schedule
```
Daily Backups:
  Time: 02:00 UTC
  Type: Incremental
  Duration: ~30 minutes
  Data: Database + Configs

Weekly Backups:
  Day: Sunday 03:00 UTC
  Type: Full
  Duration: ~2 hours
  Data: Database + Logs + State

Monthly Backups:
  Day: 1st of month, 04:00 UTC
  Type: Archive
  Duration: ~4 hours
  Data: Everything + Historical
```

## Database Backup

### PostgreSQL/TimescaleDB Full Backup
```bash
#!/bin/bash
# backup_database_full.sh

set -e

BACKUP_DIR="/var/backups/modax/database"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Full database dump with compression
pg_dump -h timescaledb \
    -U modax_user \
    -d modax \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_DIR}/modax_full_${DATE}.dump" \
    --verbose

# Calculate checksum
sha256sum "${BACKUP_DIR}/modax_full_${DATE}.dump" > "${BACKUP_DIR}/modax_full_${DATE}.dump.sha256"

# Log backup completion
echo "$(date): Full backup completed - ${BACKUP_DIR}/modax_full_${DATE}.dump" >> /var/log/modax/backups.log

# Cleanup old backups
find ${BACKUP_DIR} -name "modax_full_*.dump" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "modax_full_*.sha256" -mtime +${RETENTION_DAYS} -delete

# Upload to remote storage (S3)
aws s3 cp "${BACKUP_DIR}/modax_full_${DATE}.dump" \
    s3://modax-backups/database/full/ \
    --storage-class STANDARD_IA

echo "Backup uploaded to S3"
```

### Incremental Backup with WAL Archiving
```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = '/usr/local/bin/archive_wal.sh %p %f'
archive_timeout = 300  # 5 minutes

# archive_wal.sh
#!/bin/bash
WAL_FILE=$1
WAL_NAME=$2
ARCHIVE_DIR="/var/backups/modax/wal"

# Copy to local archive
cp $WAL_FILE ${ARCHIVE_DIR}/${WAL_NAME}

# Upload to S3
aws s3 cp ${ARCHIVE_DIR}/${WAL_NAME} \
    s3://modax-backups/database/wal/ \
    --storage-class STANDARD_IA

# Verify upload
if [ $? -eq 0 ]; then
    exit 0
else
    echo "WAL archive upload failed: ${WAL_NAME}" >> /var/log/modax/wal_archive_errors.log
    exit 1
fi
```

### Automated Backup via Cron
```cron
# /etc/cron.d/modax-backups

# Daily full backup at 2 AM
0 2 * * * root /usr/local/bin/backup_database_full.sh

# Backup configuration files daily at 2:30 AM
30 2 * * * root /usr/local/bin/backup_configs.sh

# Weekly full system backup on Sunday at 3 AM
0 3 * * 0 root /usr/local/bin/backup_system_full.sh

# Monthly archive on 1st of month at 4 AM
0 4 1 * * root /usr/local/bin/backup_archive.sh

# Verify backups daily at 6 AM
0 6 * * * root /usr/local/bin/verify_backups.sh
```

## Configuration Backup

### Backup Script
```bash
#!/bin/bash
# backup_configs.sh

BACKUP_DIR="/var/backups/modax/configs"
DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_DIRS=(
    "/etc/modax"
    "/opt/modax/config"
    "/var/lib/mosquitto/config"
)

mkdir -p ${BACKUP_DIR}

# Create tar archive
tar -czf "${BACKUP_DIR}/configs_${DATE}.tar.gz" \
    ${CONFIG_DIRS[@]} \
    --exclude='*.log' \
    --exclude='*.pyc'

# Encrypt sensitive configs
gpg --encrypt \
    --recipient backups@modax.local \
    "${BACKUP_DIR}/configs_${DATE}.tar.gz"

# Remove unencrypted archive
rm "${BACKUP_DIR}/configs_${DATE}.tar.gz"

# Upload to S3
aws s3 cp "${BACKUP_DIR}/configs_${DATE}.tar.gz.gpg" \
    s3://modax-backups/configs/

# Cleanup old backups (keep 90 days)
find ${BACKUP_DIR} -name "configs_*.tar.gz.gpg" -mtime +90 -delete

echo "$(date): Configuration backup completed" >> /var/log/modax/backups.log
```

## Application State Backup

### AI Models Backup
```bash
#!/bin/bash
# backup_ai_models.sh

BACKUP_DIR="/var/backups/modax/ai-models"
DATE=$(date +%Y%m%d_%H%M%S)
AI_MODELS_DIR="/opt/modax/ai-layer/models"

mkdir -p ${BACKUP_DIR}

# Backup AI models
tar -czf "${BACKUP_DIR}/ai_models_${DATE}.tar.gz" \
    -C ${AI_MODELS_DIR} .

# Upload to S3
aws s3 cp "${BACKUP_DIR}/ai_models_${DATE}.tar.gz" \
    s3://modax-backups/ai-models/

echo "AI models backed up: ${DATE}"
```

### Docker Images Backup
```bash
#!/bin/bash
# backup_docker_images.sh

BACKUP_DIR="/var/backups/modax/docker-images"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Save production images
docker save modax/control-layer:latest | gzip > "${BACKUP_DIR}/control-layer_${DATE}.tar.gz"
docker save modax/ai-layer:latest | gzip > "${BACKUP_DIR}/ai-layer_${DATE}.tar.gz"

# Upload to S3
aws s3 cp ${BACKUP_DIR}/ \
    s3://modax-backups/docker-images/${DATE}/ \
    --recursive

# Keep only last 4 weeks of image backups
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +28 -delete
```

## Recovery Procedures

### Database Recovery

#### Full Recovery from Dump
```bash
#!/bin/bash
# restore_database_full.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: restore_database_full.sh <backup_file>"
    exit 1
fi

echo "Starting database restoration from ${BACKUP_FILE}"

# Verify backup file integrity
sha256sum -c "${BACKUP_FILE}.sha256" || exit 1

# Stop applications
docker-compose stop control-layer ai-layer

# Drop and recreate database
psql -h timescaledb -U postgres -c "DROP DATABASE IF EXISTS modax;"
psql -h timescaledb -U postgres -c "CREATE DATABASE modax OWNER modax_user;"

# Restore database
pg_restore -h timescaledb \
    -U modax_user \
    -d modax \
    --verbose \
    ${BACKUP_FILE}

# Restart applications
docker-compose start control-layer ai-layer

echo "Database restoration completed"
```

#### Point-in-Time Recovery (PITR)
```bash
#!/bin/bash
# restore_database_pitr.sh

TARGET_TIME=$1  # Format: 2024-12-06 14:30:00

if [ -z "$TARGET_TIME" ]; then
    echo "Usage: restore_database_pitr.sh 'YYYY-MM-DD HH:MM:SS'"
    exit 1
fi

echo "Starting point-in-time recovery to ${TARGET_TIME}"

# Stop PostgreSQL
docker-compose stop timescaledb

# Restore base backup
LATEST_BACKUP=$(ls -t /var/backups/modax/database/modax_full_*.dump | head -1)
pg_restore -h timescaledb -U modax_user -d modax --clean ${LATEST_BACKUP}

# Configure recovery
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /var/backups/modax/wal/%f %p'
recovery_target_time = '${TARGET_TIME}'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL (will replay WAL logs to target time)
docker-compose start timescaledb

echo "PITR recovery initiated. PostgreSQL will replay WAL logs."
echo "Check logs: docker-compose logs -f timescaledb"
```

### Configuration Recovery
```bash
#!/bin/bash
# restore_configs.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: restore_configs.sh <encrypted_backup_file>"
    exit 1
fi

# Decrypt backup
gpg --decrypt ${BACKUP_FILE} > /tmp/configs_restore.tar.gz

# Extract to temporary location
mkdir -p /tmp/modax_restore
tar -xzf /tmp/configs_restore.tar.gz -C /tmp/modax_restore

# Stop services
docker-compose stop

# Restore configuration files
cp -r /tmp/modax_restore/etc/modax/* /etc/modax/
cp -r /tmp/modax_restore/opt/modax/config/* /opt/modax/config/
cp -r /tmp/modax_restore/var/lib/mosquitto/config/* /var/lib/mosquitto/config/

# Restart services
docker-compose start

# Cleanup
rm -rf /tmp/modax_restore /tmp/configs_restore.tar.gz

echo "Configuration restored successfully"
```

### AI Models Recovery
```bash
#!/bin/bash
# restore_ai_models.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: restore_ai_models.sh <backup_file>"
    exit 1
fi

AI_MODELS_DIR="/opt/modax/ai-layer/models"

# Backup current models (just in case)
mv ${AI_MODELS_DIR} ${AI_MODELS_DIR}.backup_$(date +%Y%m%d_%H%M%S)

# Create models directory
mkdir -p ${AI_MODELS_DIR}

# Extract models
tar -xzf ${BACKUP_FILE} -C ${AI_MODELS_DIR}

# Restart AI layer
docker-compose restart ai-layer

echo "AI models restored successfully"
```

### Complete System Recovery
```bash
#!/bin/bash
# disaster_recovery.sh

echo "=== MODAX Disaster Recovery Procedure ==="
echo "This will restore the entire system from backups"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

# 1. Download latest backups from S3
echo "1. Downloading backups from S3..."
aws s3 sync s3://modax-backups/database/full/ /tmp/recovery/database/
aws s3 sync s3://modax-backups/configs/ /tmp/recovery/configs/
aws s3 sync s3://modax-backups/ai-models/ /tmp/recovery/ai-models/

# 2. Restore configurations
echo "2. Restoring configurations..."
LATEST_CONFIG=$(ls -t /tmp/recovery/configs/configs_*.tar.gz.gpg | head -1)
./restore_configs.sh ${LATEST_CONFIG}

# 3. Restore database
echo "3. Restoring database..."
LATEST_DB=$(ls -t /tmp/recovery/database/modax_full_*.dump | head -1)
./restore_database_full.sh ${LATEST_DB}

# 4. Restore AI models
echo "4. Restoring AI models..."
LATEST_MODELS=$(ls -t /tmp/recovery/ai-models/ai_models_*.tar.gz | head -1)
./restore_ai_models.sh ${LATEST_MODELS}

# 5. Verify services
echo "5. Verifying services..."
sleep 30
./verify_system.sh

echo "=== Disaster Recovery Complete ==="
```

## Backup Verification

### Automated Verification Script
```bash
#!/bin/bash
# verify_backups.sh

BACKUP_DIR="/var/backups/modax"
ERRORS=0

echo "=== Backup Verification Report - $(date) ===" > /var/log/modax/backup_verification.log

# 1. Verify database backup exists and is valid
LATEST_DB=$(ls -t ${BACKUP_DIR}/database/modax_full_*.dump 2>/dev/null | head -1)
if [ -n "$LATEST_DB" ]; then
    # Check age (should be less than 24 hours old)
    AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_DB")) / 3600 ))
    if [ $AGE -lt 24 ]; then
        echo "[OK] Database backup is recent (${AGE}h old)" >> /var/log/modax/backup_verification.log
        
        # Verify checksum
        sha256sum -c "${LATEST_DB}.sha256" >> /var/log/modax/backup_verification.log 2>&1
        if [ $? -eq 0 ]; then
            echo "[OK] Database backup checksum verified" >> /var/log/modax/backup_verification.log
        else
            echo "[ERROR] Database backup checksum mismatch" >> /var/log/modax/backup_verification.log
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "[ERROR] Database backup is too old (${AGE}h)" >> /var/log/modax/backup_verification.log
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "[ERROR] No database backup found" >> /var/log/modax/backup_verification.log
    ERRORS=$((ERRORS + 1))
fi

# 2. Verify configuration backup
LATEST_CONFIG=$(ls -t ${BACKUP_DIR}/configs/configs_*.tar.gz.gpg 2>/dev/null | head -1)
if [ -n "$LATEST_CONFIG" ]; then
    AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_CONFIG")) / 3600 ))
    if [ $AGE -lt 24 ]; then
        echo "[OK] Configuration backup is recent (${AGE}h old)" >> /var/log/modax/backup_verification.log
    else
        echo "[WARNING] Configuration backup is old (${AGE}h)" >> /var/log/modax/backup_verification.log
    fi
else
    echo "[ERROR] No configuration backup found" >> /var/log/modax/backup_verification.log
    ERRORS=$((ERRORS + 1))
fi

# 3. Verify S3 sync status
S3_DB_COUNT=$(aws s3 ls s3://modax-backups/database/full/ | wc -l)
if [ $S3_DB_COUNT -gt 0 ]; then
    echo "[OK] S3 database backups present (${S3_DB_COUNT} files)" >> /var/log/modax/backup_verification.log
else
    echo "[ERROR] No S3 database backups found" >> /var/log/modax/backup_verification.log
    ERRORS=$((ERRORS + 1))
fi

# 4. Test restore (monthly only, on a test instance)
if [ $(date +%d) -eq 1 ]; then
    echo "[INFO] Monthly restore test scheduled" >> /var/log/modax/backup_verification.log
    # Schedule test restore on test system
fi

# Summary
echo "=== Verification Complete ===" >> /var/log/modax/backup_verification.log
echo "Errors found: ${ERRORS}" >> /var/log/modax/backup_verification.log

# Send alert if errors found
if [ $ERRORS -gt 0 ]; then
    # Send email/Slack alert
    echo "ALERT: Backup verification failed with ${ERRORS} errors" | \
        mail -s "MODAX Backup Verification Failed" admin@modax.local
fi

exit $ERRORS
```

## Backup Monitoring

### Prometheus Metrics
```python
# backup_metrics.py
from prometheus_client import Gauge, Counter

backup_age_seconds = Gauge(
    'modax_backup_age_seconds',
    'Time since last successful backup',
    ['backup_type']
)

backup_size_bytes = Gauge(
    'modax_backup_size_bytes',
    'Size of last backup',
    ['backup_type']
)

backup_success_total = Counter(
    'modax_backup_success_total',
    'Total successful backups',
    ['backup_type']
)

backup_failure_total = Counter(
    'modax_backup_failure_total',
    'Total failed backups',
    ['backup_type']
)
```

### Grafana Dashboard Queries
```promql
# Backup age
time() - modax_backup_age_seconds{backup_type="database"}

# Backup failure rate
rate(modax_backup_failure_total[24h])

# Backup size trend
modax_backup_size_bytes{backup_type="database"}
```

## Retention Policies

### Data Retention Schedule
| Data Type | Local Retention | Remote Retention | Archive Retention |
|-----------|-----------------|------------------|-------------------|
| Database Full | 30 days | 90 days | 7 years |
| Database Incremental | 7 days | 30 days | - |
| Configuration | 90 days | 1 year | 7 years |
| Application Logs | 30 days | 90 days | 1 year |
| AI Models | 30 days | 90 days | 3 years |
| Audit Logs | 90 days | 1 year | 7 years |

### Compliance Requirements
- **Financial records:** 7 years
- **Audit logs:** 7 years
- **Safety records:** Permanently
- **Personal data:** As per GDPR (deletion on request)

## Disaster Recovery Plan

### Recovery Time Objective (RTO)
- **Critical Systems:** < 4 hours
- **Database:** < 1 hour
- **Applications:** < 30 minutes
- **Configuration:** < 15 minutes

### Recovery Point Objective (RPO)
- **Database:** < 5 minutes (WAL archiving)
- **Configuration:** < 24 hours
- **Application State:** < 24 hours

### DR Testing Schedule
- **Quarterly:** Partial restore test
- **Annually:** Full disaster recovery drill
- **Documentation:** Update procedures after each test

## Best Practices

### DO:
✅ Test backups regularly  
✅ Verify backup integrity  
✅ Keep multiple backup copies  
✅ Encrypt sensitive backups  
✅ Monitor backup success/failure  
✅ Document recovery procedures  
✅ Maintain off-site backups  

### DON'T:
❌ Rely on single backup location  
❌ Skip backup verification  
❌ Store backups on same storage as primary data  
❌ Neglect backup monitoring  
❌ Forget to test recovery procedures  
❌ Leave backups unencrypted  
❌ Keep unnecessary backup copies indefinitely  

## Troubleshooting

### Backup Failures
```bash
# Check backup logs
tail -f /var/log/modax/backups.log

# Check disk space
df -h /var/backups

# Verify S3 credentials
aws s3 ls s3://modax-backups/

# Test database connectivity
pg_isready -h timescaledb -U modax_user
```

### Recovery Failures
```bash
# Check recovery logs
tail -f /var/log/modax/recovery.log

# Verify backup file integrity
sha256sum -c backup_file.sha256

# Check database logs
docker-compose logs timescaledb

# Verify disk space for recovery
df -h /var/lib/postgresql
```

## References
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Disaster Recovery Best Practices](https://www.nist.gov/itl/smallbusinesscyber/guidance-topic/backup-recovery)

---
**Last Updated:** 2024-12-06  
**Maintained By:** MODAX Operations Team
