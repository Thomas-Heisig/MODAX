-- MODAX TimescaleDB Schema
-- This schema defines the database structure for storing sensor data, safety events,
-- AI analysis results, and control commands.

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Device Registry (Relational Table)
CREATE TABLE IF NOT EXISTS devices (
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

CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);

-- Sensor Data (Time-Series Hypertable)
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    current_a DOUBLE PRECISION,
    current_b DOUBLE PRECISION,
    current_c DOUBLE PRECISION,
    vibration DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    rpm INTEGER,
    power_kw DOUBLE PRECISION,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- Convert to hypertable (only if not already a hypertable)
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

-- Add compression policy (compress data older than 7 days)
ALTER TABLE sensor_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id'
);

-- Add compression policy
SELECT add_compression_policy('sensor_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sensor_device_time ON sensor_data (device_id, time DESC);

-- Safety Events (Time-Series Hypertable)
CREATE TABLE IF NOT EXISTS safety_events (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50),
    is_safe BOOLEAN,
    emergency_stop BOOLEAN,
    door_open BOOLEAN,
    overload_detected BOOLEAN,
    temperature_alarm BOOLEAN,
    description TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

SELECT create_hypertable('safety_events', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_safety_device_time ON safety_events (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_safety_type ON safety_events (event_type, time DESC);

-- AI Analysis Results (Time-Series Hypertable)
CREATE TABLE IF NOT EXISTS ai_analysis (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(50), -- 'anomaly', 'wear', 'optimization', 'combined'
    confidence DOUBLE PRECISION,
    is_anomaly BOOLEAN,
    anomaly_score DOUBLE PRECISION,
    wear_percentage DOUBLE PRECISION,
    remaining_hours INTEGER,
    recommendations JSONB,
    model_version VARCHAR(20),
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

SELECT create_hypertable('ai_analysis', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_ai_device_time ON ai_analysis (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ai_type ON ai_analysis (analysis_type, time DESC);

-- Control Commands (Audit Trail)
CREATE TABLE IF NOT EXISTS control_commands (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    command VARCHAR(100),
    parameters JSONB,
    user_id VARCHAR(50),
    source VARCHAR(50), -- 'hmi', 'api', 'automation'
    status VARCHAR(20), -- 'executed', 'blocked', 'failed'
    reason TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

SELECT create_hypertable('control_commands', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_commands_device_time ON control_commands (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_commands_user ON control_commands (user_id, time DESC);

-- Continuous Aggregates (Pre-computed Statistics)

-- Hourly Aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_hourly
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

-- Refresh policy for hourly aggregates
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Daily Aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_daily
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

-- Refresh policy for daily aggregates
SELECT add_continuous_aggregate_policy('sensor_data_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Retention Policies

-- Raw sensor data: 7 days
SELECT add_retention_policy('sensor_data', INTERVAL '7 days', if_not_exists => TRUE);

-- AI analysis: 30 days
SELECT add_retention_policy('ai_analysis', INTERVAL '30 days', if_not_exists => TRUE);

-- Safety events: 1 year (compliance)
SELECT add_retention_policy('safety_events', INTERVAL '1 year', if_not_exists => TRUE);

-- Control commands: 1 year (audit)
SELECT add_retention_policy('control_commands', INTERVAL '1 year', if_not_exists => TRUE);

-- Monthly Statistics (Manual Table)
CREATE TABLE IF NOT EXISTS sensor_data_monthly (
    month DATE PRIMARY KEY,
    device_id VARCHAR(50),
    avg_current_a DOUBLE PRECISION,
    avg_vibration DOUBLE PRECISION,
    avg_temperature DOUBLE PRECISION,
    max_current_a DOUBLE PRECISION,
    max_vibration DOUBLE PRECISION,
    max_temperature DOUBLE PRECISION,
    operating_hours INTEGER,
    sample_count BIGINT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- Helper function to populate monthly statistics (run via cron job)
CREATE OR REPLACE FUNCTION populate_monthly_statistics()
RETURNS void AS $$
BEGIN
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
        (SUM(sample_count) / 36000)::INTEGER AS operating_hours, -- 10Hz = 36000 samples/hour
        SUM(sample_count)
    FROM sensor_data_daily
    WHERE day >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
      AND day < DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY month, device_id
    ON CONFLICT (month) DO UPDATE SET
        avg_current_a = EXCLUDED.avg_current_a,
        avg_vibration = EXCLUDED.avg_vibration,
        avg_temperature = EXCLUDED.avg_temperature,
        max_current_a = EXCLUDED.max_current_a,
        max_vibration = EXCLUDED.max_vibration,
        max_temperature = EXCLUDED.max_temperature,
        operating_hours = EXCLUDED.operating_hours,
        sample_count = EXCLUDED.sample_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE devices IS 'Device registry with metadata';
COMMENT ON TABLE sensor_data IS 'Time-series sensor data from field devices';
COMMENT ON TABLE safety_events IS 'Safety status events and alarms';
COMMENT ON TABLE ai_analysis IS 'AI analysis results and predictions';
COMMENT ON TABLE control_commands IS 'Control command audit trail';
COMMENT ON MATERIALIZED VIEW sensor_data_hourly IS 'Hourly aggregated sensor statistics';
COMMENT ON MATERIALIZED VIEW sensor_data_daily IS 'Daily aggregated sensor statistics';
COMMENT ON TABLE sensor_data_monthly IS 'Monthly aggregated sensor statistics';
