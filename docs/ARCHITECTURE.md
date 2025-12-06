# MODAX System Architecture

## Overview
MODAX is a 4-layer industrial control system with integrated AI capabilities for predictive maintenance and optimization. The system is designed with safety as the top priority, keeping all safety-critical functions AI-free.

## System Layers

### 1. Field Layer (ESP32)
**Purpose**: Real-time sensor data acquisition and safety monitoring

**Technology**: C++ on ESP32 microcontrollers

**Responsibilities**:
- Read sensors at 10Hz (current, vibration, temperature)
- Monitor safety interlocks at 20Hz (faster for safety)
- Publish data via MQTT
- Execute immediate safety responses (hardware-level)

**Key Features**:
- **Hardware Safety**: Emergency stop, door sensors, overload detection
- **Real-time Processing**: Deterministic timing for safety checks
- **Local Actions**: Can trigger safety relays without network
- **AI-Free Zone**: No AI/ML processing in safety path

**Communication**:
- MQTT Topics: `modax/sensor/data`, `modax/sensor/safety`
- Message Format: JSON (prepared for Protobuf migration)

### 2. Control Layer (Python)
**Purpose**: Central coordination and data aggregation

**Technology**: Python with FastAPI, paho-mqtt

**Responsibilities**:
- Aggregate sensor data from multiple devices
- Interface with AI layer
- Provide REST API for HMI
- Route control commands
- Monitor overall system safety

**Key Features**:
- **Data Aggregation**: Statistical summaries for AI analysis
- **Safety Validation**: Blocks unsafe commands
- **Real-time API**: WebSocket-ready for future enhancements
- **Scalable**: Can handle multiple field devices

**Architecture Components**:
- `control_layer.py`: Main orchestration
- `data_aggregator.py`: Data collection and statistics
- `mqtt_handler.py`: MQTT communication
- `control_api.py`: REST API
- `ai_interface.py`: AI layer communication

**API Endpoints**:
- GET `/status` - System status
- GET `/devices` - Connected devices
- GET `/devices/{id}/data` - Real-time data
- GET `/devices/{id}/ai-analysis` - AI insights
- POST `/control/command` - Send commands

### 3. AI Layer (Python)
**Purpose**: Intelligent analysis and recommendations

**Technology**: Python with NumPy, SciPy, scikit-learn, ONNX Runtime

**Responsibilities**:
- Detect anomalies in sensor patterns
- Predict component wear
- Generate optimization recommendations
- Provide confidence scores

**Current Models**:
1. **Statistical Anomaly Detector**
   - Z-score based detection
   - Adaptive baseline learning
   - Multi-sensor correlation
   - Domain knowledge thresholds

2. **Empirical Wear Predictor**
   - Stress accumulation model
   - Multiple wear factors (current, vibration, temperature)
   - Remaining useful life estimation

3. **Rule-Based Optimizer**
   - Expert system recommendations
   - Efficiency optimization
   - Maintenance scheduling

**Future Enhancements**:
- ONNX deep learning models
- LSTM for time-series prediction
- Autoencoder for anomaly detection
- Transfer learning across devices

**Important**: All AI analysis is **advisory only** and not used for safety decisions.

### 4. HMI Layer (C#)
**Purpose**: Human-machine interface for monitoring and control

**Technology**: C# with Windows Forms, .NET 8.0

**Responsibilities**:
- Display real-time sensor data
- Show safety status prominently
- Present AI recommendations
- Accept operator commands
- Provide system overview

**Key Features**:
- **Real-time Updates**: 2-second refresh cycle
- **Safety Emphasis**: Clear visual separation of safety data
- **AI Transparency**: Clearly labeled advisory information
- **Command Safety**: Blocks commands when system unsafe

**User Interface Sections**:
- System status header
- Real-time sensor displays
- Safety status (green/red indicator)
- AI analysis and recommendations
- Control buttons (safety-validated)

## Data Flow

### Sensor Data Flow
```
ESP32 Sensors → MQTT Broker → Control Layer → {
    → REST API → HMI
    → AI Layer → Analysis → MQTT → Control Layer → HMI
}
```

### Safety Data Flow
```
ESP32 Safety Checks (20Hz) → MQTT (High Priority) → Control Layer → {
    → Immediate logging
    → REST API → HMI (Red/Green display)
    → Command validation
}
```

### Control Command Flow
```
HMI → REST API → Control Layer → {
    Safety Check → [PASS/FAIL]
    → MQTT → Field Layer (if safe)
}
```

## Communication Protocols

