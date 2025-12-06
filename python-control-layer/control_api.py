"""REST API for Control Layer - Interface for HMI"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="MODAX Control Layer API", version="1.0.0")

# Enable CORS for HMI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global reference to control layer (set by main)
control_layer = None

def set_control_layer(layer):
    """Set reference to control layer instance"""
    global control_layer
    control_layer = layer

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
    return {"message": "MODAX Control Layer API", "version": "1.0.0"}

@app.get("/status", response_model=SystemStatus)
def get_system_status():
    """Get overall system status"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")
    
    return SystemStatus(
        is_safe=control_layer.aggregator.is_system_safe(),
        devices_online=control_layer.aggregator.get_device_ids(),
        ai_enabled=control_layer.config.control.ai_layer_enabled,
        last_update=control_layer.get_last_update_time()
    )

@app.get("/devices", response_model=List[str])
def get_devices():
    """Get list of connected devices"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")
    
    return control_layer.aggregator.get_device_ids()

@app.get("/devices/{device_id}/data", response_model=DeviceData)
def get_device_data(device_id: str, count: int = 1):
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

@app.get("/devices/{device_id}/history")
def get_device_history(device_id: str, count: int = 100):
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

@app.get("/devices/{device_id}/ai-analysis", response_model=AIAnalysisResponse)
def get_ai_analysis(device_id: str):
    """Get latest AI analysis for a device"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")
    
    analysis = control_layer.get_latest_ai_analysis(device_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"No AI analysis for device {device_id}")
    
    return AIAnalysisResponse(**analysis)

@app.post("/control/command")
def send_control_command(command: ControlCommandRequest):
    """Send control command to system"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")
    
    # Safety check - don't allow commands if system is not safe
    if not control_layer.aggregator.is_system_safe():
        raise HTTPException(status_code=403, detail="System not in safe state")
    
    try:
        control_layer.send_control_command(command.command_type, command.parameters or {})
        return {"status": "success", "command": command.command_type}
    except Exception as e:
        logger.error(f"Error sending control command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/status")
def get_ai_status():
    """Get AI layer status"""
    if not control_layer:
        raise HTTPException(status_code=503, detail="Control layer not initialized")
    
    return {
        "enabled": control_layer.config.control.ai_layer_enabled,
        "last_analysis": control_layer.get_last_ai_analysis_time(),
        "devices_analyzed": len(control_layer.ai_analysis_results)
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    if not control_layer:
        return {"status": "initializing"}
    
    return {
        "status": "healthy",
        "mqtt_connected": True,  # Could add actual check
        "devices_online": len(control_layer.aggregator.get_device_ids()),
        "system_safe": control_layer.aggregator.is_system_safe()
    }
