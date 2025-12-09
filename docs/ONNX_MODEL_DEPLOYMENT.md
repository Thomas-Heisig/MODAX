# ONNX Model Deployment Guide

**Last Updated:** 2025-12-09  
**Status:** Implemented  
**Version:** 1.0

## Overview

MODAX AI Layer now supports ONNX-based deep learning models for Remaining Useful Life (RUL) prediction. This enables advanced predictive maintenance using time-series models like LSTM and TCN (Temporal Convolutional Networks).

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Layer                                  │
│                                                               │
│  ┌─────────────────┐     ┌──────────────────┐              │
│  │  Statistical    │     │   ONNX Runtime   │              │
│  │  Predictor      │     │   RUL Predictor  │              │
│  │  (Fallback)     │     │   (Primary)      │              │
│  └─────────────────┘     └──────────────────┘              │
│           │                        │                         │
│           └────────────┬───────────┘                         │
│                        │                                     │
│                ┌───────▼────────┐                           │
│                │  Prediction     │                           │
│                │  Aggregator     │                           │
│                └────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Sensor Data Collection**: Control layer sends aggregated sensor data
2. **Feature Extraction**: Extract 6 key features from sensor data
3. **Sequence Building**: Build time-series sequence (default: 50 time steps)
4. **Normalization**: Apply feature normalization using training parameters
5. **Inference**: Run ONNX model inference
6. **Post-processing**: Convert raw output to actionable RUL prediction
7. **Recommendation Generation**: Generate maintenance recommendations

## Supported Models

### Model Types

1. **LSTM (Long Short-Term Memory)**
   - Best for: Long-term dependencies, gradual degradation patterns
   - Input: (batch_size, sequence_length, feature_count)
   - Output: (batch_size, 1) - predicted RUL in hours

2. **TCN (Temporal Convolutional Network)**
   - Best for: Fast inference, parallel processing
   - Input: (batch_size, sequence_length, feature_count)
   - Output: (batch_size, 1) - predicted RUL in hours

3. **GRU (Gated Recurrent Unit)**
   - Best for: Balance between LSTM accuracy and TCN speed
   - Input: (batch_size, sequence_length, feature_count)
   - Output: (batch_size, 1) - predicted RUL in hours

### Model Requirements

- **Format**: ONNX (Open Neural Network Exchange)
- **Input Shape**: (1, 50, 6) - batch_size=1, sequence_length=50, features=6
- **Output Shape**: (1, 1) - single RUL value in hours
- **Quantization**: FP32 (float32) or FP16 for faster inference
- **Opset Version**: 11 or higher

## Training Pipeline

### Overview

The ONNX model should be trained offline using historical sensor data:

```
Historical Data → Feature Engineering → Model Training → 
ONNX Conversion → Validation → Deployment
```

### Step 1: Data Collection

Collect historical sensor data with known degradation outcomes:

```python
# Required fields per sample
sample = {
    'timestamp': 1234567890,
    'device_id': 'ESP32_001',
    'current_mean': [5.2, 5.3, 5.1],
    'vibration_mean': {'x': 2.1, 'y': 2.3, 'z': 1.9},
    'temperature_mean': [48.5, 49.0, 48.8],
    'load_factor': 0.65,
    'rul_actual': 850.5  # Actual remaining hours (label)
}
```

### Step 2: Feature Engineering

Extract 6 features per time step:

1. **Current (A)**: Mean motor current
2. **Vibration X (m/s²)**: X-axis vibration magnitude
3. **Vibration Y (m/s²)**: Y-axis vibration magnitude
4. **Vibration Z (m/s²)**: Z-axis vibration magnitude
5. **Temperature (°C)**: Mean operating temperature
6. **Load Factor**: Normalized load (0.0-1.0)

Calculate normalization parameters:

```python
import numpy as np

features = np.array([...])  # Shape: (n_samples, 6)
feature_mean = np.mean(features, axis=0)
feature_std = np.std(features, axis=0)

# Save for deployment
metadata = {
    'feature_mean': feature_mean.tolist(),
    'feature_std': feature_std.tolist()
}
```

