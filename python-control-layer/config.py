"""Configuration for Control Layer"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MQTTConfig:
    """MQTT Broker configuration"""
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    username: Optional[str] = os.getenv("MQTT_USERNAME")
    password: Optional[str] = os.getenv("MQTT_PASSWORD")
    
    # Topics
    topic_sensor_data: str = "modax/sensor/data"
    topic_safety: str = "modax/sensor/safety"
    topic_ai_analysis: str = "modax/ai/analysis"
    topic_control_commands: str = "modax/control/commands"

@dataclass
class ControlConfig:
    """Control Layer configuration"""
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Data aggregation settings
    aggregation_window_seconds: int = 10
    max_data_points: int = 1000
    
    # AI Layer integration
    ai_layer_enabled: bool = os.getenv("AI_ENABLED", "true").lower() == "true"
    ai_analysis_interval_seconds: int = 60

@dataclass
class Config:
    """Master configuration"""
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    control: ControlConfig = field(default_factory=ControlConfig)

# Global config instance
config = Config()
