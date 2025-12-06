# MODAX Setup Guide

## Prerequisites

### Hardware Requirements
- **Field Layer**: ESP32 development board with sensors
- **Control/AI Layers**: Linux/Windows/macOS with Python 3.8+
- **HMI Layer**: Windows machine with .NET 8.0+
- **Network**: WiFi or Ethernet for MQTT communication

### Software Requirements
- Python 3.8 or higher
- .NET 8.0 SDK (for HMI)
- MQTT Broker (e.g., Mosquitto)
- PlatformIO (for ESP32 development)
- Git

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Thomas-Heisig/MODAX.git
cd MODAX
```

### 2. Setup MQTT Broker

#### Option A: Mosquitto (Recommended)
**Linux/macOS:**
```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients  # Ubuntu/Debian
brew install mosquitto                            # macOS

# Start broker
sudo systemctl start mosquitto  # Linux
brew services start mosquitto   # macOS
```

**Windows:**
Download from https://mosquitto.org/download/ and install.

#### Option B: Docker
```bash
docker run -d -p 1883:1883 -p 9001:9001 eclipse-mosquitto
```

### 3. Setup Field Layer (ESP32)

#### Install PlatformIO
```bash
pip install platformio
```

#### Configure WiFi and MQTT
Edit `esp32-field-layer/src/main.cpp`:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "192.168.1.100";  // Your MQTT broker IP
```

#### Build and Upload
```bash
cd esp32-field-layer
pio run --target upload
pio device monitor
```

#### Expected Output
```
=== MODAX Field Layer ESP32 ===
MPU6050 initialized
Connecting to WiFi: YOUR_SSID
...
WiFi connected
IP address: 192.168.1.50
Attempting MQTT connection...connected
Published sensor data: {...}
```

### 4. Setup Control Layer (Python)

#### Install Dependencies
```bash
cd python-control-layer
pip install -r requirements.txt
```

#### Configure Environment
Create `.env` file:
```bash
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
API_HOST=0.0.0.0
API_PORT=8000
AI_ENABLED=true
```

#### Start Control Layer
```bash
python main.py
```

#### Expected Output
```
============================================================
MODAX Control Layer Starting
============================================================
INFO:__main__:Starting MODAX Control Layer
INFO:mqtt_handler:Connecting to MQTT broker at localhost:1883
INFO:mqtt_handler:Connected to MQTT broker
INFO:control_layer:AI analysis thread started
INFO:control_layer:Control Layer started successfully
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Verify Control Layer
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}

curl http://localhost:8000/status
# Expected: {"is_safe":true,"devices_online":[...],...}
```

### 5. Setup AI Layer (Python)

#### Install Dependencies
```bash
cd python-ai-layer
pip install -r requirements.txt
```

#### Start AI Layer
```bash
python main.py
```

#### Expected Output
```
============================================================
MODAX AI Layer Starting
============================================================
INFO:     Started server process [12346]
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### Verify AI Layer
```bash
curl http://localhost:8001/health
# Expected: {"status":"healthy",...}

curl http://localhost:8001/models/info
# Expected: {"anomaly_detection":{...},...}
```

### 6. Setup HMI Layer (C#)

#### Install .NET SDK
Download from https://dotnet.microsoft.com/download/dotnet/8.0

#### Build and Run
```bash
cd csharp-hmi-layer
dotnet restore
dotnet build
dotnet run
```

Or open `MODAX.HMI.csproj` in Visual Studio and press F5.

#### Expected Result
Windows application opens showing:
- System status header
- Device selector
- Real-time sensor data
- Safety status panel
- AI recommendations

## Verification

### Complete System Test

#### 1. Check All Services
```bash
# MQTT Broker
mosquitto_sub -t "modax/#" -v

# Control Layer
curl http://localhost:8000/status

# AI Layer
curl http://localhost:8001/health

# HMI - should show GUI
```

#### 2. Verify Data Flow
Watch MQTT messages:
```bash
mosquitto_sub -t "modax/sensor/data" -v
# Should see JSON data every 100ms

