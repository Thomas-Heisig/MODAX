# Database Schema Migration Guide

This document describes the strategy and implementation for database schema migrations in the MODAX system using Alembic.

**Last Updated:** 2025-12-09  
**Version:** 0.3.0  
**Issue:** #029  
**Status:** Implementation Guide

## Problem Statement

Currently, database schema changes must be performed manually:
- No version control for database schema
- Difficult to track changes across deployments
- Risk of inconsistencies between environments
- No rollback capability for schema changes
- Manual SQL scripts prone to errors

## Solution: Alembic Migration Framework

Alembic is a lightweight database migration tool for use with SQLAlchemy. It provides:
- Version control for database schemas
- Automatic migration script generation
- Support for upgrade and downgrade operations
- Branch and merge support for parallel development
- Integration with SQLAlchemy ORM

## Architecture

```
MODAX/
├── python-control-layer/
│   ├── alembic/
│   │   ├── versions/        # Migration scripts
│   │   ├── env.py          # Alembic environment
│   │   └── script.py.mako  # Template for new migrations
│   ├── alembic.ini         # Alembic configuration
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── sensor_data.py
│   │   └── device.py
│   └── db_connection.py    # Database connection
```

## Installation and Setup

### Step 1: Install Alembic

Add to `requirements.txt`:
```
alembic>=1.13.0
sqlalchemy>=2.0.0
```

Install dependencies:
```bash
cd python-control-layer
pip install -r requirements.txt
```

### Step 2: Initialize Alembic

```bash
cd python-control-layer
alembic init alembic
```

This creates:
- `alembic/` directory with migration infrastructure
- `alembic.ini` configuration file

### Step 3: Configure Database Connection

Edit `alembic.ini`:
```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://modax:password@localhost:5432/modax

# Or use environment variable
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

For environment-based configuration, edit `alembic/env.py`:
```python
from config import config as app_config
from db_connection import get_database_url

# Set the database URL from application config
config.set_main_option('sqlalchemy.url', get_database_url())
```

### Step 4: Define SQLAlchemy Models

Create `models/__init__.py`:
```python
"""SQLAlchemy models for MODAX database"""
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Use consistent naming convention
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

Base = declarative_base(metadata=metadata)

# Import all models
from .sensor_data import SensorData, SafetyStatus
from .device import Device
from .ai_analysis import AIAnalysis

__all__ = ['Base', 'SensorData', 'SafetyStatus', 'Device', 'AIAnalysis']
```

Create `models/sensor_data.py`:
```python
"""Sensor data models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ARRAY, Index
from sqlalchemy.sql import func
from . import Base

class SensorData(Base):
    """Sensor readings from field devices"""
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Sensor readings
    motor_currents = Column(ARRAY(Float), nullable=False)
    vibration = Column(ARRAY(Float), nullable=False)
    temperatures = Column(ARRAY(Float), nullable=False)
    
    # Aggregated data
    current_mean = Column(Float)
    current_std = Column(Float)
    current_max = Column(Float)
    vibration_mean = Column(Float)
    vibration_std = Column(Float)
    vibration_max = Column(Float)
    temperature_mean = Column(Float)
    temperature_max = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for time-series queries
    __table_args__ = (
        Index('ix_sensor_data_device_time', 'device_id', 'timestamp'),
    )

class SafetyStatus(Base):
    """Safety status readings"""
    __tablename__ = 'safety_status'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    emergency_stop = Column(Boolean, nullable=False)
    door_closed = Column(Boolean, nullable=False)
    overload_detected = Column(Boolean, nullable=False)
    temperature_ok = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_safety_status_device_time', 'device_id', 'timestamp'),
    )
```

Create `models/device.py`:
```python
"""Device models"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from . import Base

class Device(Base):
    """Registered devices"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    device_type = Column(String(50), nullable=False)
    location = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    
    # Configuration
    config = Column(JSON)  # Device-specific configuration
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

Create `models/ai_analysis.py`:
```python
"""AI analysis results models"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from . import Base

class AIAnalysis(Base):
    """AI analysis results"""
    __tablename__ = 'ai_analysis'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Analysis results
    anomalies_detected = Column(Boolean, nullable=False)
    anomaly_confidence = Column(Float)
    anomaly_types = Column(JSON)  # List of detected anomaly types
    
    wear_estimate = Column(Float)
    wear_confidence = Column(Float)
    estimated_cycles_remaining = Column(Integer)
    
    recommendations = Column(JSON)  # List of optimization recommendations
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Step 5: Configure Alembic Environment

Edit `alembic/env.py`:
```python
"""Alembic environment configuration"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models and config
from models import Base
from config import config as app_config

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Get database URL from application config
def get_url():
    """Get database URL from application configuration"""
    return app_config.control.database_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Creating Migrations

### Automatic Migration Generation

Alembic can auto-generate migrations by comparing models to database:

```bash
# Generate migration based on model changes
alembic revision --autogenerate -m "Add sensor_data table"
```

This creates a new migration file in `alembic/versions/` like:
`20251209_1234_add_sensor_data_table.py`

### Manual Migration Creation

For complex changes, create manually:

```bash
alembic revision -m "Add index for time series queries"
```

Edit the generated file:
```python
"""Add index for time series queries

Revision ID: abc123
Revises: xyz789
Create Date: 2025-12-09 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema"""
    op.create_index(
        'ix_sensor_data_device_time',
        'sensor_data',
        ['device_id', 'timestamp'],
        unique=False
    )

def downgrade() -> None:
    """Downgrade schema"""
    op.drop_index('ix_sensor_data_device_time', table_name='sensor_data')
