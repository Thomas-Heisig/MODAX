# C# HMI Layer

## Overview
The HMI (Human-Machine Interface) layer provides a Windows Forms-based graphical interface for monitoring and controlling the MODAX industrial system. It displays real-time sensor data, safety status, and AI-generated recommendations.

## Features
- **Real-time Monitoring**: Live display of sensor data (currents, vibration, temperature)
- **Safety Status Display**: Clear visualization of safety-critical status (AI-free zone)
- **AI Recommendations**: Advisory information from AI analysis
- **Wear Prediction Display**: Visual representation of component wear levels
- **Control Commands**: Send start/stop commands (only when system is safe)
- **Multi-Device Support**: Switch between multiple field devices

## Architecture
```
HMI (C# WinForms) <--> REST API <--> Control Layer
                                        |
                                        v
                                   AI Analysis (Advisory)
```

## Requirements
- .NET 8.0 SDK or higher
- Windows operating system
- Running Control Layer (Python) on localhost:8000

## Building

### Using Visual Studio
1. Open `MODAX.HMI.csproj` in Visual Studio 2022 or later
2. Build solution (Ctrl+Shift+B)
3. Run (F5)

### Using .NET CLI
```bash
cd csharp-hmi-layer
dotnet restore
dotnet build
dotnet run
```

## Configuration
The HMI connects to the Control Layer at `http://localhost:8000` by default. To change this, modify the `ControlLayerClient` constructor in `Services/ControlLayerClient.cs`:

```csharp
public ControlLayerClient(string baseUrl = "http://YOUR_CONTROL_LAYER:8000")
```

## User Interface

### Main Screen Layout

#### 1. Header Section
- System status overview
- Device selector dropdown
- Refresh button

#### 2. Sensor Data Panel (Left)
- **Motor Currents**: Real-time current readings for each motor
- **Vibration**: 3-axis acceleration and overall magnitude
- **Temperature**: Temperature sensor readings

#### 3. Safety Status Panel (Right)
- **Safety Status Display**: 
  - GREEN: System safe (all interlocks satisfied)
  - RED: Unsafe condition detected
- **Status Details**: Shows specific safety issues
- **Control Buttons**:
  - START: Enabled only when system is safe
  - STOP: Always enabled for emergency shutdown

#### 4. AI Analysis Panel (Bottom)
- **Anomaly Detection**: Shows if AI detected unusual patterns
- **Wear Level**: Progress bar showing component wear
- **Recommendations**: Actionable advice from AI analysis

### Safety Design
The HMI clearly distinguishes between:
- **Safety-Critical Data** (from field layer, AI-free): Displayed prominently in Safety Status panel
- **Advisory AI Data**: Clearly labeled as "Advisory Only" and displayed separately

Control commands are blocked if the system is not in a safe state, regardless of AI recommendations.

## Data Update Cycle
- **Update Frequency**: Every 2 seconds
- **Device Data**: Latest sensor readings
- **AI Analysis**: Most recent AI recommendations
- **Safety Status**: Real-time safety interlock states

## Components

### Models/
- `SensorData.cs`: Data models for sensor readings
- Safety status and AI analysis models

### Services/
- `ControlLayerClient.cs`: HTTP client for Control Layer API

### Views/
- `MainForm.cs`: Main application window

### Program.cs
Application entry point

## Usage

### Starting the HMI
1. Ensure Control Layer is running (port 8000)
2. Launch the HMI application
3. Select a device from the dropdown
4. Monitor real-time data and safety status

### Sending Commands
1. Verify system is in "Safe" state (green safety panel)
2. Click START or STOP button
3. Command is sent to Control Layer
4. Confirmation dialog appears

### Interpreting AI Recommendations
AI recommendations are **advisory only** and include:
- Anomaly alerts (unusual patterns)
- Wear predictions (remaining useful life)
- Optimization suggestions (efficiency improvements)
- Maintenance recommendations

**IMPORTANT**: Do NOT use AI recommendations for safety decisions. All safety logic is in the field layer.

## Error Handling
- Connection errors are logged to console
- Failed API calls return gracefully
- Disconnected state is indicated in UI
- Commands fail gracefully with user notification

## Extending the HMI

### Adding New Visualizations
1. Add controls in `CreateXXXPanel()` methods
2. Update data in corresponding `UpdateXXXAsync()` methods
3. Follow existing patterns for data binding

### Adding New Commands
1. Add button in `CreateSafetyPanel()`
2. Create command handler calling `SendCommandAsync()`
3. Ensure safety checks are maintained

### Adding Charts
The project includes LiveCharts.WinForms for advanced visualizations:
```csharp
using LiveCharts;
using LiveCharts.WinForms;

var chart = new CartesianChart
{
    Location = new Point(x, y),
    Size = new Size(width, height)
};
// Configure chart...
```

## Security Considerations
- API endpoints should use authentication in production
- Use HTTPS for remote connections
- Validate all user inputs
- Log all control commands with user identity
- Implement role-based access control for commands

## Testing
Test the HMI with:
1. Control Layer running without field devices (simulated data)
2. Multiple devices connected
3. Safety condition changes
4. AI anomaly detection triggers
5. Network disconnections

## Troubleshooting

### "Cannot connect to Control Layer"
- Verify Control Layer is running on port 8000
- Check firewall settings
- Ensure correct base URL in ControlLayerClient

### "No devices available"
- Check if field devices (ESP32) are connected
- Verify MQTT broker is running
- Check Control Layer logs

### "Commands disabled"
- Verify system safety status is green
- Check for emergency stop or open doors
- Review safety interlock states