mosquitto_sub -t "modax/sensor/safety" -v
# Should see safety status periodically
```

#### 3. Check HMI
- Select device from dropdown
- Verify sensor readings update every 2 seconds
- Check safety status shows green (if safe)
- Verify AI recommendations appear

#### 4. Test Commands
- In HMI, click START button (if safe)
- Should see command in MQTT topic:
```bash
mosquitto_sub -t "modax/control/commands" -v
```

### Troubleshooting

#### ESP32 Not Connecting to WiFi
```
Symptoms: "Connecting to WiFi..." loop
Solutions:
- Verify WiFi credentials
- Check 2.4GHz network (ESP32 doesn't support 5GHz)
- Ensure ESP32 is in range
```

#### MQTT Connection Failed
```
Symptoms: "Failed to connect to MQTT broker"
Solutions:
- Verify broker is running: sudo systemctl status mosquitto
- Check broker IP/port configuration
- Test with mosquitto_pub: mosquitto_pub -t test -m "hello"
- Check firewall rules
```

#### Control Layer API Not Responding
```
Symptoms: curl timeout or connection refused
Solutions:
- Check if control layer is running
- Verify port 8000 is not in use: lsof -i :8000
- Check firewall/antivirus
- Try localhost instead of 0.0.0.0
```

#### AI Layer Not Receiving Requests
```
Symptoms: No AI analysis in HMI
Solutions:
- Verify AI layer is running on port 8001
- Check control layer can reach AI: curl http://localhost:8001/health
- Review control layer logs for AI errors
- Ensure AI_ENABLED=true in control layer config
```

#### HMI Shows "No Devices"
```
Symptoms: Device dropdown is empty
Solutions:
- Verify ESP32 is publishing data
- Check control layer receives data: curl http://localhost:8000/devices
- Ensure MQTT topics match
- Click Refresh button in HMI
```

## Configuration Files

### MQTT Broker Config
Create `/etc/mosquitto/conf.d/modax.conf`:
```
listener 1883
allow_anonymous true
max_queued_messages 1000
```

Restart: `sudo systemctl restart mosquitto`

### Control Layer `.env`
```bash
# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=              # Optional
MQTT_PASSWORD=              # Optional

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AI Layer
AI_ENABLED=true
```

### ESP32 Configuration
In `esp32-field-layer/src/main.cpp`:
```cpp
// WiFi
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// MQTT
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;

// Device ID (unique per device)
const char* device_id = "ESP32_FIELD_001";
```

## Network Configuration

### Recommended Network Topology
```
Field Network (192.168.1.0/24):
  - ESP32 devices: 192.168.1.50-99
  - MQTT Broker: 192.168.1.100
  - Control Layer: 192.168.1.101
  - AI Layer: 192.168.1.102

Office Network (192.168.2.0/24):
  - HMI clients: 192.168.2.x
  - Gateway to field network
```

### Firewall Rules
```bash
# Allow MQTT
sudo ufw allow 1883/tcp

# Allow Control Layer API
sudo ufw allow 8000/tcp

# Allow AI Layer API (if accessed remotely)
sudo ufw allow 8001/tcp
```

## Production Deployment

### Security Hardening
1. Enable MQTT authentication
2. Use TLS/SSL for all connections
3. Change default ports
4. Implement API authentication
5. Use strong passwords
6. Regular security updates

### Performance Tuning
1. Increase MQTT QoS for critical messages
2. Tune database connection pools
3. Enable caching where appropriate
4. Monitor resource usage
5. Set up log rotation

### Monitoring
1. Setup monitoring for all services
2. Configure alerts for failures
3. Log aggregation (ELK stack)
4. Metrics collection (Prometheus)
5. Health check endpoints

## Next Steps

After successful setup:
1. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. Read component-specific READMEs for details
3. Test safety interlocks with emergency stop
4. Configure AI thresholds for your use case
5. Customize HMI for your requirements

## Support

For issues and questions:
- Check component READMEs
- Review logs for error messages
- Verify network connectivity
- Test each layer independently
- Check GitHub issues

## Quick Start Scripts

### Start All Services (Linux/macOS)
Create `start-all.sh`:
```bash
#!/bin/bash
# Start MQTT broker
mosquitto -c /etc/mosquitto/mosquitto.conf -d

# Start Control Layer
cd python-control-layer
python main.py &
CONTROL_PID=$!

# Start AI Layer
cd ../python-ai-layer
python main.py &
AI_PID=$!

echo "Control Layer PID: $CONTROL_PID"
echo "AI Layer PID: $AI_PID"
echo "All services started"
```

### Stop All Services
Create `stop-all.sh`:
```bash
#!/bin/bash
killall mosquitto
pkill -f "python main.py"
echo "All services stopped"
```

Make executable:
```bash
chmod +x start-all.sh stop-all.sh
```
