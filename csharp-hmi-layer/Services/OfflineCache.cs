using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Linq;
using System.Text.Json;
using MODAX.HMI.Models;

namespace MODAX.HMI.Services
{
    /// <summary>
    /// Local SQLite cache for offline data storage and synchronization
    /// </summary>
    public class OfflineCache : IDisposable
    {
        private readonly string _dbPath;
        private SQLiteConnection? _connection;
        private readonly object _lock = new object();

        public OfflineCache(string? dbPath = null)
        {
            // Use AppData folder for database
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var modaxDataPath = Path.Combine(appDataPath, "MODAX", "Data");
            Directory.CreateDirectory(modaxDataPath);

            _dbPath = dbPath ?? Path.Combine(modaxDataPath, "offline_cache.db");
            
            InitializeDatabase();
        }

        private void InitializeDatabase()
        {
            lock (_lock)
            {
                _connection = new SQLiteConnection($"Data Source={_dbPath};Version=3;");
                _connection.Open();

                // Create tables if they don't exist
                using var cmd = _connection.CreateCommand();
                
                // Sensor data table
                cmd.CommandText = @"
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        data_json TEXT NOT NULL,
                        synced INTEGER DEFAULT 0,
                        created_at INTEGER NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_sensor_device ON sensor_data(device_id);
                    CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_sensor_synced ON sensor_data(synced);
                ";
                cmd.ExecuteNonQuery();

                // AI analysis table
                cmd.CommandText = @"
                    CREATE TABLE IF NOT EXISTS ai_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        data_json TEXT NOT NULL,
                        synced INTEGER DEFAULT 0,
                        created_at INTEGER NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_ai_device ON ai_analysis(device_id);
                    CREATE INDEX IF NOT EXISTS idx_ai_timestamp ON ai_analysis(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_ai_synced ON ai_analysis(synced);
                ";
                cmd.ExecuteNonQuery();

                // Pending commands table (for commands sent while offline)
                cmd.CommandText = @"
                    CREATE TABLE IF NOT EXISTS pending_commands (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        command_type TEXT NOT NULL,
                        command_json TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        retry_count INTEGER DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_command_device ON pending_commands(device_id);
                ";
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Cache sensor data locally
        /// </summary>
        public void CacheSensorData(string deviceId, SensorData data)
        {
            lock (_lock)
            {
                if (_connection == null) return;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    INSERT INTO sensor_data (device_id, timestamp, data_json, created_at)
                    VALUES (@device_id, @timestamp, @data_json, @created_at)
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);
                cmd.Parameters.AddWithValue("@timestamp", data.Timestamp);
                cmd.Parameters.AddWithValue("@data_json", JsonSerializer.Serialize(data));
                cmd.Parameters.AddWithValue("@created_at", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Cache AI analysis data locally
        /// </summary>
        public void CacheAIAnalysis(string deviceId, AIAnalysis analysis)
        {
            lock (_lock)
            {
                if (_connection == null) return;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    INSERT INTO ai_analysis (device_id, timestamp, data_json, created_at)
                    VALUES (@device_id, @timestamp, @data_json, @created_at)
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);
                cmd.Parameters.AddWithValue("@timestamp", analysis.Timestamp);
                cmd.Parameters.AddWithValue("@data_json", JsonSerializer.Serialize(analysis));
                cmd.Parameters.AddWithValue("@created_at", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Get latest cached sensor data for a device
        /// </summary>
        public SensorData? GetLatestSensorData(string deviceId)
        {
            lock (_lock)
            {
                if (_connection == null) return null;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    SELECT data_json FROM sensor_data 
                    WHERE device_id = @device_id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);

                var result = cmd.ExecuteScalar();
                if (result == null) return null;

                return JsonSerializer.Deserialize<SensorData>(result.ToString()!);
            }
        }

        /// <summary>
        /// Get latest cached AI analysis for a device
        /// </summary>
        public AIAnalysis? GetLatestAIAnalysis(string deviceId)
        {
            lock (_lock)
            {
                if (_connection == null) return null;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    SELECT data_json FROM ai_analysis 
                    WHERE device_id = @device_id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);

                var result = cmd.ExecuteScalar();
                if (result == null) return null;

                return JsonSerializer.Deserialize<AIAnalysis>(result.ToString()!);
            }
        }

        /// <summary>
        /// Get historical sensor data for a device (for charts)
        /// </summary>
        public List<SensorData> GetHistoricalSensorData(string deviceId, int limit = 50)
        {
            lock (_lock)
            {
                if (_connection == null) return new List<SensorData>();

                var data = new List<SensorData>();
                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    SELECT data_json FROM sensor_data 
                    WHERE device_id = @device_id 
                    ORDER BY timestamp DESC 
                    LIMIT @limit
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);
                cmd.Parameters.AddWithValue("@limit", limit);

                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                {
                    var json = reader.GetString(0);
                    var sensorData = JsonSerializer.Deserialize<SensorData>(json);
                    if (sensorData != null)
                    {
                        data.Add(sensorData);
                    }
                }

                // Reverse to get chronological order
                data.Reverse();
                return data;
            }
        }

        /// <summary>
        /// Queue a command to be sent when online
        /// </summary>
        public void QueueCommand(string deviceId, string commandType, object? commandData = null)
        {
            lock (_lock)
            {
                if (_connection == null) return;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    INSERT INTO pending_commands (device_id, command_type, command_json, created_at)
                    VALUES (@device_id, @command_type, @command_json, @created_at)
                ";
                cmd.Parameters.AddWithValue("@device_id", deviceId);
                cmd.Parameters.AddWithValue("@command_type", commandType);
                cmd.Parameters.AddWithValue("@command_json", 
                    commandData != null ? JsonSerializer.Serialize(commandData) : "{}");
                cmd.Parameters.AddWithValue("@created_at", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Get all pending commands to be synchronized
        /// </summary>
        public List<(int id, string deviceId, string commandType, string commandJson)> GetPendingCommands()
        {
            lock (_lock)
            {
                if (_connection == null) return new List<(int, string, string, string)>();

                var commands = new List<(int, string, string, string)>();
                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    SELECT id, device_id, command_type, command_json 
                    FROM pending_commands 
                    WHERE retry_count < 3
                    ORDER BY created_at ASC
                ";

                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                {
                    commands.Add((
                        reader.GetInt32(0),
                        reader.GetString(1),
                        reader.GetString(2),
                        reader.GetString(3)
                    ));
                }

                return commands;
            }
        }

        /// <summary>
        /// Mark a command as successfully sent
        /// </summary>
        public void MarkCommandSent(int commandId)
        {
            lock (_lock)
            {
                if (_connection == null) return;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = "DELETE FROM pending_commands WHERE id = @id";
                cmd.Parameters.AddWithValue("@id", commandId);
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Increment retry count for a failed command
        /// </summary>
        public void IncrementCommandRetry(int commandId)
        {
            lock (_lock)
            {
                if (_connection == null) return;

                using var cmd = _connection.CreateCommand();
                cmd.CommandText = @"
                    UPDATE pending_commands 
                    SET retry_count = retry_count + 1 
                    WHERE id = @id
                ";
                cmd.Parameters.AddWithValue("@id", commandId);
                cmd.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Clean up old cached data (keep last 1000 entries per device)
        /// </summary>
        public void CleanupOldData()
        {
            lock (_lock)
            {
                if (_connection == null) return;

                // Clean sensor data
                using var cmd1 = _connection.CreateCommand();
                cmd1.CommandText = @"
                    DELETE FROM sensor_data 
                    WHERE id NOT IN (
                        SELECT id FROM sensor_data 
                        ORDER BY timestamp DESC 
                        LIMIT 1000
                    )
                ";
                cmd1.ExecuteNonQuery();

                // Clean AI analysis data
                using var cmd2 = _connection.CreateCommand();
                cmd2.CommandText = @"
                    DELETE FROM ai_analysis 
                    WHERE id NOT IN (
                        SELECT id FROM ai_analysis 
                        ORDER BY timestamp DESC 
                        LIMIT 1000
                    )
                ";
                cmd2.ExecuteNonQuery();
            }
        }

        /// <summary>
        /// Get cache statistics
        /// </summary>
        public (int sensorCount, int aiCount, int pendingCommands) GetCacheStats()
        {
            lock (_lock)
            {
                if (_connection == null) return (0, 0, 0);

                int sensorCount = 0, aiCount = 0, pendingCommands = 0;

                using (var cmd = _connection.CreateCommand())
                {
                    cmd.CommandText = "SELECT COUNT(*) FROM sensor_data";
                    sensorCount = Convert.ToInt32(cmd.ExecuteScalar());
                }

                using (var cmd = _connection.CreateCommand())
                {
                    cmd.CommandText = "SELECT COUNT(*) FROM ai_analysis";
                    aiCount = Convert.ToInt32(cmd.ExecuteScalar());
                }

                using (var cmd = _connection.CreateCommand())
                {
                    cmd.CommandText = "SELECT COUNT(*) FROM pending_commands";
                    pendingCommands = Convert.ToInt32(cmd.ExecuteScalar());
                }

                return (sensorCount, aiCount, pendingCommands);
            }
        }

        public void Dispose()
        {
            lock (_lock)
            {
                _connection?.Close();
                _connection?.Dispose();
                _connection = null;
            }
        }
    }
}
