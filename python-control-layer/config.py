"""Configuration for Control Layer"""
import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


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

    def validate(self) -> List[str]:
        """Validate MQTT configuration"""
        errors = []
        if self.broker_port < 1 or self.broker_port > 65535:
            errors.append(f"Invalid MQTT_BROKER_PORT: {self.broker_port} (must be 1-65535)")
        if self.use_tls and not self.ca_certs:
            errors.append("MQTT_USE_TLS is enabled but MQTT_CA_CERTS is not set")
        return errors


@dataclass
class ControlConfig:
    """Control Layer configuration"""
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # API Authentication
    api_key_enabled: bool = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    api_key: Optional[str] = os.getenv("API_KEY")  # API key for authentication

    # CORS configuration
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    cors_allow_methods: str = os.getenv("CORS_ALLOW_METHODS", "*")
    cors_allow_headers: str = os.getenv("CORS_ALLOW_HEADERS", "*")

    # Rate limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_default: str = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")

    # Data aggregation settings
    aggregation_window_seconds: int = 10
    max_data_points: int = 1000

    # AI Layer integration
    ai_layer_enabled: bool = os.getenv("AI_ENABLED", "true").lower() == "true"
    ai_layer_url: str = os.getenv("AI_LAYER_URL", "http://localhost:8001/api/v1/analyze")
    ai_layer_timeout: int = int(os.getenv("AI_LAYER_TIMEOUT", "5"))  # seconds
    ai_analysis_interval_seconds: int = 60

    def validate(self) -> List[str]:
        """Validate Control configuration"""
        errors = []
        if self.api_port < 1 or self.api_port > 65535:
            errors.append(f"Invalid API_PORT: {self.api_port} (must be 1-65535)")
        if self.api_key_enabled and not self.api_key:
            errors.append("API_KEY_ENABLED is true but API_KEY is not set")
        if self.ai_layer_timeout < 1:
            errors.append(f"Invalid AI_LAYER_TIMEOUT: {self.ai_layer_timeout} (must be >= 1)")
        return errors


@dataclass
class Config:
    """Master configuration"""
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    control: ControlConfig = field(default_factory=ControlConfig)

    def validate(self) -> bool:
        """Validate all configuration and exit if invalid"""
        all_errors = []
        all_errors.extend(self.mqtt.validate())
        all_errors.extend(self.control.validate())

        if all_errors:
            logger.error("Configuration validation failed:")
            for error in all_errors:
                logger.error(f"  - {error}")
            sys.exit(1)

        logger.info("Configuration validation passed")
        return True


# Global config instance
config = Config()
