"""AI Service - Main AI analysis service with REST API"""
import logging
import time
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from anomaly_detector import StatisticalAnomalyDetector
from wear_predictor import SimpleWearPredictor
from optimizer import OptimizationRecommender

logger = logging.getLogger(__name__)

# Initialize rate limiter
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)

# Prometheus metrics
ANALYSIS_COUNT = Counter('ai_analysis_requests_total', 'Total analysis requests', ['status'])
ANALYSIS_DURATION = Histogram('ai_analysis_duration_seconds', 'Analysis request duration')
ANOMALY_DETECTED = Counter('ai_anomalies_detected_total', 'Total anomalies detected', ['type'])

app = FastAPI(
    title="MODAX AI Layer",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "*")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "*")

cors_origins = CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS.split(",") if CORS_ALLOW_METHODS != "*" else ["*"],
    allow_headers=CORS_ALLOW_HEADERS.split(",") if CORS_ALLOW_HEADERS != "*" else ["*"],
)

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


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    message: str
    status_code: int
    timestamp: str
    details: Optional[Dict] = None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for standardized error responses"""
    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=str(exc),
        status_code=500,
        timestamp=datetime.utcnow().isoformat(),
        details={"path": request.url.path, "method": request.method}
    )
    logger.error("Unhandled exception", extra={
        "error": error_response.error,
        "message": error_response.message,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized format"""
    error_response = ErrorResponse(
        error="HTTPException",
        message=exc.detail,
        status_code=exc.status_code,
        timestamp=datetime.utcnow().isoformat(),
        details={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@app.get("/")
def root() -> Dict[str, any]:
    """API root"""
    return {
        "service": "MODAX AI Layer",
        "version": "1.0.0",
        "status": "operational",
        "api_prefix": "/api/v1",
        "models": {
            "anomaly_detection": "Statistical (Z-score based)",
            "wear_prediction": "Empirical stress accumulation",
            "optimization": "Rule-based recommendations"
        }
    }


@app.get("/health")
@limiter.limit(RATE_LIMIT_DEFAULT)
def health_check(request: Request) -> Dict[str, str]:
    """Health check endpoint - returns 200 if service is running"""
    return {
        "status": "healthy",
        "service": "modax-ai-layer",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready")
@limiter.limit(RATE_LIMIT_DEFAULT)
def readiness_check(request: Request):
    """Readiness check endpoint - returns 200 if service is ready to accept requests"""
    return {
        "status": "ready",
        "service": "modax-ai-layer",
        "models_loaded": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/analyze", response_model=AIAnalysisResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def analyze_sensor_data(request: Request, data: SensorDataInput):
    """
    Analyze sensor data and provide AI-based insights

    This endpoint performs:
    1. Anomaly detection on current, vibration, and temperature
    2. Wear prediction based on operating conditions
    3. Optimization recommendations

    Note: All analysis is for advisory purposes only.
    Safety-critical decisions remain in the control layer.
    """
    start_time = time.time()
    try:
        logger.info("Analyzing data", extra={"device_id": data.device_id})

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
            ANOMALY_DETECTED.labels(type="current").inc()

        if vibration_anomaly.is_anomaly:
            anomalies.append(vibration_anomaly.description)
            max_anomaly_score = max(max_anomaly_score, vibration_anomaly.score)
            min_confidence = min(min_confidence, vibration_anomaly.confidence)
            ANOMALY_DETECTED.labels(type="vibration").inc()

        if temperature_anomaly.is_anomaly:
            anomalies.append(temperature_anomaly.description)
            max_anomaly_score = max(max_anomaly_score, temperature_anomaly.score)
            min_confidence = min(min_confidence, temperature_anomaly.confidence)
            ANOMALY_DETECTED.labels(type="temperature").inc()

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

        # Record metrics
        duration = time.time() - start_time
        ANALYSIS_DURATION.observe(duration)
        ANALYSIS_COUNT.labels(status="success").inc()

        logger.info("Analysis complete", extra={
            "device_id": data.device_id,
            "anomaly_detected": anomaly_detected,
            "wear_level": wear_prediction.wear_level,
            "duration_seconds": duration
        })

        return response

    except Exception as e:
        ANALYSIS_COUNT.labels(status="error").inc()
        logger.error("Error analyzing sensor data", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/v1/reset-wear/{device_id}")
@limiter.limit("10/minute")  # Stricter rate limit for maintenance operations
def reset_device_wear(request: Request, device_id: str):
    """
    Reset wear counter for a device (e.g., after maintenance)
    """
    try:
        wear_predictor.reset_wear(device_id)
        logger.info("Wear counter reset", extra={"device_id": device_id})
        return {"status": "success", "device_id": device_id, "message": "Wear counter reset"}
    except Exception as e:
        logger.error("Error resetting wear", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/models/info")
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_model_info(request: Request):
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
