using System;
using System.Drawing;
using System.Windows.Forms;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Main MDI Parent Form for MODAX Industrial Control System
    /// </summary>
    public partial class MainFormMdi : Form
    {
        // MDI child forms
        private DashboardForm? _dashboardForm;
        private NetworkScannerForm? _networkScannerForm;
        
        // Menu and toolbar
        private MenuStrip? _menuStrip;
        private ToolStrip? _toolStrip;
        private StatusStrip? _statusStrip;
        private ToolStripStatusLabel? _statusLabel;
        private ToolStripStatusLabel? _connectionLabel;
        
        public MainFormMdi()
        {
            InitializeComponents();
            InitializeMenus();
            InitializeToolbar();
            InitializeStatusBar();
            
            // Open dashboard by default
            OpenDashboard();
        }
        
        private void InitializeComponents()
        {
            // Form setup
            Text = "MODAX - Industrial Control System (MDI)";
            Size = new Size(1400, 900);
            StartPosition = FormStartPosition.CenterScreen;
            IsMdiContainer = true;
            KeyPreview = true;
            
            // Set MDI background
            if (MdiClient != null)
            {
                foreach (Control control in Controls)
                {
                    if (control is MdiClient mdiClient)
                    {
                        mdiClient.BackColor = Color.FromArgb(240, 240, 240);
                    }
                }
            }
            
            // Handle keyboard shortcuts
            KeyDown += MainFormMdi_KeyDown;
        }
        
        private void InitializeMenus()
        {
            _menuStrip = new MenuStrip();
            
            // File Menu
            var fileMenu = new ToolStripMenuItem("&File");
            fileMenu.DropDownItems.Add("&Exit", null, (s, e) => Application.Exit());
            _menuStrip.Items.Add(fileMenu);
            
            // View Menu
            var viewMenu = new ToolStripMenuItem("&View");
            viewMenu.DropDownItems.Add("&Dashboard", null, (s, e) => OpenDashboard());
            viewMenu.DropDownItems.Add("&Network Scanner", null, (s, e) => OpenNetworkScanner());
            viewMenu.DropDownItems.Add("&Classic View", null, (s, e) => OpenClassicView());
            viewMenu.DropDownItems.Add(new ToolStripSeparator());
            viewMenu.DropDownItems.Add("&Refresh All", null, (s, e) => RefreshAllWindows());
            _menuStrip.Items.Add(viewMenu);
            
            // Window Menu
            var windowMenu = new ToolStripMenuItem("&Window");
            windowMenu.DropDownItems.Add("&Cascade", null, (s, e) => LayoutMdi(MdiLayout.Cascade));
            windowMenu.DropDownItems.Add("Tile &Horizontal", null, (s, e) => LayoutMdi(MdiLayout.TileHorizontal));
            windowMenu.DropDownItems.Add("Tile &Vertical", null, (s, e) => LayoutMdi(MdiLayout.TileVertical));
            windowMenu.DropDownItems.Add("&Arrange Icons", null, (s, e) => LayoutMdi(MdiLayout.ArrangeIcons));
            windowMenu.DropDownItems.Add(new ToolStripSeparator());
            windowMenu.DropDownItems.Add("&Close All", null, (s, e) => CloseAllWindows());
            _menuStrip.Items.Add(windowMenu);
            
            // Help Menu
            var helpMenu = new ToolStripMenuItem("&Help");
            helpMenu.DropDownItems.Add("&Documentation (F1)", null, (s, e) => ShowHelp());
            helpMenu.DropDownItems.Add("&Keyboard Shortcuts", null, (s, e) => ShowKeyboardShortcuts());
            helpMenu.DropDownItems.Add(new ToolStripSeparator());
            helpMenu.DropDownItems.Add("&About", null, (s, e) => ShowAbout());
            _menuStrip.Items.Add(helpMenu);
            
            MainMenuStrip = _menuStrip;
            Controls.Add(_menuStrip);
        }
        
        private void InitializeToolbar()
        {
            _toolStrip = new ToolStrip
            {
                ImageScalingSize = new Size(24, 24)
            };
            
            // Dashboard button
            var dashboardButton = new ToolStripButton
            {
                Text = "Dashboard",
                DisplayStyle = ToolStripItemDisplayStyle.ImageAndText,
                Image = SystemIcons.Information.ToBitmap()
            };
            dashboardButton.Click += (s, e) => OpenDashboard();
            _toolStrip.Items.Add(dashboardButton);
            
            // Network Scanner button
            var scannerButton = new ToolStripButton
            {
                Text = "Network Scanner",
                DisplayStyle = ToolStripItemDisplayStyle.ImageAndText,
                Image = SystemIcons.Shield.ToBitmap()
            };
            scannerButton.Click += (s, e) => OpenNetworkScanner();
            _toolStrip.Items.Add(scannerButton);
            
            // Classic View button
            var classicButton = new ToolStripButton
            {
                Text = "Classic View",
                DisplayStyle = ToolStripItemDisplayStyle.ImageAndText,
                Image = SystemIcons.Application.ToBitmap()
            };
            classicButton.Click += (s, e) => OpenClassicView();
            _toolStrip.Items.Add(classicButton);
            
            _toolStrip.Items.Add(new ToolStripSeparator());
            
            // Cascade button
            var cascadeButton = new ToolStripButton
            {
                Text = "Cascade",
                DisplayStyle = ToolStripItemDisplayStyle.Text
            };
            cascadeButton.Click += (s, e) => LayoutMdi(MdiLayout.Cascade);
            _toolStrip.Items.Add(cascadeButton);
            
            // Tile Horizontal button
            var tileHButton = new ToolStripButton
            {
                Text = "Tile H",
                DisplayStyle = ToolStripItemDisplayStyle.Text
            };
            tileHButton.Click += (s, e) => LayoutMdi(MdiLayout.TileHorizontal);
            _toolStrip.Items.Add(tileHButton);
            
            // Tile Vertical button
            var tileVButton = new ToolStripButton
            {
                Text = "Tile V",
                DisplayStyle = ToolStripItemDisplayStyle.Text
            };
            tileVButton.Click += (s, e) => LayoutMdi(MdiLayout.TileVertical);
            _toolStrip.Items.Add(tileVButton);
            
            _toolStrip.Items.Add(new ToolStripSeparator());
            
            // Help button
            var helpButton = new ToolStripButton
            {
                Text = "Help (F1)",
                DisplayStyle = ToolStripItemDisplayStyle.Text
            };
            helpButton.Click += (s, e) => ShowHelp();
            _toolStrip.Items.Add(helpButton);
            
            Controls.Add(_toolStrip);
        }
        
        private void InitializeStatusBar()
        {
            _statusStrip = new StatusStrip();
            
            _statusLabel = new ToolStripStatusLabel
            {
                Text = "Ready",
                Spring = true,
                TextAlign = ContentAlignment.MiddleLeft
            };
            _statusStrip.Items.Add(_statusLabel);
            
            _connectionLabel = new ToolStripStatusLabel
            {
                Text = "Checking connection...",
                ForeColor = Color.Gray
            };
            _statusStrip.Items.Add(_connectionLabel);
            
            var timeLabel = new ToolStripStatusLabel
            {
                Text = DateTime.Now.ToString("HH:mm:ss")
            };
            _statusStrip.Items.Add(timeLabel);
            
            // Update time every second
            var timer = new System.Windows.Forms.Timer { Interval = 1000 };
            timer.Tick += (s, e) => timeLabel.Text = DateTime.Now.ToString("HH:mm:ss");
            timer.Start();
            
            Controls.Add(_statusStrip);
            
            // Start connection check
            CheckConnectionAsync();
        }
        
        private async void CheckConnectionAsync()
        {
            try
            {
                var client = new Services.ControlLayerClient();
                var isConnected = await client.IsConnectedAsync();
                
                if (_connectionLabel != null)
                {
                    if (isConnected)
                    {
                        _connectionLabel.Text = "✓ Connected to Control Layer";
                        _connectionLabel.ForeColor = Color.DarkGreen;
                    }
                    else
                    {
                        _connectionLabel.Text = "⚠ Disconnected";
                        _connectionLabel.ForeColor = Color.Red;
                    }
                }
            }
            catch
            {
                if (_connectionLabel != null)
                {
                    _connectionLabel.Text = "⚠ Connection Error";
                    _connectionLabel.ForeColor = Color.Red;
                }
            }
        }
        
        private void OpenDashboard()
        {
            // Check if already open
            if (_dashboardForm != null && !_dashboardForm.IsDisposed)
            {
                _dashboardForm.Activate();
                return;
            }
            
            _dashboardForm = new DashboardForm
            {
                MdiParent = this
            };
            _dashboardForm.Show();
            
            if (_statusLabel != null)
            {
                _statusLabel.Text = "Dashboard opened";
            }
        }
        
        private void OpenNetworkScanner()
        {
            // Check if already open
            if (_networkScannerForm != null && !_networkScannerForm.IsDisposed)
            {
                _networkScannerForm.Activate();
                return;
            }
            
            _networkScannerForm = new NetworkScannerForm
            {
                MdiParent = this
            };
            _networkScannerForm.Show();
            
            if (_statusLabel != null)
            {
                _statusLabel.Text = "Network Scanner opened";
            }
        }
        
        private void OpenClassicView()
        {
            // Create a non-MDI instance of the classic view
            var classicForm = new MainForm();
            classicForm.Show();
            
            if (_statusLabel != null)
            {
                _statusLabel.Text = "Classic View opened in separate window";
            }
        }
        
        private void RefreshAllWindows()
        {
            foreach (Form child in MdiChildren)
            {
                if (child is DashboardForm || child is NetworkScannerForm)
                {
                    // Trigger refresh - could be implemented via interface
                    child.Refresh();
                }
            }
            
            if (_statusLabel != null)
            {
                _statusLabel.Text = "All windows refreshed";
            }
        }
        
        private void CloseAllWindows()
        {
            foreach (Form child in MdiChildren)
            {
                child.Close();
            }
            
            if (_statusLabel != null)
            {
                _statusLabel.Text = "All windows closed";
            }
        }
        
        private void ShowHelp()
        {
            try
            {
                var helpForm = new HelpForm();
                helpForm.Show(this);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Error opening help:\n\n{ex.Message}",
                    "Help Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
            }
        }
        
        private void ShowKeyboardShortcuts()
        {
            var shortcuts = @"Keyboard Shortcuts:

F1                - Show Help Documentation
Ctrl+D            - Open Dashboard
Ctrl+N            - Open Network Scanner
Ctrl+K            - Open Classic View
Ctrl+W            - Close Active Window
Ctrl+Shift+W      - Close All Windows

Window Management:
Ctrl+1            - Cascade Windows
Ctrl+2            - Tile Horizontally
Ctrl+3            - Tile Vertically

General:
Alt+F4            - Exit Application";
            
            MessageBox.Show(
                shortcuts,
                "Keyboard Shortcuts",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            );
        }
        
        private void ShowAbout()
        {
            var about = @"MODAX - Modular Industrial Control System

Version: 0.4.1
MDI Interface Edition

© 2024 Thomas Heisig
Licensed under MIT License

Features:
• Multi-Document Interface (MDI)
• Real-time Dashboard
• Network Scanner & Port Scanner
• CNC Machine Control
• AI-Powered Analysis
• Comprehensive Monitoring

For more information, visit the documentation (F1)";
            
            MessageBox.Show(
                about,
                "About MODAX",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            );
        }
        
        private void MainFormMdi_KeyDown(object? sender, KeyEventArgs e)
        {
            // Dashboard
            if (e.Control && e.KeyCode == Keys.D)
            {
                e.Handled = true;
                OpenDashboard();
            }
            // Network Scanner
            else if (e.Control && e.KeyCode == Keys.N)
            {
                e.Handled = true;
                OpenNetworkScanner();
            }
            // Classic View
            else if (e.Control && e.KeyCode == Keys.K)
            {
                e.Handled = true;
                OpenClassicView();
            }
            // Close active window
            else if (e.Control && e.KeyCode == Keys.W)
            {
                e.Handled = true;
                if (e.Shift)
                {
                    CloseAllWindows();
                }
                else if (ActiveMdiChild != null)
                {
                    ActiveMdiChild.Close();
                }
            }
            // Window layouts
            else if (e.Control && e.KeyCode == Keys.D1)
            {
                e.Handled = true;
                LayoutMdi(MdiLayout.Cascade);
            }
            else if (e.Control && e.KeyCode == Keys.D2)
            {
                e.Handled = true;
                LayoutMdi(MdiLayout.TileHorizontal);
            }
            else if (e.Control && e.KeyCode == Keys.D3)
            {
                e.Handled = true;
                LayoutMdi(MdiLayout.TileVertical);
            }
            // Help
            else if (e.KeyCode == Keys.F1)
            {
                e.Handled = true;
                ShowHelp();
            }
        }
    }
}
