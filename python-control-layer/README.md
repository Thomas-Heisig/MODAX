# Python Control Layer

## Overview
The Control Layer is the central coordination component of the MODAX system. It aggregates sensor data from the field layer (ESP32), interfaces with the AI layer for analysis, and provides a REST API for the HMI layer.

## Architecture
```
Field Layer (ESP32) --> MQTT --> Control Layer --> REST API --> HMI Layer
                                       |
                                       v
                                   AI Layer
```

## Features
- **MQTT Communication**: Receives sensor data and safety status from field devices
- **Data Aggregation**: Collects and aggregates sensor readings for AI analysis
- **Safety Monitoring**: Tracks safety-critical status across all devices
- **AI Integration**: Requests analysis from AI layer and distributes results
- **REST API**: Provides HTTP interface for HMI and monitoring tools
- **Real-time Processing**: Handles sensor data streams at 10Hz

## Installation

### Requirements
- Python 3.8 or higher
- MQTT Broker (e.g., Mosquitto)

### Setup
```bash
cd python-control-layer
pip install -r requirements.txt
```

### Configuration
Create a `.env` file or set environment variables:
```bash
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
API_HOST=0.0.0.0
API_PORT=8000
AI_ENABLED=true
```

## Running

### Start the control layer:
```bash
python main.py
```

The control layer will:
1. Connect to the MQTT broker
2. Subscribe to sensor and safety topics
3. Start the REST API server on port 8000
4. Begin periodic AI analysis (if enabled)

## API Endpoints

### System Status
- `GET /status` - Overall system status
- `GET /health` - Health check
- `GET /ai/status` - AI layer status

### Device Management
- `GET /devices` - List all connected devices
- `GET /devices/{device_id}/data` - Latest data from a device
- `GET /devices/{device_id}/history` - Historical data
- `GET /devices/{device_id}/ai-analysis` - Latest AI analysis

### Control
- `POST /control/command` - Send control command

Example command:
```json
{
  "command_type": "start",
  "parameters": {
    "speed": "100",
    "mode": "auto"
  }
}
```

## Data Flow

### Sensor Data Flow
1. ESP32 publishes sensor data to `modax/sensor/data`
2. Control layer receives and aggregates data
3. Periodically sends aggregated data to AI layer
4. AI analysis results published to `modax/ai/analysis`
5. HMI retrieves data via REST API

### Safety Flow
1. ESP32 publishes safety status to `modax/sensor/safety`
2. Control layer monitors safety state
3. Safety alerts logged immediately
4. Unsafe state prevents control commands
5. HMI displays safety status via REST API

## Components

### `control_layer.py`
Main orchestration component that coordinates all other modules.

### `data_aggregator.py`
Collects and aggregates sensor data for analysis. Maintains ring buffers of recent data and calculates statistical summaries.

### `mqtt_handler.py`
Manages MQTT communication with field layer and AI layer.

### `control_api.py`
FastAPI-based REST API for HMI integration.

### `ai_interface.py`
Interface to AI layer for requesting analysis.

### `config.py`
Configuration management for all components.

## Safety Features
- Control commands blocked when system is not safe
- Safety status monitored independently of AI
- Immediate logging of safety alerts
- Separate high-priority MQTT topic for safety data

## Monitoring
Monitor the control layer with:
```bash
# Check logs
tail -f control_layer.log

# Check API
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/status
```
