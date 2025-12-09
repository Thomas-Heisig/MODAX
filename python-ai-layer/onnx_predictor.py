"""
ONNX Model Predictor for Remaining Useful Life (RUL) Prediction

This module provides ONNX-based deep learning models for predictive maintenance,
specifically for Remaining Useful Life (RUL) prediction of industrial machinery.

Supports:
- LSTM-based time series prediction
- TCN (Temporal Convolutional Network) models
- Real-time inference using ONNX Runtime
- Model versioning and A/B testing

The models are trained offline on historical sensor data and converted to ONNX
format for efficient inference.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("ONNX Runtime not available. Install with: pip install onnxruntime")

logger = logging.getLogger(__name__)

# Model configuration constants
DEFAULT_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "models/rul_predictor.onnx")
DEFAULT_SEQUENCE_LENGTH = 50  # Number of time steps in input sequence
DEFAULT_FEATURE_COUNT = 6  # current, vibration_x, vibration_y, vibration_z, temperature, load
MODEL_INPUT_NAME = "input"
MODEL_OUTPUT_NAME = "output"

# RUL thresholds
RUL_CRITICAL_THRESHOLD = 10  # hours
RUL_WARNING_THRESHOLD = 50  # hours
RUL_NORMAL_THRESHOLD = 200  # hours

# Confidence calculation parameters
CONFIDENCE_BASE = 0.9
CONFIDENCE_PREDICTION_STD_PENALTY = 0.1
CONFIDENCE_DATA_QUALITY_FACTOR = 0.05


@dataclass
class RULPrediction:
    """Remaining Useful Life prediction result"""
    predicted_rul_hours: float
    confidence: float
    health_status: str  # "critical", "warning", "normal"
    contributing_factors: List[str]
    model_version: str
    raw_prediction: float
    uncertainty: Optional[float] = None


@dataclass
class ModelMetadata:
    """ONNX model metadata"""
    model_path: str
    model_version: str
    model_type: str  # "LSTM", "TCN", "GRU"
    input_shape: Tuple[int, ...]
    output_shape: Tuple[int, ...]
    feature_names: List[str]
    training_date: str
    performance_metrics: Dict[str, float]


class ONNXRULPredictor:
    """
    ONNX-based Remaining Useful Life Predictor
    
    Uses pre-trained deep learning models (LSTM/TCN) converted to ONNX format
    for efficient real-time RUL prediction on time-series sensor data.
    """
    
    def __init__(self, model_path: str = DEFAULT_MODEL_PATH,
                 sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
                 feature_count: int = DEFAULT_FEATURE_COUNT):
        """
        Initialize ONNX RUL predictor
        
        Args:
            model_path: Path to ONNX model file
            sequence_length: Number of time steps in input sequence
            feature_count: Number of features per time step
        """
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.feature_count = feature_count
        self.session = None
        self.metadata = None
        self.is_loaded = False
        
        # Data buffer for sequence building
        self.data_buffer: Dict[str, List[np.ndarray]] = {}
        
        # Feature normalization parameters (loaded from model metadata)
        self.feature_mean = None
        self.feature_std = None
        
        # Try to load model
        if ONNX_AVAILABLE:
            self._load_model()
        else:
            logger.warning("ONNX Runtime not available - predictor will use fallback mode")
    
    def _load_model(self):
        """Load ONNX model and metadata"""
        try:
            model_path_obj = Path(self.model_path)
            
            if not model_path_obj.exists():
                logger.warning(f"ONNX model not found at {self.model_path}")
                logger.info("To use ONNX prediction, place trained model at the specified path")
                logger.info("Falling back to statistical prediction")
                return
            
            # Load ONNX model
            logger.info(f"Loading ONNX model from {self.model_path}")
            self.session = ort.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']  # Use CPU for portability
            )
            
            # Load metadata if available
            metadata_path = model_path_obj.with_suffix('.json')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata_dict = json.load(f)
                    self.metadata = ModelMetadata(**metadata_dict)
                    logger.info(f"Loaded model metadata: {self.metadata.model_type} "
                               f"v{self.metadata.model_version}")
                    
                    # Load normalization parameters
                    if 'feature_mean' in metadata_dict:
                        self.feature_mean = np.array(metadata_dict['feature_mean'])
                        self.feature_std = np.array(metadata_dict['feature_std'])
                        logger.info("Loaded feature normalization parameters")
            
            self.is_loaded = True
            logger.info("ONNX model loaded successfully")
            
            # Log model input/output info
            input_info = self.session.get_inputs()[0]
            output_info = self.session.get_outputs()[0]
            logger.info(f"Model input: {input_info.name}, shape: {input_info.shape}")
            logger.info(f"Model output: {output_info.name}, shape: {output_info.shape}")
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}", exc_info=True)
            self.is_loaded = False
    
    def _prepare_features(self, sensor_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract and prepare features from sensor data
        
        Args:
            sensor_data: Dictionary containing sensor measurements
            
        Returns:
            Feature array of shape (feature_count,)
        """
        # Extract features in expected order
        features = [
            np.mean(sensor_data.get('current_mean', [0.0])),
            sensor_data.get('vibration_mean', {}).get('x', 0.0),
            sensor_data.get('vibration_mean', {}).get('y', 0.0),
            sensor_data.get('vibration_mean', {}).get('z', 0.0),
            np.mean(sensor_data.get('temperature_mean', [0.0])),
            sensor_data.get('load_factor', 0.5)  # Default load factor
        ]
        
        return np.array(features, dtype=np.float32)
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features using loaded parameters
        
        Args:
            features: Raw feature array
            
        Returns:
            Normalized feature array
        """
        if self.feature_mean is not None and self.feature_std is not None:
            return (features - self.feature_mean) / (self.feature_std + 1e-8)
        return features
    
    def _build_sequence(self, device_id: str, features: np.ndarray) -> Optional[np.ndarray]:
        """
        Build time-series sequence from buffered data
        
        Args:
            device_id: Device identifier
            features: Current feature vector
            
        Returns:
            Sequence array of shape (1, sequence_length, feature_count) or None if insufficient data
        """
        # Initialize buffer for device if needed
        if device_id not in self.data_buffer:
            self.data_buffer[device_id] = []
        
        # Add current features to buffer
        self.data_buffer[device_id].append(features)
        
        # Maintain buffer size
        max_buffer_size = self.sequence_length * 2
        if len(self.data_buffer[device_id]) > max_buffer_size:
            self.data_buffer[device_id] = self.data_buffer[device_id][-max_buffer_size:]
        
        # Check if we have enough data
        if len(self.data_buffer[device_id]) < self.sequence_length:
            logger.debug(f"Insufficient data for device {device_id}: "
                        f"{len(self.data_buffer[device_id])}/{self.sequence_length}")
            return None
        
        # Build sequence from most recent data
        sequence = np.array(self.data_buffer[device_id][-self.sequence_length:])
        
        # Reshape to (batch_size=1, sequence_length, feature_count)
        return sequence.reshape(1, self.sequence_length, self.feature_count)
    
    def predict_rul(self, sensor_data: Dict[str, Any], device_id: str) -> RULPrediction:
        """
        Predict Remaining Useful Life using ONNX model
        
        Args:
            sensor_data: Current sensor measurements
            device_id: Device identifier
            
        Returns:
            RULPrediction with estimated RUL and metadata
        """
        # Prepare features
        features = self._prepare_features(sensor_data)
        
        # If model not loaded, use fallback statistical prediction
        if not self.is_loaded or self.session is None:
            return self._fallback_prediction(sensor_data, device_id)
        
        try:
            # Normalize features
            normalized_features = self._normalize_features(features)
            
            # Build sequence
            sequence = self._build_sequence(device_id, normalized_features)
            
            if sequence is None:
                # Not enough data yet, use fallback
                logger.debug(f"Using fallback prediction for {device_id} - insufficient data")
                return self._fallback_prediction(sensor_data, device_id)
            
            # Run inference
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name
            
            onnx_input = {input_name: sequence.astype(np.float32)}
            onnx_output = self.session.run([output_name], onnx_input)
            
            # Extract prediction
            raw_prediction = float(onnx_output[0][0])
            
            # Post-process prediction
            predicted_rul = max(0.0, raw_prediction)  # Ensure non-negative
            
            # Calculate confidence based on data quality and model uncertainty
            confidence = self._calculate_confidence(sensor_data, predicted_rul)
            
            # Determine health status
            if predicted_rul < RUL_CRITICAL_THRESHOLD:
                health_status = "critical"
            elif predicted_rul < RUL_WARNING_THRESHOLD:
                health_status = "warning"
            else:
                health_status = "normal"
            
            # Identify contributing factors
            contributing_factors = self._identify_contributing_factors(
                sensor_data, predicted_rul
            )
            
            model_version = self.metadata.model_version if self.metadata else "unknown"
            
            logger.info(f"RUL prediction for {device_id}: {predicted_rul:.1f}h "
                       f"(confidence: {confidence:.2f}, status: {health_status})")
            
            return RULPrediction(
                predicted_rul_hours=predicted_rul,
                confidence=confidence,
                health_status=health_status,
                contributing_factors=contributing_factors,
                model_version=model_version,
                raw_prediction=raw_prediction
            )
            
        except Exception as e:
            logger.error(f"Error during ONNX inference: {e}", exc_info=True)
            return self._fallback_prediction(sensor_data, device_id)
    
    def _fallback_prediction(self, sensor_data: Dict[str, Any], 
                            device_id: str) -> RULPrediction:
        """
        Fallback statistical RUL prediction when ONNX model is not available
        
        Uses simple heuristics based on sensor values to estimate RUL.
        This is less accurate than the trained model but provides a baseline.
        """
        # Calculate wear factors from sensor data
        current_mean = np.mean(sensor_data.get('current_mean', [0.0]))
        vibration_mean = sensor_data.get('vibration_mean', {})
        vibration_magnitude = np.sqrt(
            vibration_mean.get('x', 0.0)**2 + 
            vibration_mean.get('y', 0.0)**2 + 
            vibration_mean.get('z', 0.0)**2
        )
        temperature_mean = np.mean(sensor_data.get('temperature_mean', [0.0]))
        
        # Simple linear wear model
        wear_factor = 0.0
        
        # Current contribution (5A normal, wear increases above)
        if current_mean > 5.0:
            wear_factor += (current_mean - 5.0) * 0.02
        
        # Vibration contribution (3 m/s² normal)
        if vibration_magnitude > 3.0:
            wear_factor += (vibration_magnitude - 3.0) * 0.03
        
        # Temperature contribution (50°C normal)
        if temperature_mean > 50.0:
            wear_factor += (temperature_mean - 50.0) * 0.01
        
        # Estimate RUL (10000 hours nominal lifetime)
        nominal_rul = 10000.0
        predicted_rul = nominal_rul * (1.0 - min(wear_factor, 0.95))
        
        # Confidence is lower for statistical prediction
        confidence = 0.6
        
        # Determine health status
        if predicted_rul < RUL_CRITICAL_THRESHOLD:
            health_status = "critical"
        elif predicted_rul < RUL_WARNING_THRESHOLD:
            health_status = "warning"
        else:
            health_status = "normal"
        
        contributing_factors = ["Statistical estimation (ONNX model not available)"]
        
        logger.debug(f"Fallback RUL prediction for {device_id}: {predicted_rul:.1f}h")
        
        return RULPrediction(
            predicted_rul_hours=predicted_rul,
            confidence=confidence,
            health_status=health_status,
            contributing_factors=contributing_factors,
            model_version="fallback-v1.0",
            raw_prediction=predicted_rul
        )
    
    def _calculate_confidence(self, sensor_data: Dict[str, Any], 
                             predicted_rul: float) -> float:
        """
        Calculate confidence score for RUL prediction
        
        Confidence based on:
        - Data quality (completeness, variance)
        - Prediction uncertainty
        - Model performance metrics
        """
        confidence = CONFIDENCE_BASE
        
        # Penalty for incomplete data
        required_fields = ['current_mean', 'vibration_mean', 'temperature_mean']
        missing_fields = sum(1 for field in required_fields 
                           if field not in sensor_data or not sensor_data[field])
        confidence -= missing_fields * CONFIDENCE_DATA_QUALITY_FACTOR
        
        # Penalty for high variability (uncertain conditions)
        current_std = np.mean(sensor_data.get('current_std', [0.0]))
        if current_std > 2.0:
            confidence -= CONFIDENCE_PREDICTION_STD_PENALTY
        
        # Bonus for model performance metrics if available
        if self.metadata and 'test_mae' in self.metadata.performance_metrics:
            mae = self.metadata.performance_metrics['test_mae']
            if mae < 10.0:  # Good model performance
                confidence = min(0.95, confidence + 0.05)
        
        return max(0.1, min(0.95, confidence))
    
    def _identify_contributing_factors(self, sensor_data: Dict[str, Any],
                                      predicted_rul: float) -> List[str]:
        """Identify factors contributing to wear"""
        factors = []
        
        current_mean = np.mean(sensor_data.get('current_mean', [0.0]))
        if current_mean > 7.0:
            factors.append(f"High current load ({current_mean:.1f}A)")
        
        vibration_mean = sensor_data.get('vibration_mean', {})
        vibration_magnitude = np.sqrt(
            vibration_mean.get('x', 0.0)**2 + 
            vibration_mean.get('y', 0.0)**2 + 
            vibration_mean.get('z', 0.0)**2
        )
        if vibration_magnitude > 5.0:
            factors.append(f"Excessive vibration ({vibration_magnitude:.2f} m/s²)")
        
        temperature_mean = np.mean(sensor_data.get('temperature_mean', [0.0]))
        if temperature_mean > 70.0:
            factors.append(f"High temperature ({temperature_mean:.1f}°C)")
        
        if not factors:
            factors.append("Normal operating conditions")
        
        return factors
    
    def reset_buffer(self, device_id: str):
        """Reset data buffer for a specific device"""
        if device_id in self.data_buffer:
            del self.data_buffer[device_id]
            logger.info(f"Reset data buffer for device {device_id}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model"""
        if not self.is_loaded:
            return {
                "status": "not_loaded",
                "message": "ONNX model not available"
            }
        
        info = {
            "status": "loaded",
            "model_path": self.model_path,
            "sequence_length": self.sequence_length,
            "feature_count": self.feature_count,
            "providers": self.session.get_providers() if self.session else []
        }
        
        if self.metadata:
            info.update({
                "model_version": self.metadata.model_version,
                "model_type": self.metadata.model_type,
                "training_date": self.metadata.training_date,
                "performance_metrics": self.metadata.performance_metrics
            })
        
        return info


# Global predictor instance (initialized on module load)
_global_predictor: Optional[ONNXRULPredictor] = None


def get_rul_predictor() -> ONNXRULPredictor:
    """Get or create global RUL predictor instance"""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = ONNXRULPredictor()
    return _global_predictor
