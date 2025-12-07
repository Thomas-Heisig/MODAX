"""REST API for Control Layer - Interface for HMI"""
from fastapi import FastAPI, HTTPException, Depends, Security, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import os
import time
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from auth import get_api_key, require_read, require_write, require_control
from security_audit import get_security_audit_logger
from websocket_manager import get_websocket_manager
from data_export import get_data_exporter
from config import config

logger = logging.getLogger(__name__)
audit_logger = get_security_audit_logger()
ws_manager = get_websocket_manager()
data_exporter = get_data_exporter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, enabled=config.control.rate_limit_enabled)

# Prometheus metrics
REQUEST_COUNT = Counter('control_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('control_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
DEVICES_ONLINE = Gauge('control_devices_online', 'Number of devices online')
SYSTEM_SAFE = Gauge('control_system_safe', 'System safety status (1=safe, 0=unsafe)')

app = FastAPI(
    title="MODAX Control Layer API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable configurable CORS
cors_origins = config.control.cors_origins.split(",") if config.control.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=config.control.cors_allow_credentials,
    allow_methods=config.control.cors_allow_methods.split(",") if config.control.cors_allow_methods != "*" else ["*"],
    allow_headers=config.control.cors_allow_headers.split(",") if config.control.cors_allow_headers != "*" else ["*"],
)

# Check if API authentication is enabled
API_AUTH_ENABLED = os.getenv("API_KEY_ENABLED", "false").lower() == "true"

# Global reference to control layer (set by main)
control_layer = None


def set_control_layer(layer):
    """Set reference to control layer instance"""
    global control_layer
    control_layer = layer


# Standardized error response model
class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    message: str
    status_code: int
    timestamp: str
    details: Optional[Dict] = None


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect metrics for all requests"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


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


class SystemStatus(BaseModel):
    """Overall system status"""
    is_safe: bool
    devices_online: List[str]
    ai_enabled: bool
    last_update: float


class DeviceData(BaseModel):
    """Current device data"""
    device_id: str
    timestamp: float
    motor_currents: List[float]
    vibration: Dict[str, float]
    temperatures: List[float]
    safety_status: Optional[Dict[str, bool]]


class AIAnalysisResponse(BaseModel):
    """AI analysis results"""
    device_id: str
    timestamp: float
    anomaly_detected: bool
    anomaly_score: float
    anomaly_description: str
    predicted_wear_level: float
    estimated_remaining_hours: int
    recommendations: List[str]
    confidence: float


class ControlCommandRequest(BaseModel):
    """Control command from HMI"""
    command_type: str
    parameters: Optional[Dict[str, str]] = None


@app.get("/")
def root():
    """API root"""
    return {"message": "MODAX Control Layer API", "version": "1.0.0", "api_prefix": "/api/v1"}


@app.get("/health")
@limiter.limit(config.control.rate_limit_default)
def health_check(request: Request):
    """Health check endpoint - returns 200 if service is running"""
    return {
        "status": "healthy",
        "service": "modax-control-layer",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready")
@limiter.limit(config.control.rate_limit_default)
def readiness_check(request: Request):
    """Readiness check endpoint - returns 200 if service is ready to accept requests"""
    if not control_layer:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "Control layer not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # Update system metrics
    devices = control_layer.aggregator.get_device_ids()
    DEVICES_ONLINE.set(len(devices))
    SYSTEM_SAFE.set(1 if control_layer.aggregator.is_system_safe() else 0)
    
    return {
        "status": "ready",
        "service": "modax-control-layer",
        "mqtt_connected": True,
        "devices_online": len(devices),
        "system_safe": control_layer.aggregator.is_system_safe(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/status", response_model=SystemStatus)
@limiter.limit(config.control.rate_limit_default)
async def get_system_status(
    request: Request,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get overall system status"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    return SystemStatus(
        is_safe=control_layer.aggregator.is_system_safe(),
        devices_online=control_layer.aggregator.get_device_ids(),
        ai_enabled=control_layer.config.control.ai_layer_enabled,
        last_update=control_layer.get_last_update_time()
    )


@app.get("/api/v1/devices", response_model=List[str])
@limiter.limit(config.control.rate_limit_default)
async def get_devices(
    request: Request,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get list of connected devices"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    return control_layer.aggregator.get_device_ids()


@app.get("/api/v1/devices/{device_id}/data", response_model=DeviceData)
@limiter.limit(config.control.rate_limit_default)
async def get_device_data(
    request: Request,
    device_id: str,
    count: int = 1,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get latest data from a specific device"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    readings = control_layer.aggregator.get_recent_readings(device_id, count)
    if not readings:
        raise HTTPException(status_code=404, detail=f"No data for device {device_id}")

    latest = readings[-1]
    safety = control_layer.aggregator.get_latest_safety_status(device_id)

    safety_dict = None
    if safety:
        safety_dict = {
            "emergency_stop": safety.emergency_stop,
            "door_closed": safety.door_closed,
            "overload_detected": safety.overload_detected,
            "temperature_ok": safety.temperature_ok
        }

    return DeviceData(
        device_id=latest.device_id,
        timestamp=latest.timestamp,
        motor_currents=latest.motor_currents,
        vibration=latest.vibration,
        temperatures=latest.temperatures,
        safety_status=safety_dict
    )


@app.get("/api/v1/devices/{device_id}/history")
@limiter.limit(config.control.rate_limit_default)
async def get_device_history(
    request: Request,
    device_id: str,
    count: int = 100,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get historical data from a device"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    readings = control_layer.aggregator.get_recent_readings(device_id, count)
    if not readings:
        raise HTTPException(status_code=404, detail=f"No data for device {device_id}")

    return {
        "device_id": device_id,
        "count": len(readings),
        "readings": [
            {
                "timestamp": r.timestamp,
                "motor_currents": r.motor_currents,
                "vibration": r.vibration,
                "temperatures": r.temperatures
            } for r in readings
        ]
    }


@app.get("/api/v1/devices/{device_id}/ai-analysis", response_model=AIAnalysisResponse)
@limiter.limit(config.control.rate_limit_default)
async def get_ai_analysis(
    request: Request,
    device_id: str,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get latest AI analysis for a device"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    analysis = control_layer.get_latest_ai_analysis(device_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"No AI analysis for device {device_id}")

    return AIAnalysisResponse(**analysis)


@app.post("/api/v1/control/command")
@limiter.limit("10/minute")  # Stricter rate limit for control commands
async def send_control_command(
    request: Request,
    command: ControlCommandRequest,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Send control command to system"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    # Safety check - don't allow commands if system is not safe
    if not control_layer.aggregator.is_system_safe():
        audit_logger.log_control_command(
            user="api_key_user",
            device_id="system",
            command=command.command_type,
            status="blocked",
            parameters=command.parameters,
            reason="system_not_safe"
        )
        raise HTTPException(status_code=403, detail="System not in safe state")

    try:
        control_layer.send_control_command(command.command_type, command.parameters or {})
        audit_logger.log_control_command(
            user="api_key_user",
            device_id="system",
            command=command.command_type,
            status="executed",
            parameters=command.parameters
        )
        return {"status": "success", "command": command.command_type}
    except Exception as e:
        logger.error(f"Error sending control command: {e}")
        audit_logger.log_control_command(
            user="api_key_user",
            device_id="system",
            command=command.command_type,
            status="failed",
            parameters=command.parameters,
            reason=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai/status")
@limiter.limit(config.control.rate_limit_default)
async def get_ai_status(
    request: Request,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """Get AI layer status"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")

    return {
        "enabled": control_layer.config.control.ai_layer_enabled,
        "last_analysis": control_layer.get_last_ai_analysis_time(),
        "devices_analyzed": len(control_layer.ai_analysis_results)
    }


# WebSocket endpoints for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates (all devices)"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            data = await websocket.receive_text()
            # Echo back for now (can be extended to handle commands)
            await websocket.send_json({"type": "ping", "message": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


@app.websocket("/ws/device/{device_id}")
async def websocket_device_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for device-specific real-time updates"""
    await ws_manager.connect(websocket, device_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ping", "message": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected from device {device_id}")


# Data export endpoints
@app.get("/api/v1/export/{device_id}/csv")
@limiter.limit("10/minute")  # Lower rate limit for export operations
async def export_device_data_csv(
    request: Request,
    device_id: str,
    hours: int = 24,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """
    Export device sensor data as CSV
    
    Args:
        device_id: Device identifier
        hours: Number of hours of data to export (default: 24)
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        csv_content = data_exporter.export_to_csv(
            device_id, start_time, end_time
        )
        
        if not csv_content:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for device {device_id}"
            )
        
        filename = f"modax_{device_id}_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting CSV data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/export/{device_id}/json")
@limiter.limit("10/minute")  # Lower rate limit for export operations
async def export_device_data_json(
    request: Request,
    device_id: str,
    hours: int = 24,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """
    Export device sensor data as JSON
    
    Args:
        device_id: Device identifier
        hours: Number of hours of data to export (default: 24)
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        json_content = data_exporter.export_to_json(
            device_id, start_time, end_time
        )
        
        if json_content == "[]":
            raise HTTPException(
                status_code=404,
                detail=f"No data available for device {device_id}"
            )
        
        filename = f"modax_{device_id}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting JSON data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/export/{device_id}/statistics")
@limiter.limit("10/minute")  # Lower rate limit for export operations
async def export_device_statistics(
    request: Request,
    device_id: str,
    hours: int = 24,
    api_key: str = Depends(get_api_key) if API_AUTH_ENABLED else None
):
    """
    Export device hourly statistics as JSON
    
    Args:
        device_id: Device identifier
        hours: Number of hours of statistics to export (default: 24)
    """
    try:
        json_content = data_exporter.export_statistics_to_json(device_id, hours)
        
        if json_content == "[]":
            raise HTTPException(
                status_code=404,
                detail=f"No statistics available for device {device_id}"
            )
        
        filename = f"modax_{device_id}_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
