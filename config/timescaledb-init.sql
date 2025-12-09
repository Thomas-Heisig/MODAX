-- MODAX TimescaleDB Initialization Script
-- This script sets up the database schema for historical sensor data storage

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- SENSOR DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    
    -- Sensor readings
    temperature REAL,
    vibration_x REAL,
    vibration_y REAL,
    vibration_z REAL,
    current REAL,
    spindle_speed REAL,
    feed_rate REAL,
    
    -- Metadata
    is_safe BOOLEAN DEFAULT true,
    quality_score REAL,
    
    PRIMARY KEY (time, device_id)
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('sensor_data', 'time', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sensor_device_time 
    ON sensor_data (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_safe 
    ON sensor_data (is_safe, time DESC) WHERE is_safe = false;

-- ============================================================================
-- AI ANALYSIS RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_analysis (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    
    -- Anomaly detection
    has_anomaly BOOLEAN DEFAULT false,
    anomaly_type TEXT,
    anomaly_score REAL,
    anomaly_details JSONB,
    
    -- Wear prediction
    wear_level REAL,
    estimated_cycles_remaining INTEGER,
    maintenance_recommended BOOLEAN,
    
    -- Optimization
    optimization_suggestions JSONB,
    confidence REAL,
    
    PRIMARY KEY (time, device_id)
);

-- Convert to hypertable
SELECT create_hypertable('ai_analysis', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ai_device_time 
    ON ai_analysis (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ai_anomaly 
    ON ai_analysis (has_anomaly, time DESC) WHERE has_anomaly = true;
CREATE INDEX IF NOT EXISTS idx_ai_maintenance 
    ON ai_analysis (maintenance_recommended, time DESC) WHERE maintenance_recommended = true;

-- ============================================================================
-- CONTROL COMMANDS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS control_commands (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    command_type TEXT NOT NULL,
    command_data JSONB,
    source TEXT,
    executed BOOLEAN DEFAULT false,
    result TEXT,
    
    PRIMARY KEY (time, command_type)
);

-- Convert to hypertable
SELECT create_hypertable('control_commands', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_commands_device_time 
    ON control_commands (device_id, time DESC);

-- ============================================================================
-- SYSTEM EVENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_events (
    time TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    component TEXT,
    message TEXT,
    details JSONB,
    
    PRIMARY KEY (time, event_type, component)
);

-- Convert to hypertable
SELECT create_hypertable('system_events', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_events_severity 
    ON system_events (severity, time DESC);
CREATE INDEX IF NOT EXISTS idx_events_component 
    ON system_events (component, time DESC);

-- ============================================================================
-- CONTINUOUS AGGREGATES (Pre-computed aggregations for performance)
-- ============================================================================

-- Hourly sensor data aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    device_id,
    AVG(temperature) AS avg_temperature,
    MAX(temperature) AS max_temperature,
    MIN(temperature) AS min_temperature,
    AVG(vibration_x) AS avg_vibration_x,
    AVG(vibration_y) AS avg_vibration_y,
    AVG(vibration_z) AS avg_vibration_z,
    AVG(current) AS avg_current,
    MAX(current) AS max_current,
    COUNT(*) AS sample_count,
    COUNT(*) FILTER (WHERE is_safe = false) AS unsafe_count
FROM sensor_data
GROUP BY bucket, device_id;

-- Daily sensor data aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS bucket,
    device_id,
    AVG(temperature) AS avg_temperature,
    MAX(temperature) AS max_temperature,
    MIN(temperature) AS min_temperature,
    AVG(current) AS avg_current,
    MAX(current) AS max_current,
    COUNT(*) AS sample_count,
    COUNT(*) FILTER (WHERE is_safe = false) AS unsafe_count
FROM sensor_data
GROUP BY bucket, device_id;

-- Hourly anomaly statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS anomaly_stats_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    device_id,
    COUNT(*) FILTER (WHERE has_anomaly = true) AS anomaly_count,
    AVG(anomaly_score) FILTER (WHERE has_anomaly = true) AS avg_anomaly_score,
    AVG(wear_level) AS avg_wear_level,
    COUNT(*) FILTER (WHERE maintenance_recommended = true) AS maintenance_alerts
FROM ai_analysis
GROUP BY bucket, device_id;

-- ============================================================================
-- RETENTION POLICIES
-- ============================================================================

-- Keep raw sensor data for 30 days
SELECT add_retention_policy('sensor_data', INTERVAL '30 days', if_not_exists => TRUE);

-- Keep raw AI analysis for 90 days
SELECT add_retention_policy('ai_analysis', INTERVAL '90 days', if_not_exists => TRUE);

-- Keep control commands for 180 days
SELECT add_retention_policy('control_commands', INTERVAL '180 days', if_not_exists => TRUE);

-- Keep system events for 365 days
SELECT add_retention_policy('system_events', INTERVAL '365 days', if_not_exists => TRUE);

-- Keep hourly aggregates for 1 year
SELECT add_retention_policy('sensor_data_hourly', INTERVAL '1 year', if_not_exists => TRUE);

-- Keep daily aggregates for 5 years
SELECT add_retention_policy('sensor_data_daily', INTERVAL '5 years', if_not_exists => TRUE);

-- ============================================================================
-- COMPRESSION POLICIES (Save disk space)
-- ============================================================================

-- Compress sensor data older than 7 days
SELECT add_compression_policy('sensor_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Compress AI analysis older than 14 days
SELECT add_compression_policy('ai_analysis', INTERVAL '14 days', if_not_exists => TRUE);

-- Compress system events older than 30 days
SELECT add_compression_policy('system_events', INTERVAL '30 days', if_not_exists => TRUE);

-- ============================================================================
-- REFRESH POLICIES FOR CONTINUOUS AGGREGATES
-- ============================================================================

-- Refresh hourly aggregates every 30 minutes
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Refresh daily aggregates every 12 hours
SELECT add_continuous_aggregate_policy('sensor_data_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '12 hours',
    if_not_exists => TRUE
);

-- Refresh anomaly statistics every hour
SELECT add_continuous_aggregate_policy('anomaly_stats_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- GRAFANA DATABASE (for Grafana configuration persistence)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS grafana;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE modax TO modax;
GRANT ALL PRIVILEGES ON DATABASE grafana TO modax;

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- Latest sensor readings per device
CREATE OR REPLACE VIEW latest_sensor_data AS
SELECT DISTINCT ON (device_id)
    device_id,
    time,
    temperature,
    vibration_x,
    vibration_y,
    vibration_z,
    current,
    spindle_speed,
    feed_rate,
    is_safe,
    quality_score
FROM sensor_data
ORDER BY device_id, time DESC;

-- Latest AI analysis per device
CREATE OR REPLACE VIEW latest_ai_analysis AS
SELECT DISTINCT ON (device_id)
    device_id,
    time,
    has_anomaly,
    anomaly_type,
    anomaly_score,
    wear_level,
    estimated_cycles_remaining,
    maintenance_recommended,
    confidence
FROM ai_analysis
ORDER BY device_id, time DESC;

-- Active devices (devices with data in last 5 minutes)
CREATE OR REPLACE VIEW active_devices AS
SELECT DISTINCT device_id
FROM sensor_data
WHERE time > NOW() - INTERVAL '5 minutes';

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This script is idempotent and can be run multiple times safely
-- 2. Hypertables automatically partition data by time for better performance
-- 3. Continuous aggregates pre-compute common queries for fast dashboards
-- 4. Retention policies automatically delete old data
-- 5. Compression policies save disk space for old data
-- 6. Adjust retention and compression intervals based on your requirements
