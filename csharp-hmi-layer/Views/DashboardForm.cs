using System;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;
using MODAX.HMI.Services;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Dashboard form with multiple tabs for system overview
    /// </summary>
    public partial class DashboardForm : MdiChildForm
    {
        // Configuration constants
        private const int MAX_LOG_LINES = 1000;
        private const int LOG_TRIM_SIZE = 500;
        
        private readonly ControlLayerClient _controlClient;
        private TabControl? _tabControl;
        private System.Windows.Forms.Timer? _updateTimer;
        
        // Tab pages
        private TabPage? _overviewTab;
        private TabPage? _devicesTab;
        private TabPage? _analyticsTab;
        private TabPage? _logsTab;
        
        // Overview tab controls
        private Label? _systemStatusLabel;
        private Label? _devicesOnlineLabel;
        private Label? _aiStatusLabel;
        private Label? _uptimeLabel;
        
        // Devices tab controls
        private DataGridView? _devicesGrid;
        
        // Logs tab controls
        private TextBox? _logsTextBox;
        
        public DashboardForm()
        {
            _controlClient = new ControlLayerClient();
            Text = "Dashboard";
            Size = new Size(1000, 700);
            
            InitializeComponents();
            InitializeTimer();
        }
        
        private void InitializeComponents()
        {
            // Create tab control
            _tabControl = new TabControl
            {
                Dock = DockStyle.Fill
            };
            
            // Create tabs
            CreateOverviewTab();
            CreateDevicesTab();
            CreateAnalyticsTab();
            CreateLogsTab();
            
            Controls.Add(_tabControl);
        }
        
        private void CreateOverviewTab()
        {
            _overviewTab = new TabPage("Overview");
            
            var panel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 4,
                ColumnCount = 2,
                Padding = new Padding(20)
            };
            
            panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
            panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
            panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 50F));
            panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 30F));
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 70F));
            
            // System Status
            var statusLabelHeader = new Label
            {
                Text = "System Status:",
                Font = new Font("Arial", 12, FontStyle.Bold),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(statusLabelHeader, 0, 0);
            
            _systemStatusLabel = new Label
            {
                Text = "Connecting...",
                Font = new Font("Arial", 12),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                ForeColor = Color.Gray
            };
            panel.Controls.Add(_systemStatusLabel, 1, 0);
            
            // Devices Online
            var devicesLabelHeader = new Label
            {
                Text = "Devices Online:",
                Font = new Font("Arial", 12, FontStyle.Bold),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(devicesLabelHeader, 0, 1);
            
            _devicesOnlineLabel = new Label
            {
                Text = "0",
                Font = new Font("Arial", 12),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(_devicesOnlineLabel, 1, 1);
            
            // AI Status
            var aiLabelHeader = new Label
            {
                Text = "AI Status:",
                Font = new Font("Arial", 12, FontStyle.Bold),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(aiLabelHeader, 0, 2);
            
            _aiStatusLabel = new Label
            {
                Text = "Unknown",
                Font = new Font("Arial", 12),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(_aiStatusLabel, 1, 2);
            
            // Uptime
            var uptimeLabelHeader = new Label
            {
                Text = "Uptime:",
                Font = new Font("Arial", 12, FontStyle.Bold),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft
            };
            panel.Controls.Add(uptimeLabelHeader, 0, 3);
            
            _uptimeLabel = new Label
            {
                Text = "N/A",
                Font = new Font("Arial", 12),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.TopLeft
            };
            panel.Controls.Add(_uptimeLabel, 1, 3);
            
            _overviewTab.Controls.Add(panel);
            _tabControl?.TabPages.Add(_overviewTab);
        }
        
        private void CreateDevicesTab()
        {
            _devicesTab = new TabPage("Devices");
            
            var panel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(10) };
            
            // Refresh button
            var refreshButton = new Button
            {
                Text = "Refresh Devices",
                Location = new Point(10, 10),
                Size = new Size(120, 30)
            };
            refreshButton.Click += async (s, e) => await RefreshDevicesAsync();
            panel.Controls.Add(refreshButton);
            
            // Data grid
            _devicesGrid = new DataGridView
            {
                Location = new Point(10, 50),
                Size = new Size(panel.Width - 20, panel.Height - 60),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                ReadOnly = true,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect
            };
            
            // Add columns
            _devicesGrid.Columns.Add("DeviceId", "Device ID");
            _devicesGrid.Columns.Add("Type", "Type");
            _devicesGrid.Columns.Add("Status", "Status");
            _devicesGrid.Columns.Add("LastSeen", "Last Seen");
            
            panel.Controls.Add(_devicesGrid);
            
            _devicesTab.Controls.Add(panel);
            _tabControl?.TabPages.Add(_devicesTab);
        }
        
        private void CreateAnalyticsTab()
        {
            _analyticsTab = new TabPage("Analytics");
            
            var label = new Label
            {
                Text = "Analytics charts and statistics will be displayed here.",
                Font = new Font("Arial", 12),
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter,
                ForeColor = Color.Gray
            };
            
            _analyticsTab.Controls.Add(label);
            _tabControl?.TabPages.Add(_analyticsTab);
        }
        
        private void CreateLogsTab()
        {
            _logsTab = new TabPage("Logs");
            
            var panel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(10) };
            
            // Clear button
            var clearButton = new Button
            {
                Text = "Clear Logs",
                Location = new Point(10, 10),
                Size = new Size(100, 30)
            };
            clearButton.Click += (s, e) => _logsTextBox?.Clear();
            panel.Controls.Add(clearButton);
            
            // Logs text box
            _logsTextBox = new TextBox
            {
                Location = new Point(10, 50),
                Size = new Size(panel.Width - 20, panel.Height - 60),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
                Multiline = true,
                ScrollBars = ScrollBars.Both,
                ReadOnly = true,
                Font = new Font("Consolas", 9)
            };
            
            panel.Controls.Add(_logsTextBox);
            
            _logsTab.Controls.Add(panel);
            _tabControl?.TabPages.Add(_logsTab);
        }
        
        private void InitializeTimer()
        {
            _updateTimer = new System.Windows.Forms.Timer
            {
                Interval = 2000 // Update every 2 seconds
            };
            _updateTimer.Tick += async (s, e) => await UpdateDataAsync();
            _updateTimer.Start();
        }
        
        private async Task UpdateDataAsync()
        {
            try
            {
                var systemStatus = await _controlClient.GetSystemStatusAsync();
                if (systemStatus != null)
                {
                    // Update overview tab
                    if (_systemStatusLabel != null)
                    {
                        _systemStatusLabel.Text = "✓ Connected";
                        _systemStatusLabel.ForeColor = Color.DarkGreen;
                    }
                    
                    if (_devicesOnlineLabel != null)
                    {
                        _devicesOnlineLabel.Text = systemStatus.DevicesOnline.Count.ToString();
                    }
                    
                    if (_aiStatusLabel != null)
                    {
                        _aiStatusLabel.Text = systemStatus.AiEnabled ? "Enabled" : "Disabled";
                        _aiStatusLabel.ForeColor = systemStatus.AiEnabled ? Color.DarkGreen : Color.Gray;
                    }
                    
                    if (_uptimeLabel != null && systemStatus.Uptime.HasValue)
                    {
                        var uptime = TimeSpan.FromSeconds(systemStatus.Uptime.Value);
                        _uptimeLabel.Text = $"{uptime.Days}d {uptime.Hours}h {uptime.Minutes}m";
                    }
                    
                    // Log activity
                    LogActivity($"[{DateTime.Now:HH:mm:ss}] System status updated - Devices: {systemStatus.DevicesOnline.Count}");
                }
            }
            catch (Exception ex)
            {
                if (_systemStatusLabel != null)
                {
                    _systemStatusLabel.Text = "⚠ Connection Error";
                    _systemStatusLabel.ForeColor = Color.Red;
                }
                
                LogActivity($"[{DateTime.Now:HH:mm:ss}] ERROR: {ex.Message}");
            }
        }
        
        private async Task RefreshDevicesAsync()
        {
            try
            {
                var devices = await _controlClient.GetDevicesAsync();
                if (devices != null && _devicesGrid != null)
                {
                    _devicesGrid.Rows.Clear();
                    
                    foreach (var deviceId in devices)
                    {
                        _devicesGrid.Rows.Add(
                            deviceId,
                            "MODAX Device",
                            "Online",
                            DateTime.Now.ToString("HH:mm:ss")
                        );
                    }
                    
                    LogActivity($"[{DateTime.Now:HH:mm:ss}] Devices refreshed - Found {devices.Count} devices");
                }
            }
            catch (Exception ex)
            {
                LogActivity($"[{DateTime.Now:HH:mm:ss}] ERROR refreshing devices: {ex.Message}");
                MessageBox.Show($"Error refreshing devices: {ex.Message}", "Error",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        
        private void LogActivity(string message)
        {
            if (_logsTextBox != null)
            {
                if (_logsTextBox.InvokeRequired)
                {
                    _logsTextBox.Invoke(new Action(() => LogActivity(message)));
                    return;
                }
                
                _logsTextBox.AppendText(message + Environment.NewLine);
                
                // Auto-scroll to bottom
                _logsTextBox.SelectionStart = _logsTextBox.Text.Length;
                _logsTextBox.ScrollToCaret();
                
                // Limit log size to prevent memory issues
                if (_logsTextBox.Lines.Length > MAX_LOG_LINES)
                {
                    var lines = _logsTextBox.Lines;
                    var newLines = new string[LOG_TRIM_SIZE];
                    Array.Copy(lines, lines.Length - LOG_TRIM_SIZE, newLines, 0, LOG_TRIM_SIZE);
                    _logsTextBox.Lines = newLines;
                }
            }
        }
        
        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            _updateTimer?.Stop();
            _updateTimer?.Dispose();
            base.OnFormClosing(e);
        }
    }
}