### MQTT Topics
| Topic | Purpose | QoS | Rate |
|-------|---------|-----|------|
| `modax/sensor/data` | Sensor readings | 0 | 10Hz |
| `modax/sensor/safety` | Safety status | 1 | 20Hz+ |
| `modax/ai/analysis` | AI results | 1 | ~1/min |
| `modax/control/commands` | Control commands | 1 | On-demand |

### REST API (Control Layer)
- **Base URL**: `http://localhost:8000`
- **Protocol**: HTTP/1.1 (HTTPS in production)
- **Format**: JSON
- **Rate Limiting**: 100 req/sec (configurable)

### AI Analysis API
- **Base URL**: `http://localhost:8001`
- **Protocol**: HTTP/1.1
- **Format**: JSON
- **Timeout**: 5 seconds max

## Safety Architecture

### Safety Principles
1. **Hardware First**: Safety at hardware level (field layer)
2. **AI-Free Safety**: No AI in safety decision path
3. **Fail-Safe Design**: System defaults to safe state
4. **Redundancy**: Multiple safety checks
5. **Deterministic**: Predictable, real-time responses

### Safety Hierarchy
```
Level 1 (Highest): Hardware interlocks on ESP32
Level 2: Field layer software checks (20Hz)
Level 3: Control layer validation
Level 4 (Lowest): HMI command blocking
```

### Safety Interlocks
- Emergency stop button (hardware)
- Safety door sensor (hardware)
- Motor overload detection (10A threshold)
- Temperature limits (85°C threshold)

### Non-Safety AI Usage
AI is used for:
- ✅ Trend analysis
- ✅ Predictive maintenance
- ✅ Efficiency optimization
- ✅ Anomaly detection (advisory)
- ❌ NOT for emergency stops
- ❌ NOT for safety interlocks
- ❌ NOT for real-time control

## Scalability

### Horizontal Scaling
- **Field Layer**: Add more ESP32 devices
- **Control Layer**: Load balance multiple instances
- **AI Layer**: Distribute analysis across workers
- **HMI Layer**: Multiple client connections

### Data Volume
- **Per Device**: ~10 samples/sec = 864,000 samples/day
- **Storage**: Time-series database (future)
- **Aggregation**: Rolling windows reduce data volume

### Performance Targets
- **Field Layer**: <50ms response time
- **Control Layer**: <100ms API latency
- **AI Layer**: <1s analysis time
- **HMI Layer**: <2s update cycle

## Security Considerations

### Network Security
- MQTT authentication (username/password)
- TLS encryption for production
- Network segmentation (OT/IT separation)
- Firewall rules per layer

### Access Control
- Role-based permissions (future)
- Command audit logging
- User authentication on HMI
- API key management

### Data Protection
- Sensor data encryption in transit
- Local data retention limits
- GDPR compliance (if applicable)
- Backup and recovery procedures

## Deployment Topologies

### Development (Single Machine)
```
ESP32 → MQTT Broker (localhost) → {
    Control Layer (port 8000)
    AI Layer (port 8001)
} ← HMI (Windows)
```

### Production (Distributed)
```
Field Network:
  ESP32 devices → Industrial MQTT Broker

Control Network:
  Control Layer (redundant)
  AI Layer (cluster)
  Time-series DB

Office Network:
  HMI clients (multiple)
  Monitoring dashboards
```

### Edge Deployment
```
Edge Device:
  - Control Layer
  - AI Layer
  - MQTT Broker
  - Local storage

Cloud (optional):
  - Long-term storage
  - Fleet analytics
  - Model training
```

## Technology Stack Summary

| Layer | Language | Framework | Key Libraries |
|-------|----------|-----------|---------------|
| Field | C++ | Arduino/ESP32 | PubSubClient, Adafruit |
| Control | Python 3.8+ | FastAPI | paho-mqtt, numpy |
| AI | Python 3.8+ | FastAPI | scikit-learn, onnxruntime |
| HMI | C# | .NET 8.0 | WinForms, Newtonsoft.Json |

## Future Roadmap

### Phase 1 (Complete)
- ✅ Basic 4-layer architecture
- ✅ Statistical anomaly detection
- ✅ Empirical wear prediction
- ✅ Safety-first design

### Phase 2 (Next)
- ONNX model deployment
- Time-series database integration
- Advanced visualizations (charts)
- WebSocket real-time updates

### Phase 3 (Future)
- Machine learning model training pipeline
- Fleet-wide analytics
- Cloud integration
- Mobile app (monitoring only)
- Automated maintenance scheduling

## References
- IEC 61508: Functional Safety
- MQTT v3.1.1 Specification
- ONNX Format Specification
- Industrial IoT Best Practices
