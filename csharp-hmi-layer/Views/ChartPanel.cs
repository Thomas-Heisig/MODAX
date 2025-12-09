using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using LiveCharts;
using LiveCharts.Defaults;
using LiveCharts.WinForms;
using LiveCharts.Wpf;
using MODAX.HMI.Models;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Panel containing real-time charts for sensor data visualization
    /// </summary>
    public class ChartPanel : Panel
    {
        private const int DEFAULT_MAX_DATA_POINTS = 50;
        private readonly int _maxDataPoints;
        
        private CartesianChart? _currentChart;
        private CartesianChart? _temperatureChart;
        private CartesianChart? _vibrationChart;
        private PieChart? _wearGauge;
        
        private ChartValues<ObservablePoint> _currentAValues = new();
        private ChartValues<ObservablePoint> _currentBValues = new();
        private ChartValues<ObservablePoint> _currentCValues = new();
        private ChartValues<ObservablePoint> _temperatureValues = new();
        private ChartValues<ObservablePoint> _vibrationValues = new();
        private ChartValues<ObservableValue> _wearValues = new();
        
        private int _dataPointCounter = 0;

        public ChartPanel(int maxDataPoints = DEFAULT_MAX_DATA_POINTS)
        {
            _maxDataPoints = maxDataPoints;
            InitializeCharts();
        }

        private void InitializeCharts()
        {
            // Set panel properties
            Dock = DockStyle.Fill;
            AutoScroll = true;
            BackColor = Color.White;
            Padding = new Padding(10);

            // Create tab control for organizing charts
            var tabControl = new TabControl
            {
                Dock = DockStyle.Fill,
                Font = new Font("Segoe UI", 10F, FontStyle.Regular)
            };

            // Current chart tab
            var currentTab = new TabPage("Motor Current");
            _currentChart = CreateCurrentChart();
            _currentChart.Dock = DockStyle.Fill;
            currentTab.Controls.Add(_currentChart);
            tabControl.TabPages.Add(currentTab);

            // Temperature chart tab
            var temperatureTab = new TabPage("Temperature");
            _temperatureChart = CreateTemperatureChart();
            _temperatureChart.Dock = DockStyle.Fill;
            temperatureTab.Controls.Add(_temperatureChart);
            tabControl.TabPages.Add(temperatureTab);

            // Vibration chart tab
            var vibrationTab = new TabPage("Vibration");
            _vibrationChart = CreateVibrationChart();
            _vibrationChart.Dock = DockStyle.Fill;
            vibrationTab.Controls.Add(_vibrationChart);
            tabControl.TabPages.Add(vibrationTab);

            // Wear gauge tab
            var wearTab = new TabPage("Wear Level");
            var wearPanel = new Panel { Dock = DockStyle.Fill };
            _wearGauge = CreateWearGauge();
            _wearGauge.Dock = DockStyle.Fill;
            wearPanel.Controls.Add(_wearGauge);
            wearTab.Controls.Add(wearPanel);
            tabControl.TabPages.Add(wearTab);

            Controls.Add(tabControl);
        }

        private CartesianChart CreateCurrentChart()
        {
            var chart = new CartesianChart
            {
                DisableAnimations = true,
                Hoverable = false,
                DataTooltip = null
            };

            chart.Series = new SeriesCollection
            {
                new LineSeries
                {
                    Title = "Motor A",
                    Values = _currentAValues,
                    PointGeometry = null,
                    Fill = System.Windows.Media.Brushes.Transparent,
                    Stroke = System.Windows.Media.Brushes.DodgerBlue,
                    StrokeThickness = 2
                },
                new LineSeries
                {
                    Title = "Motor B",
                    Values = _currentBValues,
                    PointGeometry = null,
                    Fill = System.Windows.Media.Brushes.Transparent,
                    Stroke = System.Windows.Media.Brushes.OrangeRed,
                    StrokeThickness = 2
                },
                new LineSeries
                {
                    Title = "Motor C",
                    Values = _currentCValues,
                    PointGeometry = null,
                    Fill = System.Windows.Media.Brushes.Transparent,
                    Stroke = System.Windows.Media.Brushes.Green,
                    StrokeThickness = 2
                }
            };

            chart.AxisX.Add(new Axis
            {
                Title = "Time (samples)",
                LabelFormatter = value => value.ToString("0")
            });

            chart.AxisY.Add(new Axis
            {
                Title = "Current (A)",
                LabelFormatter = value => value.ToString("0.00"),
                MinValue = 0
            });

            chart.LegendLocation = LegendLocation.Top;

            return chart;
        }

        private CartesianChart CreateTemperatureChart()
        {
            var chart = new CartesianChart
            {
                DisableAnimations = true,
                Hoverable = false,
                DataTooltip = null
            };

            chart.Series = new SeriesCollection
            {
                new LineSeries
                {
                    Title = "Temperature",
                    Values = _temperatureValues,
                    PointGeometry = DefaultGeometries.Circle,
                    PointGeometrySize = 5,
                    Fill = System.Windows.Media.Brushes.Transparent,
                    Stroke = System.Windows.Media.Brushes.Crimson,
                    StrokeThickness = 2
                }
            };

            chart.AxisX.Add(new Axis
            {
                Title = "Time (samples)",
                LabelFormatter = value => value.ToString("0")
            });

            chart.AxisY.Add(new Axis
            {
                Title = "Temperature (°C)",
                LabelFormatter = value => value.ToString("0.0"),
                MinValue = 0
            });

            chart.LegendLocation = LegendLocation.Top;

            return chart;
        }

        private CartesianChart CreateVibrationChart()
        {
            var chart = new CartesianChart
            {
                DisableAnimations = true,
                Hoverable = false,
                DataTooltip = null
            };

            chart.Series = new SeriesCollection
            {
                new ColumnSeries
                {
                    Title = "Vibration Magnitude",
                    Values = _vibrationValues,
                    Fill = System.Windows.Media.Brushes.Purple,
                    MaxColumnWidth = 20
                }
            };

            chart.AxisX.Add(new Axis
            {
                Title = "Time (samples)",
                LabelFormatter = value => value.ToString("0")
            });

            chart.AxisY.Add(new Axis
            {
                Title = "Vibration (g)",
                LabelFormatter = value => value.ToString("0.000"),
                MinValue = 0
            });

            chart.LegendLocation = LegendLocation.Top;

            return chart;
        }

        private PieChart CreateWearGauge()
        {
            _wearValues.Add(new ObservableValue(0));
            _wearValues.Add(new ObservableValue(100));

            var chart = new PieChart
            {
                DisableAnimations = false,
                Hoverable = false,
                DataTooltip = null,
                InnerRadius = 80
            };

            chart.Series = new SeriesCollection
            {
                new PieSeries
                {
                    Title = "Wear",
                    Values = new ChartValues<ObservableValue> { _wearValues[0] },
                    Fill = System.Windows.Media.Brushes.OrangeRed,
                    DataLabels = true,
                    LabelPoint = chartPoint => $"{chartPoint.Y:0.0}%"
                },
                new PieSeries
                {
                    Title = "Remaining",
                    Values = new ChartValues<ObservableValue> { _wearValues[1] },
                    Fill = System.Windows.Media.Brushes.LightGray,
                    DataLabels = false
                }
            };

            chart.LegendLocation = LegendLocation.Bottom;

            return chart;
        }

        /// <summary>
        /// Update charts with new sensor data
        /// </summary>
        public void UpdateSensorData(SensorData? data)
        {
            if (data == null) return;

            try
            {
                // Update current chart
                if (data.MotorCurrents.Count >= 3)
                {
                    AddDataPoint(_currentAValues, data.MotorCurrents[0]);
                    AddDataPoint(_currentBValues, data.MotorCurrents[1]);
                    AddDataPoint(_currentCValues, data.MotorCurrents[2]);
                }

                // Update temperature chart
                if (data.Temperatures.Count > 0)
                {
                    AddDataPoint(_temperatureValues, data.Temperatures[0]);
                }

                // Update vibration chart
                if (data.Vibration != null)
                {
                    AddDataPoint(_vibrationValues, data.Vibration.Magnitude);
                }

                _dataPointCounter++;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error updating charts: {ex.Message}");
            }
        }

        /// <summary>
        /// Update wear gauge with AI analysis data
        /// </summary>
        public void UpdateAIAnalysis(AIAnalysis? analysis)
        {
            if (analysis == null) return;

            try
            {
                // Update wear gauge
                var wearPercentage = analysis.PredictedWearLevel * 100;
                _wearValues[0].Value = wearPercentage;
                _wearValues[1].Value = 100 - wearPercentage;

                // Update gauge color based on wear level
                if (_wearGauge != null && _wearGauge.Series.Count > 0)
                {
                    var wearSeries = _wearGauge.Series[0];
                    if (wearPercentage > 80)
                        wearSeries.Fill = System.Windows.Media.Brushes.DarkRed;
                    else if (wearPercentage > 60)
                        wearSeries.Fill = System.Windows.Media.Brushes.OrangeRed;
                    else if (wearPercentage > 40)
                        wearSeries.Fill = System.Windows.Media.Brushes.Orange;
                    else
                        wearSeries.Fill = System.Windows.Media.Brushes.Green;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error updating wear gauge: {ex.Message}");
            }
        }

        /// <summary>
        /// Clear all chart data
        /// </summary>
        public void ClearCharts()
        {
            _currentAValues.Clear();
            _currentBValues.Clear();
            _currentCValues.Clear();
            _temperatureValues.Clear();
            _vibrationValues.Clear();
            _dataPointCounter = 0;

            // Reset wear gauge
            _wearValues[0].Value = 0;
            _wearValues[1].Value = 100;
        }

        private void AddDataPoint(ChartValues<ObservablePoint> values, double yValue)
        {
            // Add new point
            values.Add(new ObservablePoint(_dataPointCounter, yValue));

            // Remove old points if exceeded max
            if (values.Count > _maxDataPoints)
            {
                values.RemoveAt(0);
            }
        }
    }
}
