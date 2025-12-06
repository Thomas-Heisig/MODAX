using System;
using System.Collections.Generic;

namespace MODAX.HMI.Models
{
    /// <summary>
    /// Sensor data from a field device
    /// </summary>
    public class SensorData
    {
        public string DeviceId { get; set; } = string.Empty;
        public long Timestamp { get; set; }
        public List<double> MotorCurrents { get; set; } = new();
        public VibrationData Vibration { get; set; } = new();
        public List<double> Temperatures { get; set; } = new();
        public SafetyStatus? SafetyStatus { get; set; }

        public DateTime GetDateTime()
        {
            return DateTimeOffset.FromUnixTimeMilliseconds(Timestamp).DateTime;
        }
    }

    /// <summary>
    /// Vibration measurement data
    /// </summary>
    public class VibrationData
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
        public double Magnitude { get; set; }
    }

    /// <summary>
    /// Safety status from field layer
    /// CRITICAL: Safety decisions are made in field layer, not by AI
    /// </summary>
    public class SafetyStatus
    {
        public bool EmergencyStop { get; set; }
        public bool DoorClosed { get; set; }
        public bool OverloadDetected { get; set; }
        public bool TemperatureOk { get; set; }

        public bool IsSafe()
        {
            return !EmergencyStop && DoorClosed && !OverloadDetected && TemperatureOk;
        }

        public string GetStatusDescription()
        {
            if (IsSafe())
                return "System Safe";

            var issues = new List<string>();
            if (EmergencyStop) issues.Add("Emergency Stop Active");
            if (!DoorClosed) issues.Add("Door Open");
            if (OverloadDetected) issues.Add("Overload Detected");
            if (!TemperatureOk) issues.Add("Temperature Alert");

            return string.Join(", ", issues);
        }
    }

    /// <summary>
    /// AI analysis results
    /// ADVISORY ONLY - Not used for safety decisions
    /// </summary>
    public class AIAnalysis
    {
        public string DeviceId { get; set; } = string.Empty;
        public long Timestamp { get; set; }
        public bool AnomalyDetected { get; set; }
        public double AnomalyScore { get; set; }
        public string AnomalyDescription { get; set; } = string.Empty;
        public double PredictedWearLevel { get; set; }
        public int EstimatedRemainingHours { get; set; }
        public List<string> Recommendations { get; set; } = new();
        public double Confidence { get; set; }

        public DateTime GetDateTime()
        {
            return DateTimeOffset.FromUnixTimeMilliseconds(Timestamp).DateTime;
        }

        public string GetWearLevelDescription()
        {
            if (PredictedWearLevel > 0.8)
                return "Critical";
            if (PredictedWearLevel > 0.6)
                return "High";
            if (PredictedWearLevel > 0.4)
                return "Moderate";
            if (PredictedWearLevel > 0.2)
                return "Low";
            return "Minimal";
        }
    }

    /// <summary>
    /// System status overview
    /// </summary>
    public class SystemStatus
    {
        public bool IsSafe { get; set; }
        public List<string> DevicesOnline { get; set; } = new();
        public bool AiEnabled { get; set; }
        public double LastUpdate { get; set; }

        public string GetStatusText()
        {
            if (!IsSafe)
                return "UNSAFE";
            if (DevicesOnline.Count == 0)
                return "No Devices";
            return "Operational";
        }
    }
}
