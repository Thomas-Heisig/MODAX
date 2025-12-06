# Python AI Layer

## Overview
The AI Layer provides intelligent analysis of sensor data from industrial equipment. It performs anomaly detection, wear prediction, and generates optimization recommendations. This layer is explicitly designed to be **advisory only** - all safety-critical decisions remain in the control layer and field layer.

## Features
- **Statistical Anomaly Detection**: Detects abnormal patterns in current, vibration, and temperature
- **Wear Prediction**: Estimates component wear and remaining useful life
- **Optimization Recommendations**: Provides actionable advice to improve efficiency
- **Non-Safety-Critical**: All analysis is for advisory purposes only
- **ONNX-Ready**: Architecture supports future ML model integration

## AI Models

### 1. Anomaly Detection (Statistical)
- **Method**: Z-score based statistical analysis with domain knowledge thresholds
- **Inputs**: Current, vibration, temperature statistics
- **Outputs**: Anomaly score (0.0-1.0), description, confidence
- **Features**:
  - Adaptive baseline learning
  - Multi-sensor correlation
  - Threshold-based alerts
  - Pattern recognition

### 2. Wear Prediction (Empirical)
- **Method**: Cumulative stress factor model
- **Inputs**: Operating conditions over time
- **Outputs**: Wear level (0.0-1.0), estimated remaining hours
- **Factors**:
  - Current load (exponential impact)
  - Vibration levels
  - Temperature stress
  - Operating time accumulation

### 3. Optimization Recommender (Rule-Based)
- **Method**: Expert system with domain knowledge
- **Inputs**: Sensor analysis + anomaly/wear results
- **Outputs**: Prioritized recommendations
- **Categories**:
  - Load optimization
  - Maintenance scheduling
  - Energy efficiency
  - Preventive actions

## Installation

### Requirements
- Python 3.8 or higher

### Setup
```bash
cd python-ai-layer
pip install -r requirements.txt
```

## Running

### Start the AI service:
```bash
python main.py
```

The AI service will start on port 8001 and provide a REST API for analysis requests.

## API Endpoints

### Analysis
- `POST /analyze` - Analyze sensor data and provide insights

Example request:
```json
{
  "device_id": "ESP32_FIELD_001",
  "time_window_start": 1234567890.0,
  "time_window_end": 1234567900.0,
  "current_mean": [4.5, 4.3],
  "current_std": [0.5, 0.4],
  "current_max": [6.2, 5.8],
  "vibration_mean": {"x": 1.2, "y": 1.1, "z": 1.3, "magnitude": 2.1},
  "vibration_std": {"x": 0.3, "y": 0.3, "z": 0.4, "magnitude": 0.5},
  "vibration_max": {"x": 2.5, "y": 2.3, "z": 2.8, "magnitude": 4.2},
  "temperature_mean": [45.5],
  "temperature_max": [52.3],
  "sample_count": 100
}
```

Example response:
```json
{
  "timestamp": 1234567900000,
  "device_id": "ESP32_FIELD_001",
  "anomaly_detected": false,
  "anomaly_score": 0.0,
  "anomaly_description": "No anomalies detected",
  "predicted_wear_level": 0.15,
  "estimated_remaining_hours": 8500,
  "recommendations": [
    "System operating within normal parameters",
    "Wear accumulation progressing normally"
  ],
  "confidence": 0.82
}
```

### Maintenance
- `POST /reset-wear/{device_id}` - Reset wear counter after maintenance

### Information
- `GET /` - API information
- `GET /health` - Health check
- `GET /models/info` - Model information

## Architecture

### Data Flow
```
Control Layer --> POST /analyze --> AI Analysis --> Response --> Control Layer
                                    |
                                    v
                    [Anomaly Detection + Wear Prediction + Optimization]
```

### Model Pipeline
1. **Input Validation**: Verify sensor data completeness
2. **Anomaly Detection**: Analyze each sensor type independently
3. **Wear Prediction**: Calculate cumulative wear factors
4. **Recommendation Generation**: Synthesize actionable advice
5. **Baseline Update**: Learn from new data for adaptive thresholds

## Safety Design

### AI-Free Safety Zone
The AI layer explicitly **DOES NOT** participate in safety decisions:
- ❌ No control over emergency stops
- ❌ No control over safety interlocks
- ❌ No real-time safety monitoring
- ✅ Advisory recommendations only
- ✅ Trend analysis and prediction
- ✅ Optimization suggestions

Safety functions remain in field layer (ESP32) hardware.

## Future Enhancements

### Planned ML Integration
The architecture is designed to support ONNX models for:
1. **Deep Learning Anomaly Detection**
   - Autoencoder for pattern learning
   - LSTM for time-series prediction
   - CNN for vibration signature analysis

2. **Advanced Wear Models**
   - Remaining Useful Life (RUL) prediction
   - Failure mode classification
   - Maintenance scheduling optimization

3. **Multi-Device Correlation**
   - Fleet-wide analysis
   - Comparative benchmarking
   - Transfer learning across devices

### Model Development Workflow
```
Historical Data --> Training --> ONNX Export --> Deployment --> Inference
                      |                              |
                      v                              v
              Model Validation              Performance Monitoring
```

## Performance
- **Analysis Latency**: <100ms typical
- **Throughput**: 1000+ analyses/second
- **Memory**: ~200MB baseline
- **CPU**: Minimal (statistical models)

## Monitoring
Check AI service status:
```bash
# Health check
curl http://localhost:8001/health

# Model info
curl http://localhost:8001/models/info

# Test analysis
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

## Development

### Adding New Models
1. Create model class in new file (e.g., `new_model.py`)
2. Implement prediction interface
3. Import and initialize in `ai_service.py`
4. Add to analysis pipeline
5. Update API documentation

### Testing Models
```bash
# Unit tests (to be added)
pytest tests/

# Integration test with control layer
python test_integration.py
```
