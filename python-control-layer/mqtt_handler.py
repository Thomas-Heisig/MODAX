"""MQTT Handler - Manages communication with field layer and AI layer"""
import json
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from config import MQTTConfig
from data_aggregator import SensorReading, SafetyStatus

logger = logging.getLogger(__name__)

# MQTT reconnection constants
MQTT_RECONNECT_DELAY_MIN = 1  # Minimum reconnection delay in seconds
MQTT_RECONNECT_DELAY_MAX = 60  # Maximum reconnection delay in seconds
MQTT_RECONNECT_BACKOFF_MULTIPLIER = 2  # Exponential backoff multiplier


class MQTTHandler:
    """Handles MQTT communication for the control layer"""

    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = mqtt.Client()

        # Callbacks
        self.on_sensor_data: Optional[Callable[[SensorReading], None]] = None
        self.on_safety_status: Optional[Callable[[SafetyStatus], None]] = None
        self.on_ai_analysis: Optional[Callable[[dict], None]] = None

        # Reconnection state
        self._reconnect_delay = MQTT_RECONNECT_DELAY_MIN
        self._is_connected = False

        # Setup client
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Enable automatic reconnection using paho-mqtt's built-in mechanism
        # This sets the client's internal reconnection parameters and works
        # in conjunction with our manual exponential backoff tracking below
        self.client.reconnect_delay_set(
            min_delay=MQTT_RECONNECT_DELAY_MIN,
            max_delay=MQTT_RECONNECT_DELAY_MAX
        )

        if config.username and config.password:
            self.client.username_pw_set(config.username, config.password)

    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(
                f"Connecting to MQTT broker at {
                    self.config.broker_host}:{
                    self.config.broker_port}")
            self.client.connect(self.config.broker_host, self.config.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_ai_analysis(self, analysis: dict):
        """Publish AI analysis results to HMI"""
        try:
            payload = json.dumps(analysis)
            self.client.publish(self.config.topic_ai_analysis, payload, qos=1)
            logger.debug(f"Published AI analysis: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish AI analysis: {e}")

    def publish_control_command(self, command: dict):
        """Publish control command"""
        try:
            payload = json.dumps(command)
            self.client.publish(self.config.topic_control_commands, payload, qos=1)
            logger.info(f"Published control command: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish control command: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self._is_connected = True
            self._reconnect_delay = MQTT_RECONNECT_DELAY_MIN  # Reset delay on successful connection

            # Subscribe to topics
            client.subscribe(self.config.topic_sensor_data)
            client.subscribe(self.config.topic_safety)
            client.subscribe(self.config.topic_ai_analysis)

            logger.info(f"Subscribed to topics: {self.config.topic_sensor_data}, "
                        f"{self.config.topic_safety}, {self.config.topic_ai_analysis}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self._is_connected = False

        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker, return code: {rc}")
            logger.info(
                f"Automatic reconnection will be attempted with "
                f"exponential backoff (delay: {self._reconnect_delay}s)")

            # Update reconnect delay with exponential backoff
            self._reconnect_delay = min(
                self._reconnect_delay * MQTT_RECONNECT_BACKOFF_MULTIPLIER,
                MQTT_RECONNECT_DELAY_MAX
            )
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.debug(f"Received message on topic {topic}: {payload}")

            if topic == self.config.topic_sensor_data:
                self._handle_sensor_data(payload)
            elif topic == self.config.topic_safety:
                self._handle_safety_status(payload)
            elif topic == self.config.topic_ai_analysis:
                self._handle_ai_analysis(payload)
            else:
                logger.warning(f"Received message on unknown topic: {topic}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _handle_sensor_data(self, payload: str):
        """Handle incoming sensor data"""
        try:
            reading = SensorReading.from_json(payload)
            if self.on_sensor_data:
                self.on_sensor_data(reading)
        except Exception as e:
            logger.error(f"Error parsing sensor data: {e}")

    def _handle_safety_status(self, payload: str):
        """Handle incoming safety status"""
        try:
            status = SafetyStatus.from_json(payload)

            # Log safety issues immediately
            if not status.is_safe():
                logger.warning(f"SAFETY ALERT from {status.device_id}: "
                               f"Emergency Stop: {status.emergency_stop}, "
                               f"Door Closed: {status.door_closed}, "
                               f"Overload: {status.overload_detected}, "
                               f"Temp OK: {status.temperature_ok}")

            if self.on_safety_status:
                self.on_safety_status(status)
        except Exception as e:
            logger.error(f"Error parsing safety status: {e}")

    def _handle_ai_analysis(self, payload: str):
        """Handle incoming AI analysis (from AI layer or external)"""
        try:
            analysis = json.loads(payload)
            if self.on_ai_analysis:
                self.on_ai_analysis(analysis)
        except Exception as e:
            logger.error(f"Error parsing AI analysis: {e}")
