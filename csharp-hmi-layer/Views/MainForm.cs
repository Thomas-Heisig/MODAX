using System;
using System.Drawing;
using System.Net.Http;
using System.Windows.Forms;
using System.Threading.Tasks;
using MODAX.HMI.Services;
using MODAX.HMI.Models;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Main HMI Form for MODAX Industrial Control System
    /// </summary>
    public partial class MainForm : Form
    {
        private readonly ControlLayerClient _controlClient;
        private System.Windows.Forms.Timer? _updateTimer;
        private string? _selectedDeviceId;

        // UI Controls
        private ComboBox? _deviceComboBox;
        private TextBox? _deviceFilterTextBox;
        private System.Collections.Generic.List<string> _allDevices = new();
        private Label? _systemStatusLabel;
        private Label? _safetyStatusLabel;
        private Panel? _safetyPanel;
        
        // Sensor displays
        private Label? _currentLabel;
        private Label? _vibrationLabel;
        private Label? _temperatureLabel;
        
        // AI displays
        private Panel? _aiPanel;
        private Label? _anomalyLabel;
        private Label? _wearLevelLabel;
        private ProgressBar? _wearProgressBar;
        private TextBox? _recommendationsTextBox;
        
        // Control buttons
        private Button? _startButton;
        private Button? _stopButton;
        private Button? _refreshButton;
        
        // Loading indicator
        private Panel? _loadingPanel;
        private Label? _loadingLabel;
        private bool _isLoading = false;

        public MainForm()
        {
            _controlClient = new ControlLayerClient();
            InitializeComponents();
            InitializeTimer();
            InitializeKeyboardShortcuts();
        }

        private void InitializeComponents()
        {
            // Form setup
            Text = "MODAX - Industrial Control HMI";
            Size = new Size(1200, 800);
            StartPosition = FormStartPosition.CenterScreen;
            KeyPreview = true; // Enable keyboard shortcuts

            // Main layout
            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 3,
                Padding = new Padding(10)
            };
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 60F));
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 80F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 60F));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 40F));

            // Header section
            var headerPanel = CreateHeaderPanel();
            mainPanel.Controls.Add(headerPanel, 0, 0);
            mainPanel.SetColumnSpan(headerPanel, 2);

            // Sensor data section
            var sensorPanel = CreateSensorPanel();
            mainPanel.Controls.Add(sensorPanel, 0, 1);

            // Safety section
            var safetySection = CreateSafetyPanel();
            mainPanel.Controls.Add(safetySection, 1, 1);

            // AI analysis section
            var aiSection = CreateAIPanel();
            mainPanel.Controls.Add(aiSection, 0, 2);
            mainPanel.SetColumnSpan(aiSection, 2);

            Controls.Add(mainPanel);
        }

        private Panel CreateHeaderPanel()
        {
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.FromArgb(240, 240, 240)
            };

            var titleLabel = new Label
            {
                Text = "MODAX Industrial Control System",
                Font = new Font("Arial", 20, FontStyle.Bold),
                Location = new Point(10, 10),
                AutoSize = true
            };
            panel.Controls.Add(titleLabel);

            _systemStatusLabel = new Label
            {
                Text = "Status: Connecting...",
                Font = new Font("Arial", 12),
                Location = new Point(10, 45),
                AutoSize = true
            };
            panel.Controls.Add(_systemStatusLabel);

            // Device filter
            var filterLabel = new Label
            {
                Text = "Filter:",
                Location = new Point(400, 20),
                AutoSize = true
            };
            panel.Controls.Add(filterLabel);

            _deviceFilterTextBox = new TextBox
            {
                Location = new Point(450, 18),
                Width = 150,
                PlaceholderText = "Type to filter..."
            };
            _deviceFilterTextBox.TextChanged += OnDeviceFilterChanged;
            panel.Controls.Add(_deviceFilterTextBox);

            // Device selector
            var deviceLabel = new Label
            {
                Text = "Device:",
                Location = new Point(610, 20),
                AutoSize = true
            };
            panel.Controls.Add(deviceLabel);

            _deviceComboBox = new ComboBox
            {
                Location = new Point(670, 18),
                Width = 200,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _deviceComboBox.SelectedIndexChanged += OnDeviceSelected;
            panel.Controls.Add(_deviceComboBox);

            // Refresh button
            _refreshButton = new Button
            {
                Text = "Refresh",
                Location = new Point(880, 17),
                Width = 80
            };
            _refreshButton.Click += async (s, e) => await RefreshDevicesAsync();
            panel.Controls.Add(_refreshButton);

            return panel;
        }

        private GroupBox CreateSensorPanel()
        {
            var groupBox = new GroupBox
            {
                Text = "Sensor Data",
                Dock = DockStyle.Fill,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };

            _currentLabel = new Label
            {
                Text = "Motor Currents: --",
                Location = new Point(15, 30),
                AutoSize = true,
                Font = new Font("Arial", 11)
            };
            groupBox.Controls.Add(_currentLabel);

            _vibrationLabel = new Label
            {
                Text = "Vibration: --",
                Location = new Point(15, 70),
                AutoSize = true,
                Font = new Font("Arial", 11)
            };
            groupBox.Controls.Add(_vibrationLabel);

            _temperatureLabel = new Label
            {
                Text = "Temperature: --",
                Location = new Point(15, 110),
                AutoSize = true,
                Font = new Font("Arial", 11)
            };
            groupBox.Controls.Add(_temperatureLabel);

            return groupBox;
        }

        private GroupBox CreateSafetyPanel()
        {
            var groupBox = new GroupBox
            {
                Text = "Safety Status (AI-Free)",
                Dock = DockStyle.Fill,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };

            _safetyPanel = new Panel
            {
                Location = new Point(15, 30),
                Size = new Size(350, 120),
                BorderStyle = BorderStyle.FixedSingle
            };

            _safetyStatusLabel = new Label
            {
                Text = "Safety Status: Unknown",
                Location = new Point(10, 10),
                Size = new Size(330, 100),
                Font = new Font("Arial", 12, FontStyle.Bold)
            };
            _safetyPanel.Controls.Add(_safetyStatusLabel);

            groupBox.Controls.Add(_safetyPanel);

            // Control buttons
            _startButton = new Button
            {
                Text = "START",
                Location = new Point(15, 160),
                Size = new Size(100, 40),
                Enabled = false
            };
            _startButton.Click += async (s, e) => await SendCommandAsync("start");
            groupBox.Controls.Add(_startButton);

            _stopButton = new Button
            {
                Text = "STOP",
                Location = new Point(125, 160),
                Size = new Size(100, 40),
                Enabled = false
            };
            _stopButton.Click += async (s, e) => await SendCommandAsync("stop");
            groupBox.Controls.Add(_stopButton);

            return groupBox;
        }

        private GroupBox CreateAIPanel()
        {
            var groupBox = new GroupBox
            {
                Text = "AI Analysis (Advisory Only)",
                Dock = DockStyle.Fill,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };

            _anomalyLabel = new Label
            {
                Text = "Anomaly Detection: --",
                Location = new Point(15, 30),
                AutoSize = true,
                Font = new Font("Arial", 10)
            };
            groupBox.Controls.Add(_anomalyLabel);

            _wearLevelLabel = new Label
            {
                Text = "Wear Level: --",
                Location = new Point(15, 60),
                AutoSize = true,
                Font = new Font("Arial", 10)
            };
            groupBox.Controls.Add(_wearLevelLabel);

            _wearProgressBar = new ProgressBar
            {
                Location = new Point(150, 62),
                Size = new Size(200, 20),
                Minimum = 0,
                Maximum = 100
            };
            groupBox.Controls.Add(_wearProgressBar);

            var recLabel = new Label
            {
                Text = "Recommendations:",
                Location = new Point(15, 95),
                AutoSize = true,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };
            groupBox.Controls.Add(recLabel);

            _recommendationsTextBox = new TextBox
            {
                Location = new Point(15, 120),
                Size = new Size(1100, 100),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true
            };
            groupBox.Controls.Add(_recommendationsTextBox);

            return groupBox;
        }

        private void InitializeTimer()
        {
            // Read update interval from environment variable or use default (2000ms = 2 seconds)
            int updateInterval = 2000;
            string? intervalEnv = Environment.GetEnvironmentVariable("HMI_UPDATE_INTERVAL_MS");
            if (!string.IsNullOrEmpty(intervalEnv) && int.TryParse(intervalEnv, out int parsedInterval))
            {
                // Validate interval: minimum 500ms, maximum 30000ms (30 seconds)
                if (parsedInterval >= 500 && parsedInterval <= 30000)
                {
                    updateInterval = parsedInterval;
                }
            }

            _updateTimer = new System.Windows.Forms.Timer
            {
                Interval = updateInterval
            };
            _updateTimer.Tick += async (s, e) => await UpdateDataAsync();
            _updateTimer.Start();
        }

        private async void OnDeviceSelected(object? sender, EventArgs e)
        {
            if (_deviceComboBox?.SelectedItem is string deviceId)
            {
                _selectedDeviceId = deviceId;
                await UpdateDataAsync();
            }
        }

        private void OnDeviceFilterChanged(object? sender, EventArgs e)
        {
            if (_deviceFilterTextBox == null || _deviceComboBox == null) return;

            string filter = _deviceFilterTextBox.Text.Trim().ToLower();
            string? currentSelection = _deviceComboBox.SelectedItem as string;

            _deviceComboBox.Items.Clear();

            if (string.IsNullOrEmpty(filter))
            {
                // Show all devices when filter is empty
                foreach (var device in _allDevices)
                {
                    _deviceComboBox.Items.Add(device);
                }
            }
            else
            {
                // Show only filtered devices
                foreach (var device in _allDevices)
                {
                    if (device.ToLower().Contains(filter))
                    {
                        _deviceComboBox.Items.Add(device);
                    }
                }
            }

            // Try to restore previous selection if it's still in the filtered list
            if (currentSelection != null && _deviceComboBox.Items.Contains(currentSelection))
            {
                _deviceComboBox.SelectedItem = currentSelection;
            }
            else if (_deviceComboBox.Items.Count > 0)
            {
                _deviceComboBox.SelectedIndex = 0;
            }
        }

        private async Task RefreshDevicesAsync()
        {
            if (_isLoading) return; // Prevent concurrent refresh operations
            
            ShowLoading("Refreshing devices...");
            try
            {
                var devices = await _controlClient.GetDevicesAsync();
                if (devices != null && _deviceComboBox != null)
                {
                    // Store all devices
                    _allDevices.Clear();
                    _allDevices.AddRange(devices);

                    // Apply current filter
                    _deviceComboBox.Items.Clear();
                    string filter = _deviceFilterTextBox?.Text.Trim().ToLower() ?? "";
                    
                    foreach (var device in _allDevices)
                    {
                        if (string.IsNullOrEmpty(filter) || device.ToLower().Contains(filter))
                        {
                            _deviceComboBox.Items.Add(device);
                        }
                    }

                    if (_deviceComboBox.Items.Count > 0)
                    {
                        _deviceComboBox.SelectedIndex = 0;
                    }
                    else if (_systemStatusLabel != null)
                    {
                        _systemStatusLabel.Text = "Status: Connected but no devices found";
                        _systemStatusLabel.ForeColor = Color.Orange;
                    }
                }
                else
                {
                    // Connection failed
                    if (_systemStatusLabel != null)
                    {
                        _systemStatusLabel.Text = "Status: ⚠️ Cannot retrieve device list";
                        _systemStatusLabel.ForeColor = Color.Red;
                    }
                    
                    // Show user-friendly error dialog with troubleshooting tips
                    ShowErrorDialog(
                        "Unable to Connect",
                        "Could not retrieve device list from Control Layer.",
                        new string[]
                        {
                            "Verify the Control Layer service is running",
                            "Check the API URL configuration",
                            "Ensure network connectivity is available",
                            "Check firewall settings"
                        }
                    );
                }
            }
            catch (HttpRequestException ex)
            {
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = "Status: ⚠️ Network Error";
                    _systemStatusLabel.ForeColor = Color.Red;
                }
                
                ShowErrorDialog(
                    "Connection Failed",
                    $"Network error connecting to Control Layer:\n{ex.Message}",
                    new string[]
                    {
                        "Check that the Control Layer is running on " + _controlClient.BaseUrl,
                        "Verify network connectivity",
                        "Check firewall settings allow connection",
                        "Ensure the API port is not blocked"
                    }
                );
            }
            catch (TaskCanceledException)
            {
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = "Status: ⚠️ Connection Timeout";
                    _systemStatusLabel.ForeColor = Color.OrangeRed;
                }
                
                ShowErrorDialog(
                    "Request Timeout",
                    "The Control Layer did not respond in time.",
                    new string[]
                    {
                        "The Control Layer may be overloaded",
                        "Network latency may be too high",
                        "Try again in a few moments"
                    }
                );
            }
            catch (Exception ex)
            {
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = $"Status: ⚠️ Error: {ex.Message}";
                    _systemStatusLabel.ForeColor = Color.Red;
                }
                
                ShowErrorDialog(
                    "Unexpected Error",
                    $"An unexpected error occurred:\n{ex.Message}",
                    new string[]
                    {
                        "Try refreshing the device list again (F5)",
                        "Restart the HMI application if the problem persists",
                        "Contact support if the error continues"
                    }
                );
            }
            finally
            {
                HideLoading();
            }
        }
        
        /// <summary>
        /// Show a user-friendly error dialog with troubleshooting steps
        /// </summary>
        private void ShowErrorDialog(string title, string message, string[] troubleshootingSteps)
        {
            var fullMessage = message + "\n\nTroubleshooting steps:\n";
            for (int i = 0; i < troubleshootingSteps.Length; i++)
            {
                fullMessage += $"{i + 1}. {troubleshootingSteps[i]}\n";
            }
            
            MessageBox.Show(
                fullMessage,
                title,
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            );
        }

        private async Task UpdateDataAsync()
        {
            try
            {
                // Check connection first
                var isConnected = await _controlClient.IsConnectedAsync();
                
                if (!isConnected)
                {
                    // Display connection error to user
                    if (_systemStatusLabel != null)
                    {
                        _systemStatusLabel.Text = "Status: ⚠️ Cannot connect to Control Layer";
                        _systemStatusLabel.ForeColor = Color.Red;
                    }
                    return;
                }
                
                // Update system status
                var systemStatus = await _controlClient.GetSystemStatusAsync();
                if (systemStatus != null && _systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = $"Status: ✓ Connected | " +
                                             $"Devices: {systemStatus.DevicesOnline.Count} | " +
                                             $"AI: {(systemStatus.AiEnabled ? "Enabled" : "Disabled")}";
                    _systemStatusLabel.ForeColor = Color.DarkGreen;
                }

                // Update device-specific data
                if (!string.IsNullOrEmpty(_selectedDeviceId))
                {
                    await UpdateSensorDataAsync(_selectedDeviceId);
                    await UpdateAIAnalysisAsync(_selectedDeviceId);
                }
            }
            catch (HttpRequestException ex)
            {
                // Network/connection errors - display to user
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = $"Status: ⚠️ Connection Error: {ex.Message}";
                    _systemStatusLabel.ForeColor = Color.Red;
                }
                Console.WriteLine($"Connection error: {ex.Message}");
            }
            catch (TaskCanceledException ex)
            {
                // Timeout errors - display to user
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = "Status: ⚠️ Request Timeout - Control Layer not responding";
                    _systemStatusLabel.ForeColor = Color.OrangeRed;
                }
                Console.WriteLine($"Timeout error: {ex.Message}");
            }
            catch (Exception ex)
            {
                // General errors - display to user
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = $"Status: ⚠️ Error: {ex.Message}";
                    _systemStatusLabel.ForeColor = Color.Red;
                }
                Console.WriteLine($"Update error: {ex.Message}");
            }
        }

        private async Task UpdateSensorDataAsync(string deviceId)
        {
            var data = await _controlClient.GetDeviceDataAsync(deviceId);
            if (data == null) 
            {
                // Clear displays when no data available
                if (_currentLabel != null) _currentLabel.Text = "Motor Currents: No data available";
                if (_vibrationLabel != null) _vibrationLabel.Text = "Vibration: No data available";
                if (_temperatureLabel != null) _temperatureLabel.Text = "Temperature: No data available";
                return;
            }

            // Update sensor displays
            if (_currentLabel != null)
            {
                var currents = string.Join(", ", data.MotorCurrents.ConvertAll(c => $"{c:F2}A"));
                _currentLabel.Text = $"Motor Currents: {currents}";
            }

            if (_vibrationLabel != null)
            {
                _vibrationLabel.Text = $"Vibration: X={data.Vibration.X:F2}, Y={data.Vibration.Y:F2}, " +
                                      $"Z={data.Vibration.Z:F2}, Mag={data.Vibration.Magnitude:F2} m/s²";
            }

            if (_temperatureLabel != null)
            {
                var temps = string.Join(", ", data.Temperatures.ConvertAll(t => $"{t:F1}°C"));
                _temperatureLabel.Text = $"Temperature: {temps}";
            }

            // Update safety status
            if (data.SafetyStatus != null && _safetyStatusLabel != null && _safetyPanel != null)
            {
                var isSafe = data.SafetyStatus.IsSafe();
                _safetyStatusLabel.Text = data.SafetyStatus.GetStatusDescription();
                _safetyPanel.BackColor = isSafe ? Color.LightGreen : Color.Red;
                _safetyStatusLabel.ForeColor = isSafe ? Color.DarkGreen : Color.White;

                // Enable/disable control buttons based on safety
                if (_startButton != null) _startButton.Enabled = isSafe;
                if (_stopButton != null) _stopButton.Enabled = true;
            }
        }

        private async Task UpdateAIAnalysisAsync(string deviceId)
        {
            var analysis = await _controlClient.GetAIAnalysisAsync(deviceId);
            if (analysis == null) 
            {
                // Clear AI displays when no data available
                if (_anomalyLabel != null) 
                {
                    _anomalyLabel.Text = "Anomaly Detection: Not available";
                    _anomalyLabel.ForeColor = Color.Gray;
                }
                if (_wearLevelLabel != null) _wearLevelLabel.Text = "Wear Level: Not available";
                if (_wearProgressBar != null) _wearProgressBar.Value = 0;
                if (_recommendationsTextBox != null) _recommendationsTextBox.Text = "AI recommendations not available";
                return;
            }

            if (_anomalyLabel != null)
            {
                _anomalyLabel.Text = analysis.AnomalyDetected
                    ? $"⚠ Anomaly Detected (Score: {analysis.AnomalyScore:P0}): {analysis.AnomalyDescription}"
                    : "✓ No Anomalies Detected";
                _anomalyLabel.ForeColor = analysis.AnomalyDetected ? Color.Red : Color.Green;
            }

            if (_wearLevelLabel != null)
            {
                _wearLevelLabel.Text = $"Wear Level: {analysis.GetWearLevelDescription()} " +
                                      $"({analysis.PredictedWearLevel:P0}) - " +
                                      $"Est. {analysis.EstimatedRemainingHours:N0} hours remaining";
            }

            if (_wearProgressBar != null)
            {
                _wearProgressBar.Value = (int)(analysis.PredictedWearLevel * 100);
            }

            if (_recommendationsTextBox != null)
            {
                _recommendationsTextBox.Text = string.Join(Environment.NewLine + Environment.NewLine, 
                                                          analysis.Recommendations);
            }
        }

        private async Task SendCommandAsync(string commandType)
        {
            var success = await _controlClient.SendControlCommandAsync(commandType);
            if (success)
            {
                MessageBox.Show($"Command '{commandType}' sent successfully", "Success", 
                              MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                MessageBox.Show($"Failed to send command '{commandType}'", "Error", 
                              MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            _updateTimer?.Stop();
            _updateTimer?.Dispose();
            base.OnFormClosing(e);
        }

        protected override async void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            // Create loading panel
            CreateLoadingPanel();
            await RefreshDevicesAsync();
        }

        /// <summary>
        /// Create a loading indicator panel for async operations
        /// </summary>
        private void CreateLoadingPanel()
        {
            _loadingPanel = new Panel
            {
                Size = new Size(200, 80),
                BackColor = Color.FromArgb(200, 50, 50, 50),
                BorderStyle = BorderStyle.FixedSingle,
                Visible = false
            };

            _loadingLabel = new Label
            {
                Text = "Loading...",
                Font = new Font("Arial", 12, FontStyle.Bold),
                ForeColor = Color.White,
                TextAlign = ContentAlignment.MiddleCenter,
                Dock = DockStyle.Fill
            };

            _loadingPanel.Controls.Add(_loadingLabel);
            Controls.Add(_loadingPanel);
            _loadingPanel.BringToFront();
            
            // Center the loading panel
            _loadingPanel.Location = new Point(
                (Width - _loadingPanel.Width) / 2,
                (Height - _loadingPanel.Height) / 2
            );
        }

        /// <summary>
        /// Show loading indicator with optional message
        /// </summary>
        private void ShowLoading(string message = "Loading...")
        {
            if (_loadingPanel != null && _loadingLabel != null)
            {
                _loadingLabel.Text = message;
                _loadingPanel.Visible = true;
                _loadingPanel.BringToFront();
                _isLoading = true;
                // Note: UI updates automatically when control properties change
                // Using async/await pattern in calling methods ensures proper UI threading
            }
        }

        /// <summary>
        /// Hide loading indicator
        /// </summary>
        private void HideLoading()
        {
            if (_loadingPanel != null)
            {
                _loadingPanel.Visible = false;
                _isLoading = false;
            }
        }

        /// <summary>
        /// Initialize keyboard shortcuts for common operations
        /// Shortcuts:
        /// - F5: Refresh device list
        /// - Ctrl+R: Refresh device list
        /// - Ctrl+S: Start motor (if device selected)
        /// - Ctrl+T: Stop motor (if device selected)
        /// - F1: Show help/shortcuts
        /// </summary>
        private void InitializeKeyboardShortcuts()
        {
            KeyDown += (sender, e) =>
            {
                // Refresh shortcuts
                if (e.KeyCode == Keys.F5 || (e.Control && e.KeyCode == Keys.R))
                {
                    e.Handled = true;
                    _ = RefreshDevicesAsync();
                }
                // Start motor shortcut
                else if (e.Control && e.KeyCode == Keys.S && !string.IsNullOrEmpty(_selectedDeviceId))
                {
                    e.Handled = true;
                    _ = SendCommandAsync("start_motor");
                }
                // Stop motor shortcut
                else if (e.Control && e.KeyCode == Keys.T && !string.IsNullOrEmpty(_selectedDeviceId))
                {
                    e.Handled = true;
                    _ = SendCommandAsync("stop_motor");
                }
                // Help shortcut
                else if (e.KeyCode == Keys.F1)
                {
                    e.Handled = true;
                    ShowKeyboardShortcutsHelp();
                }
            };
        }

        /// <summary>
        /// Display keyboard shortcuts help dialog
        /// </summary>
        private void ShowKeyboardShortcutsHelp()
        {
            var helpText = @"Keyboard Shortcuts:

F5 or Ctrl+R     - Refresh device list
Ctrl+S           - Start motor (requires device selection)
Ctrl+T           - Stop motor (requires device selection)
F1               - Show this help

Note: Control commands require a device to be selected first.";

            MessageBox.Show(
                helpText,
                "MODAX HMI - Keyboard Shortcuts",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            );
        }
    }
}