### Step 3: Model Training (PyTorch Example)

```python
import torch
import torch.nn as nn

class LSTMRULPredictor(nn.Module):
    def __init__(self, input_size=6, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        # Take last time step
        last_output = lstm_out[:, -1, :]
        rul = self.fc(last_output)
        return rul

# Training loop
model = LSTMRULPredictor()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(100):
    for batch in train_loader:
        x, y = batch  # x: (batch, 50, 6), y: (batch, 1)
        
        optimizer.zero_grad()
        predictions = model(x)
        loss = criterion(predictions, y)
        loss.backward()
        optimizer.step()
```

### Step 4: TensorFlow/Keras Example

```python
import tensorflow as tf
from tensorflow import keras

# Build model
model = keras.Sequential([
    keras.layers.LSTM(64, return_sequences=True, input_shape=(50, 6)),
    keras.layers.Dropout(0.2),
    keras.layers.LSTM(64, return_sequences=False),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(1)  # RUL output
])

model.compile(
    optimizer='adam',
    loss='mse',
    metrics=['mae']
)

# Train
model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32
)
```

### Step 5: ONNX Conversion

#### From PyTorch

```python
import torch.onnx

# Prepare dummy input
dummy_input = torch.randn(1, 50, 6)

# Export model
torch.onnx.export(
    model,
    dummy_input,
    "rul_predictor.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
)
```

#### From TensorFlow

```python
import tf2onnx

spec = (tf.TensorSpec((None, 50, 6), tf.float32, name="input"),)
model_proto, _ = tf2onnx.convert.from_keras(
    model,
    input_signature=spec,
    opset=11,
    output_path="rul_predictor.onnx"
)
```

### Step 6: Create Metadata File

Create `rul_predictor.json` alongside the ONNX model:

```json
{
    "model_path": "models/rul_predictor.onnx",
    "model_version": "1.0.0",
    "model_type": "LSTM",
    "input_shape": [1, 50, 6],
    "output_shape": [1, 1],
    "feature_names": [
        "current",
        "vibration_x",
        "vibration_y",
        "vibration_z",
        "temperature",
        "load_factor"
    ],
    "feature_mean": [5.2, 2.1, 2.3, 1.9, 48.5, 0.65],
    "feature_std": [1.5, 0.8, 0.9, 0.7, 8.2, 0.15],
    "training_date": "2025-12-09",
    "performance_metrics": {
        "train_mae": 7.8,
        "test_mae": 9.2,
        "train_rmse": 11.5,
        "test_rmse": 13.8,
        "r2_score": 0.89
    }
}
```

## Deployment

### File Structure

```
MODAX/
├── python-ai-layer/
│   ├── onnx_predictor.py         # ONNX predictor module
│   ├── ai_service.py             # REST API with RUL endpoints
│   └── models/                   # Model directory
│       ├── rul_predictor.onnx    # ONNX model file
│       └── rul_predictor.json    # Model metadata
```

### Installation

1. Install ONNX Runtime:

```bash
cd python-ai-layer
pip install onnxruntime>=1.16.0
```

For GPU acceleration (optional):
```bash
pip install onnxruntime-gpu
```

2. Place model files:

```bash
mkdir -p models
cp your_trained_model.onnx models/rul_predictor.onnx
cp your_metadata.json models/rul_predictor.json
```

3. Set environment variable (optional):

```bash
export ONNX_MODEL_PATH=models/rul_predictor.onnx
```

### Configuration

The predictor automatically loads the model on initialization. Configuration options:

```python
from onnx_predictor import ONNXRULPredictor

predictor = ONNXRULPredictor(
    model_path="models/rul_predictor.onnx",  # Model file path
    sequence_length=50,                       # Time steps in sequence
    feature_count=6                           # Number of features
)
```

## API Usage

### Predict RUL Endpoint

