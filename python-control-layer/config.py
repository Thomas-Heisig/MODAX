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

    # TLS/SSL configuration
    use_tls: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    ca_certs: Optional[str] = os.getenv("MQTT_CA_CERTS")  # Path to CA certificate
    certfile: Optional[str] = os.getenv("MQTT_CERTFILE")  # Path to client certificate
    keyfile: Optional[str] = os.getenv("MQTT_KEYFILE")  # Path to client key
    tls_insecure: bool = os.getenv("MQTT_TLS_INSECURE",
                                   "false").lower() == "true"  # Skip cert verification (dev only)

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

    # API Authentication
    api_key_enabled: bool = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    api_key: Optional[str] = os.getenv("API_KEY")  # API key for authentication

    # Data aggregation settings
    aggregation_window_seconds: int = 10
    max_data_points: int = 1000

    # AI Layer integration
    ai_layer_enabled: bool = os.getenv("AI_ENABLED", "true").lower() == "true"
    ai_layer_url: str = os.getenv("AI_LAYER_URL", "http://localhost:8001/analyze")
    ai_layer_timeout: int = int(os.getenv("AI_LAYER_TIMEOUT", "5"))  # seconds
    ai_analysis_interval_seconds: int = 60


@dataclass
class Config:
    """Master configuration"""
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    control: ControlConfig = field(default_factory=ControlConfig)


# Global config instance
config = Config()