```

## Running Migrations

### Upgrade to Latest

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Upgrade one version
alembic upgrade +1
```

### Downgrade

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade xyz789

# Downgrade all
alembic downgrade base
```

### Check Current Version

```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Migration Patterns

### Adding a Column

```python
def upgrade():
    op.add_column('sensor_data', 
        sa.Column('quality_score', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('sensor_data', 'quality_score')
```

### Modifying a Column

```python
def upgrade():
    # Make column nullable
    op.alter_column('sensor_data', 'temperature_mean',
        existing_type=sa.Float(),
        nullable=True)

def downgrade():
    op.alter_column('sensor_data', 'temperature_mean',
        existing_type=sa.Float(),
        nullable=False)
```

### Adding an Index

```python
def upgrade():
    op.create_index('ix_device_last_seen', 'devices', ['last_seen'])

def downgrade():
    op.drop_index('ix_device_last_seen', table_name='devices')
```

### Data Migration

```python
from sqlalchemy import orm
from models import Device

def upgrade():
    # Get database connection
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    
    # Update existing data
    session.execute(
        "UPDATE devices SET device_type = 'ESP32' WHERE device_type IS NULL"
    )
    
    session.commit()

def downgrade():
    pass  # Cannot reverse data changes
```

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/database-migration.yml`:
```yaml
name: Database Migrations

on:
  pull_request:
    paths:
      - 'python-control-layer/models/**'
      - 'python-control-layer/alembic/**'

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: timescale/timescaledb:latest-pg14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: modax_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd python-control-layer
          pip install -r requirements.txt
      
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/modax_test
        run: |
          cd python-control-layer
          alembic upgrade head
      
      - name: Verify schema
        run: |
          cd python-control-layer
          python -c "from models import Base; from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); Base.metadata.create_all(engine)"
      
      - name: Test downgrade
        run: |
          cd python-control-layer
          alembic downgrade -1
          alembic upgrade head
```

### Docker Deployment

Update `docker-compose.yml`:
```yaml
services:
  control-layer:
    build: ./python-control-layer
    depends_on:
      db-migration:
        condition: service_completed_successfully
  
  db-migration:
    build:
      context: ./python-control-layer
      dockerfile: Dockerfile.migration
    command: alembic upgrade head
    environment:
      DATABASE_URL: postgresql://modax:${DB_PASSWORD}@timescaledb:5432/modax
    depends_on:
      timescaledb:
        condition: service_healthy
```

Create `Dockerfile.migration`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic/ ./alembic/
COPY alembic.ini .
COPY models/ ./models/
COPY config.py .
COPY db_connection.py .

CMD ["alembic", "upgrade", "head"]
```

## Best Practices

### 1. Always Review Auto-Generated Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Review the generated file before applying
cat alembic/versions/latest_file.py

# Test locally first
alembic upgrade head
```

### 2. Write Reversible Migrations
```python
# Good - reversible
def upgrade():
    op.add_column('table', sa.Column('new_col', sa.String()))

def downgrade():
    op.drop_column('table', 'new_col')

# Bad - not reversible
def upgrade():
    op.execute("DELETE FROM table WHERE condition")

def downgrade():
    pass  # Cannot restore deleted data!
```

### 3. Use Transactions
```python
def upgrade():
    with op.batch_alter_table('sensor_data') as batch_op:
        batch_op.add_column(sa.Column('quality', sa.Float()))
        batch_op.create_index('ix_quality', ['quality'])
```

### 4. Test Migrations in Staging First
```bash
# Production workflow
1. Test migration locally
2. Deploy to staging
3. Verify staging
4. Backup production database
5. Deploy to production
6. Verify production
```

### 5. Keep Migrations Small
```bash
# Good - one logical change per migration
alembic revision -m "Add quality_score column"
alembic revision -m "Add index on timestamp"

# Bad - too many changes
alembic revision -m "Add 5 tables, modify 3 columns, add 10 indexes"
```

## Rollback Strategy

### Database Backup Before Migration
```bash
# Backup database
pg_dump modax > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

# Run migration
alembic upgrade head

# If issues, restore from backup
psql modax < backup_before_migration_20251209_140000.sql
```

### Git Tag After Successful Migration
```bash
# Tag the working state
git tag -a db_migration_v1.2.3 -m "Database schema version 1.2.3"
git push origin db_migration_v1.2.3
```

## Troubleshooting

### Migration Failed Mid-Way
```bash
# Check current version
alembic current

# Check migration history
alembic history

# Try to continue from where it failed
alembic upgrade head

# If stuck, manually fix and stamp version
alembic stamp head
```

### Conflicting Migrations
```bash
# If two developers created migrations in parallel
alembic history

# Merge migrations
alembic merge -m "Merge parallel migrations" abc123 xyz789
```

### Reset Migration State
```bash
# WARNING: This drops all tables!
alembic downgrade base
alembic upgrade head
```

## Related Documentation

- [Data Persistence](DATA_PERSISTENCE.md) - Database strategy
- [Backup & Recovery](BACKUP_RECOVERY.md) - Backup procedures
- [Configuration](CONFIGURATION.md) - Database configuration
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## Migration Checklist

- [ ] SQLAlchemy models defined
- [ ] Alembic initialized
- [ ] Database URL configured
- [ ] Initial migration created
- [ ] Migration tested locally
- [ ] Migration tested in staging
- [ ] Production database backed up
- [ ] Migration applied to production
- [ ] Verification tests passed
- [ ] Git tag created
- [ ] Documentation updated