```http
POST /api/v1/predict-rul
Content-Type: application/json

{
    "device_id": "ESP32_001",
    "time_window_start": 1234567890.0,
    "time_window_end": 1234567920.0,
    "current_mean": [5.2, 5.3, 5.1],
    "current_std": [0.3, 0.4, 0.35],
    "current_max": [6.5, 6.8, 6.6],
    "vibration_mean": {"x": 2.1, "y": 2.3, "z": 1.9},
    "vibration_std": {"x": 0.5, "y": 0.6, "z": 0.4},
    "vibration_max": {"x": 4.2, "y": 4.5, "z": 3.8},
    "temperature_mean": [48.5, 49.0, 48.8],
    "temperature_max": [52.0, 53.0, 52.5],
    "sample_count": 100
}
```

Response:

```json
{
    "timestamp": 1234567920000,
    "device_id": "ESP32_001",
    "predicted_rul_hours": 850.5,
    "health_status": "normal",
    "confidence": 0.87,
    "contributing_factors": [
        "Normal operating conditions"
    ],
    "model_version": "1.0.0",
    "recommendations": [
        "Continue normal operations",
        "Monitor for any changes in operating conditions"
    ]
}
```

### Health Status Values

- **critical**: RUL < 10 hours - Immediate action required
- **warning**: RUL < 50 hours - Schedule maintenance soon
- **normal**: RUL ≥ 50 hours - Continue normal operations

### Model Info Endpoint

```http
GET /api/v1/models/info
```

Response includes ONNX model information:

```json
{
    "rul_prediction": {
        "type": "ONNX Deep Learning Model",
        "status": "loaded",
        "description": "Remaining Useful Life prediction using LSTM/TCN time-series model",
        "details": {
            "status": "loaded",
            "model_path": "models/rul_predictor.onnx",
            "model_version": "1.0.0",
            "model_type": "LSTM",
            "sequence_length": 50,
            "feature_count": 6
        }
    }
}
```

### Reset Buffer Endpoint

Clear the time-series buffer after maintenance:

```http
POST /api/v1/reset-rul-buffer/ESP32_001
```

Response:

```json
{
    "status": "success",
    "device_id": "ESP32_001",
    "message": "RUL prediction buffer reset - new sequence will be built"
}
```

## Fallback Behavior

If the ONNX model is not available, the predictor automatically falls back to statistical estimation:

- Uses simple heuristics based on sensor values
- Lower confidence scores (typically 0.6 vs 0.85-0.95)
- Model version: "fallback-v1.0"
- Still provides useful RUL estimates for operation

## Performance Considerations

### Inference Speed

- **ONNX CPU**: ~5-10ms per prediction
- **ONNX GPU**: ~1-3ms per prediction
- **Fallback**: <1ms per prediction

### Memory Usage

- **Model Size**: 1-10 MB (depending on architecture)
- **Buffer Size**: ~50 samples × 6 features × 4 bytes = 1.2 KB per device
- **Total**: Minimal memory footprint

### Sequence Building

The predictor requires 50 consecutive samples before making predictions:
- At 10Hz sensor rate: 5 seconds of data
- At 1Hz aggregation: 50 seconds of data

Use fallback prediction during warmup period.

## Model Versioning

### A/B Testing

Deploy multiple models for comparison:

```python
predictor_v1 = ONNXRULPredictor(model_path="models/rul_v1.onnx")
predictor_v2 = ONNXRULPredictor(model_path="models/rul_v2.onnx")

# Run both and compare
result_v1 = predictor_v1.predict_rul(data, device_id)
result_v2 = predictor_v2.predict_rul(data, device_id)
```

### Model Updates

1. Train new model version
2. Convert to ONNX
3. Validate on test set
4. Deploy to `models/rul_predictor_v2.onnx`
5. Update `ONNX_MODEL_PATH` environment variable
6. Restart AI service (graceful shutdown preserves buffers)

## Monitoring and Validation

### Key Metrics

Track prediction quality:

