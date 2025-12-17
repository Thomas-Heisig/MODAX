using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Linq;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Help documentation browser for MODAX HMI
    /// Displays markdown documentation with navigation
    /// </summary>
    public partial class HelpForm : Form
    {
        private readonly string _docsBasePath;
        private TreeView? _navigationTree;
        private RichTextBox? _contentDisplay;
        private TextBox? _searchBox;
        private Button? _searchButton;
        private Label? _titleLabel;
        private string _currentDocPath = "";

        // Documentation structure
        private readonly Dictionary<string, List<(string Title, string Path)>> _docCategories;

        public HelpForm()
        {
            // Determine docs base path
            _docsBasePath = Path.Combine(
                Path.GetDirectoryName(Application.ExecutablePath) ?? "",
                "..", "..", "..", "..", "docs"
            );

            // Normalize path
            _docsBasePath = Path.GetFullPath(_docsBasePath);

            // Initialize documentation structure
            _docCategories = InitializeDocumentationStructure();

            InitializeComponents();
            LoadDocumentation("HELP.md");
        }

        private Dictionary<string, List<(string Title, string Path)>> InitializeDocumentationStructure()
        {
            return new Dictionary<string, List<(string Title, string Path)>>
            {
                ["Quick Start"] = new List<(string, string)>
                {
                    ("Help & Overview", "HELP.md"),
                    ("README", "../README.md"),
                    ("Setup Guide", "SETUP.md"),
                    ("Quick Reference", "QUICK_REFERENCE.md"),
                    ("Troubleshooting", "TROUBLESHOOTING.md")
                },
                ["Architecture"] = new List<(string, string)>
                {
                    ("System Architecture", "ARCHITECTURE.md"),
                    ("Network Architecture", "NETWORK_ARCHITECTURE.md"),
                    ("Documentation Index", "INDEX.md")
                },
                ["Configuration"] = new List<(string, string)>
                {
                    ("Configuration Guide", "CONFIGURATION.md"),
                    ("Containerization", "CONTAINERIZATION.md"),
                    ("CI/CD Pipeline", "CI_CD.md"),
                    ("High Availability", "HIGH_AVAILABILITY.md")
                },
                ["APIs & Integration"] = new List<(string, string)>
                {
                    ("API Reference", "API.md"),
                    ("Device Integration", "DEVICE_INTEGRATION.md"),
                    ("OPC UA Integration", "OPC_UA_INTEGRATION.md"),
                    ("MQTT Sparkplug B", "MQTT_SPARKPLUG_B.md"),
                    ("External Integrations", "EXTERNAL_INTEGRATIONS.md")
                },
                ["CNC & Manufacturing"] = new List<(string, string)>
                {
                    ("CNC Features", "CNC_FEATURES.md"),
                    ("Extended G-Code", "EXTENDED_GCODE_SUPPORT.md"),
                    ("Hobbyist CNC Systems", "HOBBYIST_CNC_SYSTEMS.md"),
                    ("Industry 4.0", "ADVANCED_CNC_INDUSTRY_4_0.md")
                },
                ["Security"] = new List<(string, string)>
                {
                    ("Security Overview", "SECURITY.md"),
                    ("Security Implementation", "SECURITY_IMPLEMENTATION.md"),
                    ("Authentication Guide", "AUTHENTICATION_IMPLEMENTATION_GUIDE.md"),
                    ("API Authentication", "API_AUTHENTICATION_GUIDE.md")
                },
                ["Monitoring & Operations"] = new List<(string, string)>
                {
                    ("Monitoring Setup", "MONITORING.md"),
                    ("Logging Standards", "LOGGING_STANDARDS.md"),
                    ("Backup & Recovery", "BACKUP_RECOVERY.md"),
                    ("Data Persistence", "DATA_PERSISTENCE.md")
                },
                ["Testing & Quality"] = new List<(string, string)>
                {
                    ("Testing Guide", "TESTING.md"),
                    ("Best Practices", "BEST_PRACTICES.md"),
                    ("Error Handling", "ERROR_HANDLING.md")
                },
                ["Advanced Features"] = new List<(string, string)>
                {
                    ("ML Training Pipeline", "ML_TRAINING_PIPELINE.md"),
                    ("ONNX Deployment", "ONNX_MODEL_DEPLOYMENT.md"),
                    ("Digital Twin", "DIGITAL_TWIN_INTEGRATION.md"),
                    ("Federated Learning", "FEDERATED_LEARNING.md"),
                    ("Fleet Analytics", "FLEET_ANALYTICS.md"),
                    ("Cloud Integration", "CLOUD_INTEGRATION.md"),
                    ("Multi-Tenant", "MULTI_TENANT_ARCHITECTURE.md"),
                    ("Mobile App", "MOBILE_APP_ARCHITECTURE.md"),
                    ("Features Roadmap", "ADVANCED_FEATURES_ROADMAP.md")
                },
                ["Reference"] = new List<(string, string)>
                {
                    ("Function Reference", "FUNCTION_REFERENCE.md"),
                    ("Glossary", "GLOSSARY.md"),
                    ("TOFU Quick Wins", "TOFU.md")
                }
            };
        }

        private void InitializeComponents()
        {
            // Form setup
            Text = "MODAX - Help Documentation";
            Size = new Size(1200, 800);
            StartPosition = FormStartPosition.CenterScreen;
            MinimumSize = new Size(800, 600);

            // Main layout - split between navigation and content
            var mainSplitter = new SplitContainer
            {
                Dock = DockStyle.Fill,
                SplitterDistance = 300,
                BorderStyle = BorderStyle.FixedSingle
            };

            // Left panel - Navigation
            var leftPanel = new Panel
            {
                Dock = DockStyle.Fill
            };

            // Search box at top
            var searchPanel = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                Padding = new Padding(5)
            };

            _searchBox = new TextBox
            {
                Location = new Point(5, 15),
                Width = 200,
                PlaceholderText = "Search documentation..."
            };
            _searchBox.KeyDown += SearchBox_KeyDown;
            searchPanel.Controls.Add(_searchBox);

            _searchButton = new Button
            {
                Text = "Search",
                Location = new Point(210, 13),
                Width = 70
            };
            _searchButton.Click += SearchButton_Click;
            searchPanel.Controls.Add(_searchButton);

            leftPanel.Controls.Add(searchPanel);

            // Navigation tree
            _navigationTree = new TreeView
            {
                Dock = DockStyle.Fill,
                Font = new Font("Arial", 10)
            };
            _navigationTree.AfterSelect += NavigationTree_AfterSelect;
            PopulateNavigationTree();
            leftPanel.Controls.Add(_navigationTree);

            mainSplitter.Panel1.Controls.Add(leftPanel);

            // Right panel - Content display
            var rightPanel = new Panel
            {
                Dock = DockStyle.Fill,
                Padding = new Padding(10)
            };

            // Title label
            _titleLabel = new Label
            {
                Dock = DockStyle.Top,
                Font = new Font("Arial", 16, FontStyle.Bold),
                Height = 40,
                Text = "MODAX Help Documentation"
            };
            rightPanel.Controls.Add(_titleLabel);

            // Content display
            _contentDisplay = new RichTextBox
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                Font = new Font("Consolas", 10),
                BackColor = Color.White,
                BorderStyle = BorderStyle.None
            };
            rightPanel.Controls.Add(_contentDisplay);

            mainSplitter.Panel2.Controls.Add(rightPanel);
            Controls.Add(mainSplitter);

            // Add keyboard shortcuts
            KeyPreview = true;
            KeyDown += HelpForm_KeyDown;
        }

        private void PopulateNavigationTree()
        {
            if (_navigationTree == null) return;

            _navigationTree.Nodes.Clear();

            foreach (var category in _docCategories)
            {
                var categoryNode = new TreeNode(category.Key)
                {
                    Tag = null,
                    NodeFont = new Font(_navigationTree.Font, FontStyle.Bold)
                };

                foreach (var (title, path) in category.Value)
                {
                    var docNode = new TreeNode(title)
                    {
                        Tag = path
                    };
                    categoryNode.Nodes.Add(docNode);
                }

                _navigationTree.Nodes.Add(categoryNode);
            }

            // Expand Quick Start by default
            if (_navigationTree.Nodes.Count > 0)
            {
                _navigationTree.Nodes[0].Expand();
            }
        }

        private void NavigationTree_AfterSelect(object? sender, TreeViewEventArgs e)
        {
            if (e.Node?.Tag is string docPath)
            {
                LoadDocumentation(docPath);
            }
        }

        private void LoadDocumentation(string relativePath)
        {
            if (_contentDisplay == null || _titleLabel == null) return;

            try
            {
                string fullPath = Path.Combine(_docsBasePath, relativePath);
                fullPath = Path.GetFullPath(fullPath);

                if (!File.Exists(fullPath))
                {
                    _contentDisplay.Text = $"Documentation file not found: {relativePath}\n\n" +
                                          $"Expected location: {fullPath}\n\n" +
                                          "Please ensure the documentation files are in the correct location.";
                    _titleLabel.Text = "File Not Found";
                    return;
                }

                _currentDocPath = fullPath;
                string content = File.ReadAllText(fullPath);

                // Extract title from first line if it's a markdown header
                string title = Path.GetFileNameWithoutExtension(relativePath);
                var lines = content.Split('\n');
                if (lines.Length > 0 && lines[0].StartsWith("# "))
                {
                    title = lines[0].Substring(2).Trim();
                }

                _titleLabel.Text = title;

                // Simple markdown rendering
                _contentDisplay.Text = RenderMarkdown(content);
                _contentDisplay.SelectionStart = 0;
                _contentDisplay.ScrollToCaret();
            }
            catch (Exception ex)
            {
                _contentDisplay.Text = $"Error loading documentation:\n\n{ex.Message}";
                _titleLabel.Text = "Error";
            }
        }

        private string RenderMarkdown(string markdown)
        {
            // Simple markdown to plain text conversion
            // In a production system, you might use a proper markdown renderer
            var lines = markdown.Split('\n');
            var result = new System.Text.StringBuilder();

            foreach (var line in lines)
            {
                string processed = line;

                // Remove markdown formatting for display
                processed = System.Text.RegularExpressions.Regex.Replace(processed, @"\*\*(.*?)\*\*", "$1"); // Bold
                processed = System.Text.RegularExpressions.Regex.Replace(processed, @"\*(.*?)\*", "$1"); // Italic
                processed = System.Text.RegularExpressions.Regex.Replace(processed, @"`(.*?)`", "$1"); // Code
                processed = System.Text.RegularExpressions.Regex.Replace(processed, @"\[(.*?)\]\(.*?\)", "$1"); // Links

                result.AppendLine(processed);
            }

            return result.ToString();
        }

        private void SearchButton_Click(object? sender, EventArgs e)
        {
            PerformSearch();
        }

        private void SearchBox_KeyDown(object? sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                e.Handled = true;
                PerformSearch();
            }
        }

        private void PerformSearch()
        {
            if (_searchBox == null || _navigationTree == null) return;

            string searchTerm = _searchBox.Text.Trim().ToLower();
            if (string.IsNullOrEmpty(searchTerm)) return;

            // Search through all documents
            var results = new List<(string Category, string Title, string Path, int Score)>();

            foreach (var category in _docCategories)
            {
                foreach (var (title, path) in category.Value)
                {
                    int score = 0;

                    // Check title match
                    if (title.ToLower().Contains(searchTerm))
                    {
                        score += 10;
                    }

                    // Check content match (if file exists)
                    try
                    {
                        string fullPath = Path.Combine(_docsBasePath, path);
                        if (File.Exists(fullPath))
                        {
                            string content = File.ReadAllText(fullPath).ToLower();
                            int occurrences = (content.Length - content.Replace(searchTerm, "").Length) / searchTerm.Length;
                            score += occurrences;
                        }
                    }
                    catch
                    {
                        // Skip files that can't be read
                    }

                    if (score > 0)
                    {
                        results.Add((category.Key, title, path, score));
                    }
                }
            }

            // Sort by score and show results
            results = results.OrderByDescending(r => r.Score).ToList();

            if (results.Count == 0)
            {
                MessageBox.Show(
                    $"No results found for '{searchTerm}'.",
                    "Search Results",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
                return;
            }

            // If only one result, load it directly
            if (results.Count == 1)
            {
                LoadDocumentation(results[0].Path);
                HighlightNodeInTree(results[0].Path);
                return;
            }

            // Show search results dialog
            ShowSearchResults(searchTerm, results);
        }

        private void ShowSearchResults(string searchTerm, List<(string Category, string Title, string Path, int Score)> results)
        {
            var resultsForm = new Form
            {
                Text = $"Search Results for '{searchTerm}'",
                Size = new Size(600, 400),
                StartPosition = FormStartPosition.CenterParent
            };

            var listView = new ListView
            {
                Dock = DockStyle.Fill,
                View = View.Details,
                FullRowSelect = true,
                GridLines = true
            };

            listView.Columns.Add("Title", 250);
            listView.Columns.Add("Category", 150);
            listView.Columns.Add("Relevance", 100);

            foreach (var (category, title, path, score) in results.Take(20))
            {
                var item = new ListViewItem(title);
                item.SubItems.Add(category);
                item.SubItems.Add(score.ToString());
                item.Tag = path;
                listView.Items.Add(item);
            }

            listView.DoubleClick += (s, e) =>
            {
                if (listView.SelectedItems.Count > 0 && listView.SelectedItems[0].Tag is string path)
                {
                    LoadDocumentation(path);
                    HighlightNodeInTree(path);
                    resultsForm.Close();
                }
            };

            resultsForm.Controls.Add(listView);
            resultsForm.ShowDialog(this);
        }

        private void HighlightNodeInTree(string docPath)
        {
            if (_navigationTree == null) return;

            foreach (TreeNode categoryNode in _navigationTree.Nodes)
            {
                foreach (TreeNode docNode in categoryNode.Nodes)
                {
                    if (docNode.Tag is string path && path == docPath)
                    {
                        _navigationTree.SelectedNode = docNode;
                        docNode.EnsureVisible();
                        return;
                    }
                }
            }
        }

        private void HelpForm_KeyDown(object? sender, KeyEventArgs e)
        {
            // Escape to close
            if (e.KeyCode == Keys.Escape)
            {
                Close();
            }
            // Ctrl+F to focus search
            else if (e.Control && e.KeyCode == Keys.F)
            {
                _searchBox?.Focus();
                e.Handled = true;
            }
        }
    }
}
