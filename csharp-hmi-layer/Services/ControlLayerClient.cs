using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using MODAX.HMI.Models;
using Newtonsoft.Json;

namespace MODAX.HMI.Services
{
    /// <summary>
    /// Client for communicating with the Control Layer REST API
    /// Includes offline mode with local caching
    /// </summary>
    public class ControlLayerClient
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        private readonly OfflineCache _offlineCache;
        private bool _isOnline = true;

        /// <summary>
        /// Gets the base URL of the Control Layer API
        /// </summary>
        public string BaseUrl => _baseUrl;

        /// <summary>
        /// Gets whether the client is currently online
        /// </summary>
        public bool IsOnline => _isOnline;

        /// <summary>
        /// Event raised when online/offline status changes
        /// </summary>
        public event EventHandler<bool>? OnlineStatusChanged;

        public ControlLayerClient(string baseUrl = "http://localhost:8000")
        {
            _baseUrl = baseUrl;
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(_baseUrl),
                Timeout = TimeSpan.FromSeconds(5)
            };
            _offlineCache = new OfflineCache();
        }

        /// <summary>
        /// Get overall system status
        /// </summary>
        public async Task<SystemStatus?> GetSystemStatusAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/status");
                response.EnsureSuccessStatusCode();
                return await response.Content.ReadFromJsonAsync<SystemStatus>();
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Connection error getting system status: {ex.Message}");
                throw; // Re-throw to allow UI to handle connection errors
            }
            catch (TaskCanceledException ex)
            {
                Console.WriteLine($"Timeout getting system status: {ex.Message}");
                throw; // Re-throw to allow UI to handle timeout errors
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting system status: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get list of connected devices
        /// </summary>
        public async Task<List<string>?> GetDevicesAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/devices");
                response.EnsureSuccessStatusCode();
                return await response.Content.ReadFromJsonAsync<List<string>>();
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Connection error getting devices: {ex.Message}");
                throw; // Re-throw to allow UI to handle connection errors
            }
            catch (TaskCanceledException ex)
            {
                Console.WriteLine($"Timeout getting devices: {ex.Message}");
                throw; // Re-throw to allow UI to handle timeout errors
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting devices: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get latest sensor data for a device
        /// Uses offline cache when connection is unavailable
        /// </summary>
        public async Task<SensorData?> GetDeviceDataAsync(string deviceId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"/devices/{deviceId}/data");
                response.EnsureSuccessStatusCode();
                
                var json = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<SensorData>(json, new JsonSerializerSettings
                {
                    PropertyNameCaseInsensitive = true
                });
                
                // Cache the data for offline use
                if (data != null)
                {
                    _offlineCache.CacheSensorData(deviceId, data);
                    UpdateOnlineStatus(true);
                }
                
                return data;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting device data: {ex.Message}");
                UpdateOnlineStatus(false);
                
                // Return cached data when offline
                return _offlineCache.GetLatestSensorData(deviceId);
            }
        }

        /// <summary>
        /// Get historical data for a device
        /// </summary>
        public async Task<List<SensorData>?> GetDeviceHistoryAsync(string deviceId, int count = 100)
        {
            try
            {
                var response = await _httpClient.GetAsync($"/devices/{deviceId}/history?count={count}");
                response.EnsureSuccessStatusCode();
                
                var json = await response.Content.ReadAsStringAsync();
                var result = JsonConvert.DeserializeObject<DeviceHistoryResponse>(json);
                
                return result?.Readings;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting device history: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get AI analysis for a device
        /// Uses offline cache when connection is unavailable
        /// </summary>
        public async Task<AIAnalysis?> GetAIAnalysisAsync(string deviceId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"/devices/{deviceId}/ai-analysis");
                response.EnsureSuccessStatusCode();
                
                var json = await response.Content.ReadAsStringAsync();
                var analysis = JsonConvert.DeserializeObject<AIAnalysis>(json, new JsonSerializerSettings
                {
                    PropertyNameCaseInsensitive = true
                });
                
                // Cache the analysis for offline use
                if (analysis != null)
                {
                    _offlineCache.CacheAIAnalysis(deviceId, analysis);
                    UpdateOnlineStatus(true);
                }
                
                return analysis;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting AI analysis: {ex.Message}");
                UpdateOnlineStatus(false);
                
                // Return cached analysis when offline
                return _offlineCache.GetLatestAIAnalysis(deviceId);
            }
        }

        /// <summary>
        /// Send a control command
        /// Queues command for later if offline
        /// </summary>
        public async Task<bool> SendControlCommandAsync(string commandType, Dictionary<string, string>? parameters = null)
        {
            try
            {
                var command = new
                {
                    command_type = commandType,
                    parameters = parameters ?? new Dictionary<string, string>()
                };

                var response = await _httpClient.PostAsJsonAsync("/control/command", command);
                response.EnsureSuccessStatusCode();
                
                UpdateOnlineStatus(true);
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending control command: {ex.Message}");
                UpdateOnlineStatus(false);
                
                // Queue command for later when offline
                _offlineCache.QueueCommand("system", commandType, parameters);
                return false;
            }
        }

        /// <summary>
        /// Check if control layer is reachable
        /// </summary>
        public async Task<bool> IsConnectedAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/health");
                var isConnected = response.IsSuccessStatusCode;
                UpdateOnlineStatus(isConnected);
                return isConnected;
            }
            catch
            {
                UpdateOnlineStatus(false);
                return false;
            }
        }

        /// <summary>
        /// Synchronize pending commands when connection is restored
        /// </summary>
        public async Task SynchronizePendingCommandsAsync()
        {
            if (!_isOnline) return;

            var pendingCommands = _offlineCache.GetPendingCommands();
            
            foreach (var (id, deviceId, commandType, commandJson) in pendingCommands)
            {
                try
                {
                    var parameters = JsonConvert.DeserializeObject<Dictionary<string, string>>(commandJson);
                    var success = await SendControlCommandAsync(commandType, parameters);
                    
                    if (success)
                    {
                        _offlineCache.MarkCommandSent(id);
                    }
                    else
                    {
                        _offlineCache.IncrementCommandRetry(id);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error synchronizing command {id}: {ex.Message}");
                    _offlineCache.IncrementCommandRetry(id);
                }
            }
        }

        /// <summary>
        /// Get historical data from offline cache
        /// </summary>
        public List<SensorData> GetCachedHistoricalData(string deviceId, int limit = 50)
        {
            return _offlineCache.GetHistoricalSensorData(deviceId, limit);
        }

        /// <summary>
        /// Get cache statistics
        /// </summary>
        public (int sensorCount, int aiCount, int pendingCommands) GetCacheStats()
        {
            return _offlineCache.GetCacheStats();
        }

        /// <summary>
        /// Clean up old cached data
        /// </summary>
        public void CleanupCache()
        {
            _offlineCache.CleanupOldData();
        }

        private void UpdateOnlineStatus(bool isOnline)
        {
            if (_isOnline != isOnline)
            {
                _isOnline = isOnline;
                OnlineStatusChanged?.Invoke(this, isOnline);
                
                // Try to synchronize pending commands when coming online
                if (isOnline)
                {
                    _ = Task.Run(async () => await SynchronizePendingCommandsAsync());
                }
            }
        }

        private class DeviceHistoryResponse
        {
            public string? DeviceId { get; set; }
            public int Count { get; set; }
            public List<SensorData>? Readings { get; set; }
        }
    }
}