```python
# Prediction error (when actual RUL known)
mae = mean_absolute_error(actual_rul, predicted_rul)
rmse = root_mean_squared_error(actual_rul, predicted_rul)

# Confidence calibration
calibration_error = abs(predicted_probability - actual_accuracy)

# Health status accuracy
status_accuracy = correct_status_predictions / total_predictions
```

### Alerts

Set up alerts for:
- Model inference errors
- Confidence scores below threshold (< 0.5)
- Prediction outliers (RUL < 0 or > 20000)
- Buffer building delays

## Troubleshooting

### Issue: Model not loading

**Symptoms**: API returns fallback predictions

**Solutions**:
1. Check model file exists at configured path
2. Verify ONNX Runtime is installed: `pip list | grep onnxruntime`
3. Check model format: `python -m onnx.checker model.onnx`
4. Review logs for detailed error messages

### Issue: Low confidence scores

**Symptoms**: Confidence consistently below 0.7

**Causes**:
- Incomplete sensor data (missing fields)
- High sensor variability (noisy data)
- Operating conditions outside training distribution

**Solutions**:
- Improve sensor data quality
- Collect more training data covering edge cases
- Retrain model with better feature engineering

### Issue: Inconsistent predictions

**Symptoms**: RUL jumps significantly between samples

**Causes**:
- Sensor noise or outliers
- Insufficient sequence length
- Model overfitting

**Solutions**:
- Apply sensor data smoothing
- Increase sequence length (e.g., 100 samples)
- Retrain with regularization (dropout, L2)

### Issue: Slow inference

**Symptoms**: API response time > 100ms

**Solutions**:
1. Use ONNX GPU Runtime: `pip install onnxruntime-gpu`
2. Quantize model to FP16: Reduces size and speeds inference
3. Optimize model architecture (fewer layers, smaller hidden size)
4. Use batch inference for multiple devices

## Future Enhancements

### Planned Features

1. **Multi-Model Ensemble**
   - Combine LSTM, TCN, and statistical predictions
   - Weighted voting based on confidence
   - Improved robustness

2. **Online Learning**
   - Incremental model updates with new data
   - Adapt to changing operating conditions
   - Device-specific fine-tuning

3. **Uncertainty Quantification**
   - Bayesian neural networks
   - Monte Carlo dropout
   - Prediction intervals

4. **Anomaly Detection Integration**
   - Combine RUL prediction with anomaly detection
   - Early warning for unexpected degradation
   - Root cause analysis

5. **Multi-Component Prediction**
   - Separate RUL for bearings, motors, spindles
   - Component-level maintenance scheduling
   - Optimize maintenance costs

## References

### ONNX Resources

- [ONNX Official Site](https://onnx.ai/)
- [ONNX Runtime Documentation](https://onnxruntime.ai/)
- [PyTorch to ONNX Tutorial](https://pytorch.org/tutorials/advanced/super_resolution_with_onnxruntime.html)
- [TensorFlow to ONNX Conversion](https://github.com/onnx/tensorflow-onnx)

### Predictive Maintenance Papers

- "Remaining Useful Life Estimation Using LSTM" - IEEE 2020
- "Temporal Convolutional Networks for Prognostics" - PHM Society 2019
- "Deep Learning for Predictive Maintenance: A Survey" - Sensors 2021

### MODAX Documentation

- [AI Layer README](../python-ai-layer/README.md)
- [Architecture Overview](ARCHITECTURE.md)
- [API Documentation](API.md)

## Support

For issues or questions:
1. Check logs: `python-ai-layer/*.log`
2. Review model metadata: `models/rul_predictor.json`
3. Test with fallback mode first
4. Open GitHub issue with:
   - Model details (architecture, size, training data)
   - Error messages and logs
   - Sample input data (anonymized)

---

**Note**: This feature enables advanced predictive maintenance but should be used alongside manufacturer recommendations and safety protocols. RUL predictions are advisory only - not safety-critical decisions.
