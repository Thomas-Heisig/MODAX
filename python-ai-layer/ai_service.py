"""AI Service - Main AI analysis service with REST API"""
import logging
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from anomaly_detector import StatisticalAnomalyDetector
from wear_predictor import SimpleWearPredictor
from optimizer import OptimizationRecommender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MODAX AI Layer", version="1.0.0")

# Initialize AI components
anomaly_detector = StatisticalAnomalyDetector(z_threshold=3.0)
wear_predictor = SimpleWearPredictor()
optimizer = OptimizationRecommender()

class SensorDataInput(BaseModel):
    """Input sensor data for analysis"""
    device_id: str
    time_window_start: float
    time_window_end: float
    current_mean: List[float]
    current_std: List[float]
    current_max: List[float]
    vibration_mean: Dict[str, float]
    vibration_std: Dict[str, float]
    vibration_max: Dict[str, float]
    temperature_mean: List[float]
    temperature_max: List[float]
    sample_count: int

class AIAnalysisResponse(BaseModel):
    """AI analysis results"""
    timestamp: int
    device_id: str
    anomaly_detected: bool
    anomaly_score: float
    anomaly_description: str
    predicted_wear_level: float
    estimated_remaining_hours: int
    recommendations: List[str]
    confidence: float
    analysis_details: Optional[Dict] = None

@app.get("/")
def root():
    """API root"""
    return {
        "service": "MODAX AI Layer",
        "version": "1.0.0",
        "status": "operational",
        "models": {
            "anomaly_detection": "Statistical (Z-score based)",
            "wear_prediction": "Empirical stress accumulation",
            "optimization": "Rule-based recommendations"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "models_loaded": True
    }

@app.post("/analyze", response_model=AIAnalysisResponse)
def analyze_sensor_data(data: SensorDataInput):
    """
    Analyze sensor data and provide AI-based insights
    
    This endpoint performs:
    1. Anomaly detection on current, vibration, and temperature
    2. Wear prediction based on operating conditions
    3. Optimization recommendations
    
    Note: All analysis is for advisory purposes only.
    Safety-critical decisions remain in the control layer.
    """
    try:
        logger.info(f"Analyzing data for device {data.device_id}")
        
        # Convert to dict for processing
        sensor_data = data.dict()
        
        # 1. Anomaly Detection
        current_anomaly = anomaly_detector.detect_current_anomaly(
            data.current_mean, data.current_max, data.device_id
        )
        
        vibration_anomaly = anomaly_detector.detect_vibration_anomaly(
            data.vibration_mean, data.vibration_max, data.device_id
        )
        
        temperature_anomaly = anomaly_detector.detect_temperature_anomaly(
            data.temperature_mean, data.temperature_max, data.device_id
        )
        
        # Combine anomaly results
        anomalies = []
        max_anomaly_score = 0.0
        min_confidence = 1.0
        
        if current_anomaly.is_anomaly:
            anomalies.append(current_anomaly.description)
            max_anomaly_score = max(max_anomaly_score, current_anomaly.score)
            min_confidence = min(min_confidence, current_anomaly.confidence)
        
        if vibration_anomaly.is_anomaly:
            anomalies.append(vibration_anomaly.description)
            max_anomaly_score = max(max_anomaly_score, vibration_anomaly.score)
            min_confidence = min(min_confidence, vibration_anomaly.confidence)
        
        if temperature_anomaly.is_anomaly:
            anomalies.append(temperature_anomaly.description)
            max_anomaly_score = max(max_anomaly_score, temperature_anomaly.score)
            min_confidence = min(min_confidence, temperature_anomaly.confidence)
        
        anomaly_detected = len(anomalies) > 0
        anomaly_description = "; ".join(anomalies) if anomalies else "No anomalies detected"
        
        # 2. Wear Prediction
        wear_prediction = wear_predictor.predict_wear(sensor_data, data.device_id)
        
        # Update confidence based on wear prediction
        overall_confidence = (min_confidence + wear_prediction.confidence) / 2.0
        
        # 3. Generate Recommendations
        recommendations = optimizer.generate_recommendations(
            sensor_data, max_anomaly_score, wear_prediction.wear_level
        )
        
        # Add wear-specific factors to recommendations if significant
        if wear_prediction.contributing_factors:
            for factor in wear_prediction.contributing_factors[:3]:  # Top 3 factors
                if "High" in factor or "Elevated" in factor:
                    # Already included in recommendations
                    pass
        
        # Update baseline statistics for future comparisons
        anomaly_detector.update_baseline(data.device_id, sensor_data)
        
        # Prepare response
        response = AIAnalysisResponse(
            timestamp=int(time.time() * 1000),
            device_id=data.device_id,
            anomaly_detected=anomaly_detected,
            anomaly_score=max_anomaly_score,
            anomaly_description=anomaly_description,
            predicted_wear_level=wear_prediction.wear_level,
            estimated_remaining_hours=wear_prediction.estimated_remaining_hours,
            recommendations=recommendations,
            confidence=overall_confidence,
            analysis_details={
                "current_anomaly": current_anomaly.score,
                "vibration_anomaly": vibration_anomaly.score,
                "temperature_anomaly": temperature_anomaly.score,
                "wear_factors": wear_prediction.contributing_factors,
                "samples_analyzed": data.sample_count,
                "time_window_seconds": data.time_window_end - data.time_window_start
            }
        )
        
        logger.info(f"Analysis complete for {data.device_id}: "
                   f"anomaly={anomaly_detected}, wear={wear_prediction.wear_level:.2%}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing sensor data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/reset-wear/{device_id}")
def reset_device_wear(device_id: str):
    """
    Reset wear counter for a device (e.g., after maintenance)
    """
    try:
        wear_predictor.reset_wear(device_id)
        logger.info(f"Wear counter reset for device {device_id}")
        return {"status": "success", "device_id": device_id, "message": "Wear counter reset"}
    except Exception as e:
        logger.error(f"Error resetting wear: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/info")
def get_model_info():
    """Get information about loaded models"""
    return {
        "anomaly_detection": {
            "type": "Statistical Z-score",
            "threshold": anomaly_detector.z_threshold,
            "description": "Detects anomalies using statistical methods and domain knowledge"
        },
        "wear_prediction": {
            "type": "Empirical stress accumulation",
            "baseline_lifetime_hours": wear_predictor.nominal_lifetime,
            "description": "Predicts wear based on operating conditions and accumulated stress"
        },
        "optimization": {
            "type": "Rule-based expert system",
            "description": "Provides recommendations based on analysis results and best practices"
        },
        "future_enhancements": [
            "ONNX runtime for ML models",
            "Time-series forecasting",
            "Predictive maintenance scheduling",
            "Anomaly classification with neural networks"
        ]
    }
