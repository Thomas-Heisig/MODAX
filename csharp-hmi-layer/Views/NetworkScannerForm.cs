using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using MODAX.HMI.Services;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Network Scanner form for device discovery
    /// </summary>
    public partial class NetworkScannerForm : MdiChildForm
    {
        private readonly ControlLayerClient _controlClient;
        
        // Controls
        private TabControl? _tabControl;
        private TextBox? _networkTextBox;
        private Button? _scanButton;
        private DataGridView? _resultsGrid;
        private ProgressBar? _progressBar;
        private Label? _statusLabel;
        
        // Port scanner tab
        private TextBox? _hostTextBox;
        private CheckBox? _commonPortsCheckBox;
        private TextBox? _customPortsTextBox;
        private Button? _scanPortsButton;
        private DataGridView? _portResultsGrid;
        private ProgressBar? _portProgressBar;
        private Label? _portStatusLabel;
        
        public NetworkScannerForm()
        {
            _controlClient = new ControlLayerClient();
            Text = "Network Scanner";
            Size = new Size(900, 600);
            
            InitializeComponents();
        }
        
        private void InitializeComponents()
        {
            _tabControl = new TabControl
            {
                Dock = DockStyle.Fill
            };
            
            CreateNetworkScannerTab();
            CreatePortScannerTab();
            
            Controls.Add(_tabControl);
        }
        
        private void CreateNetworkScannerTab()
        {
            var tab = new TabPage("Network Scanner");
            
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                Padding = new Padding(10)
            };
            
            // Network input
            var networkLabel = new Label
            {
                Text = "Network (CIDR):",
                Location = new Point(10, 15),
                AutoSize = true
            };
            panel.Controls.Add(networkLabel);
            
            _networkTextBox = new TextBox
            {
                Location = new Point(120, 12),
                Width = 200,
                PlaceholderText = "e.g., 192.168.1.0/24"
            };
            panel.Controls.Add(_networkTextBox);
            
            // Scan button
            _scanButton = new Button
            {
                Text = "Start Scan",
                Location = new Point(330, 10),
                Width = 100
            };
            _scanButton.Click += async (s, e) => await StartNetworkScanAsync();
            panel.Controls.Add(_scanButton);
            
            // Scan local subnet button
            var scanLocalButton = new Button
            {
                Text = "Scan Local Subnet",
                Location = new Point(440, 10),
                Width = 130
            };
            scanLocalButton.Click += async (s, e) => await StartNetworkScanAsync(true);
            panel.Controls.Add(scanLocalButton);
            
            // Status label
            _statusLabel = new Label
            {
                Text = "Ready to scan",
                Location = new Point(10, 45),
                Width = 400,
                ForeColor = Color.Gray
            };
            panel.Controls.Add(_statusLabel);
            
            // Progress bar
            _progressBar = new ProgressBar
            {
                Location = new Point(10, 70),
                Width = 860,
                Style = ProgressBarStyle.Marquee,
                Visible = false
            };
            panel.Controls.Add(_progressBar);
            
            // Results grid
            _resultsGrid = new DataGridView
            {
                Location = new Point(10, 100),
                Size = new Size(860, 430),
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                ReadOnly = true,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect
            };
            
            // Add columns
            _resultsGrid.Columns.Add("IP", "IP Address");
            _resultsGrid.Columns.Add("Hostname", "Hostname");
            _resultsGrid.Columns.Add("Type", "Device Type");
            _resultsGrid.Columns.Add("OpenPorts", "Open Ports");
            _resultsGrid.Columns.Add("DiscoveredAt", "Discovered At");
            
            panel.Controls.Add(_resultsGrid);
            
            tab.Controls.Add(panel);
            _tabControl?.TabPages.Add(tab);
        }
        
        private void CreatePortScannerTab()
        {
            var tab = new TabPage("Port Scanner");
            
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                Padding = new Padding(10)
            };
            
            // Host input
            var hostLabel = new Label
            {
                Text = "Host:",
                Location = new Point(10, 15),
                AutoSize = true
            };
            panel.Controls.Add(hostLabel);
            
            _hostTextBox = new TextBox
            {
                Location = new Point(60, 12),
                Width = 200,
                PlaceholderText = "IP address or hostname"
            };
            panel.Controls.Add(_hostTextBox);
            
            // Common ports checkbox
            _commonPortsCheckBox = new CheckBox
            {
                Text = "Scan common ports",
                Location = new Point(270, 14),
                Width = 150,
                Checked = true
            };
            _commonPortsCheckBox.CheckedChanged += (s, e) =>
            {
                if (_customPortsTextBox != null)
                {
                    _customPortsTextBox.Enabled = !_commonPortsCheckBox.Checked;
                }
            };
            panel.Controls.Add(_commonPortsCheckBox);
            
            // Custom ports input
            var customPortsLabel = new Label
            {
                Text = "Custom Ports:",
                Location = new Point(10, 45),
                AutoSize = true
            };
            panel.Controls.Add(customPortsLabel);
            
            _customPortsTextBox = new TextBox
            {
                Location = new Point(100, 42),
                Width = 300,
                PlaceholderText = "e.g., 80,443,8000-8010",
                Enabled = false
            };
            panel.Controls.Add(_customPortsTextBox);
            
            // Scan button
            _scanPortsButton = new Button
            {
                Text = "Scan Ports",
                Location = new Point(410, 40),
                Width = 100
            };
            _scanPortsButton.Click += async (s, e) => await StartPortScanAsync();
            panel.Controls.Add(_scanPortsButton);
            
            // Port status label
            _portStatusLabel = new Label
            {
                Text = "Ready to scan",
                Location = new Point(10, 75),
                Width = 400,
                ForeColor = Color.Gray
            };
            panel.Controls.Add(_portStatusLabel);
            
            // Port progress bar
            _portProgressBar = new ProgressBar
            {
                Location = new Point(10, 100),
                Width = 860,
                Style = ProgressBarStyle.Marquee,
                Visible = false
            };
            panel.Controls.Add(_portProgressBar);
            
            // Port results grid
            _portResultsGrid = new DataGridView
            {
                Location = new Point(10, 130),
                Size = new Size(860, 400),
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                ReadOnly = true,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect
            };
            
            // Add columns
            _portResultsGrid.Columns.Add("Port", "Port");
            _portResultsGrid.Columns.Add("Status", "Status");
            _portResultsGrid.Columns.Add("Service", "Service");
            
            // Color code the status column
            _portResultsGrid.CellFormatting += (s, e) =>
            {
                if (e.ColumnIndex == 1 && e.Value != null)
                {
                    var status = e.Value.ToString();
                    if (status == "Open")
                    {
                        e.CellStyle.ForeColor = Color.DarkGreen;
                        e.CellStyle.Font = new Font(e.CellStyle.Font, FontStyle.Bold);
                    }
                    else if (status == "Closed")
                    {
                        e.CellStyle.ForeColor = Color.Gray;
                    }
                }
            };
            
            panel.Controls.Add(_portResultsGrid);
            
            tab.Controls.Add(panel);
            _tabControl?.TabPages.Add(tab);
        }
        
        private async Task StartNetworkScanAsync(bool localSubnet = false)
        {
            try
            {
                if (_scanButton != null) _scanButton.Enabled = false;
                if (_progressBar != null) _progressBar.Visible = true;
                if (_statusLabel != null)
                {
                    _statusLabel.Text = localSubnet ? "Scanning local subnet..." : "Scanning network...";
                    _statusLabel.ForeColor = Color.Blue;
                }
                
                if (_resultsGrid != null)
                {
                    _resultsGrid.Rows.Clear();
                }
                
                // Call the API
                string? network = localSubnet ? null : _networkTextBox?.Text;
                var response = await ScanNetworkAsync(network);
                
                if (response != null && response.ContainsKey("devices"))
                {
                    var devices = response["devices"] as List<Dictionary<string, object>>;
                    if (devices != null && _resultsGrid != null)
                    {
                        foreach (var device in devices)
                        {
                            var ip = device.GetValueOrDefault("ip", "Unknown").ToString();
                            var hostname = device.GetValueOrDefault("hostname", "Unknown").ToString();
                            var deviceType = device.GetValueOrDefault("device_type", "Unknown").ToString();
                            var openPorts = device.GetValueOrDefault("open_ports", new List<int>());
                            var discoveredAt = device.GetValueOrDefault("discovered_at", DateTime.Now.ToString()).ToString();
                            
                            string portsString = "";
                            if (openPorts is System.Text.Json.JsonElement jsonElement && jsonElement.ValueKind == System.Text.Json.JsonValueKind.Array)
                            {
                                var portsList = new List<int>();
                                foreach (var port in jsonElement.EnumerateArray())
                                {
                                    portsList.Add(port.GetInt32());
                                }
                                portsString = string.Join(", ", portsList);
                            }
                            
                            _resultsGrid.Rows.Add(ip, hostname, deviceType, portsString, discoveredAt);
                        }
                        
                        if (_statusLabel != null)
                        {
                            _statusLabel.Text = $"Scan complete - Found {devices.Count} devices";
                            _statusLabel.ForeColor = Color.DarkGreen;
                        }
                    }
                }
                else
                {
                    if (_statusLabel != null)
                    {
                        _statusLabel.Text = "Scan complete - No devices found";
                        _statusLabel.ForeColor = Color.Orange;
                    }
                }
            }
            catch (Exception ex)
            {
                if (_statusLabel != null)
                {
                    _statusLabel.Text = $"Error: {ex.Message}";
                    _statusLabel.ForeColor = Color.Red;
                }
                
                MessageBox.Show($"Error scanning network: {ex.Message}", "Error",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                if (_scanButton != null) _scanButton.Enabled = true;
                if (_progressBar != null) _progressBar.Visible = false;
            }
        }
        
        private async Task StartPortScanAsync()
        {
            try
            {
                if (string.IsNullOrWhiteSpace(_hostTextBox?.Text))
                {
                    MessageBox.Show("Please enter a host to scan", "Error",
                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                
                if (_scanPortsButton != null) _scanPortsButton.Enabled = false;
                if (_portProgressBar != null) _portProgressBar.Visible = true;
                if (_portStatusLabel != null)
                {
                    _portStatusLabel.Text = "Scanning ports...";
                    _portStatusLabel.ForeColor = Color.Blue;
                }
                
                if (_portResultsGrid != null)
                {
                    _portResultsGrid.Rows.Clear();
                }
                
                // Call the API
                var host = _hostTextBox?.Text;
                var commonPorts = _commonPortsCheckBox?.Checked ?? true;
                var response = await ScanPortsAsync(host!, commonPorts);
                
                if (response != null && response.ContainsKey("results"))
                {
                    var results = response["results"] as List<Dictionary<string, object>>;
                    if (results != null && _portResultsGrid != null)
                    {
                        foreach (var result in results)
                        {
                            var port = result.GetValueOrDefault("port", 0).ToString();
                            var isOpen = Convert.ToBoolean(result.GetValueOrDefault("open", false));
                            var service = result.GetValueOrDefault("service", "Unknown").ToString();
                            
                            _portResultsGrid.Rows.Add(
                                port,
                                isOpen ? "Open" : "Closed",
                                service
                            );
                        }
                        
                        var openCount = results.Count(r => Convert.ToBoolean(r.GetValueOrDefault("open", false)));
                        
                        if (_portStatusLabel != null)
                        {
                            _portStatusLabel.Text = $"Scan complete - {openCount} open ports found";
                            _portStatusLabel.ForeColor = Color.DarkGreen;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                if (_portStatusLabel != null)
                {
                    _portStatusLabel.Text = $"Error: {ex.Message}";
                    _portStatusLabel.ForeColor = Color.Red;
                }
                
                MessageBox.Show($"Error scanning ports: {ex.Message}", "Error",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                if (_scanPortsButton != null) _scanPortsButton.Enabled = true;
                if (_portProgressBar != null) _portProgressBar.Visible = false;
            }
        }
        
        private async Task<Dictionary<string, object>?> ScanNetworkAsync(string? network)
        {
            try
            {
                var url = $"{_controlClient.BaseUrl}/api/v1/network/scan";
                if (!string.IsNullOrEmpty(network))
                {
                    url += $"?network={Uri.EscapeDataString(network)}";
                }
                
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromMinutes(5); // Network scans can take time
                
                var response = await client.PostAsync(url, null);
                response.EnsureSuccessStatusCode();
                
                return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Network scan error: {ex.Message}");
                throw;
            }
        }
        
        private async Task<Dictionary<string, object>?> ScanPortsAsync(string host, bool commonPorts)
        {
            try
            {
                var url = $"{_controlClient.BaseUrl}/api/v1/port/scan?host={Uri.EscapeDataString(host)}&common_ports={commonPorts}";
                
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromMinutes(2);
                
                var response = await client.PostAsync(url, null);
                response.EnsureSuccessStatusCode();
                
                return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Port scan error: {ex.Message}");
                throw;
            }
        }
    }
}
