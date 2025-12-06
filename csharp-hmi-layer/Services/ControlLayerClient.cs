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
    /// </summary>
    public class ControlLayerClient
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;

        public ControlLayerClient(string baseUrl = "http://localhost:8000")
        {
            _baseUrl = baseUrl;
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(_baseUrl),
                Timeout = TimeSpan.FromSeconds(5)
            };
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
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting devices: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get latest sensor data for a device
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
                
                return data;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting device data: {ex.Message}");
                return null;
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
                
                return analysis;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting AI analysis: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Send a control command
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
                
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending control command: {ex.Message}");
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
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
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
