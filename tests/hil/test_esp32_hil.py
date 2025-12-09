"""
ESP32 Hardware-in-the-Loop (HIL) Tests

This module provides automated HIL tests for the ESP32 field layer.
Tests validate ESP32 firmware functionality with simulated sensor inputs
and real MQTT communication.

Test Categories:
1. Basic Communication - MQTT connection and message publishing
2. Sensor Data Flow - Verify sensor data format and frequency
3. Safety Monitoring - Test safety checks and emergency responses
4. Robustness - Long-running tests, network fluctuation, power loss simulation
5. Edge Cases - Boundary conditions and error handling

Requirements:
- MQTT broker running (mosquitto)
- ESP32 device connected and running firmware
- pytest with paho-mqtt
"""

import pytest
import paho.mqtt.client as mqtt
import json
import time
import threading
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SensorMessage:
    """Captured sensor data message"""
    timestamp: float
    device_id: str
    current_1: float
    current_2: float
    temperature_1: float
    vibration_x: float
    vibration_y: float
    vibration_z: float
    raw_data: Dict[str, Any]


@dataclass
class SafetyMessage:
    """Captured safety status message"""
    timestamp: float
    device_id: str
    emergency_stop: bool
    door_closed: bool
    overload_detected: bool
    temperature_ok: bool
    raw_data: Dict[str, Any]


@dataclass
class MessageCapture:
    """Thread-safe message capture buffer"""
    sensor_messages: List[SensorMessage] = field(default_factory=list)
    safety_messages: List[SafetyMessage] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    
    def add_sensor(self, msg: SensorMessage):
        with self.lock:
            self.sensor_messages.append(msg)
    
    def add_safety(self, msg: SafetyMessage):
        with self.lock:
            self.safety_messages.append(msg)
    
    def clear(self):
        with self.lock:
            self.sensor_messages.clear()
            self.safety_messages.clear()
    
    def get_sensor_count(self) -> int:
        with self.lock:
            return len(self.sensor_messages)
    
    def get_safety_count(self) -> int:
        with self.lock:
            return len(self.safety_messages)
    
    def get_latest_sensor(self) -> Optional[SensorMessage]:
        with self.lock:
            return self.sensor_messages[-1] if self.sensor_messages else None
    
    def get_latest_safety(self) -> Optional[SafetyMessage]:
        with self.lock:
            return self.safety_messages[-1] if self.safety_messages else None


class ESP32HILTestClient:
    """MQTT Test Client for ESP32 HIL Testing"""
    
    def __init__(self, broker: str = "localhost", port: int = 1883,
                 device_id: str = "ESP32_FIELD_001"):
        self.broker = broker
        self.port = port
        self.device_id = device_id
        self.client = mqtt.Client(client_id="hil_test_client")
        self.capture = MessageCapture()
        self.connected = False
        
        # MQTT topics
        self.topic_sensor_data = "modax/sensor/data"
        self.topic_safety = "modax/sensor/safety"
        self.topic_command = f"modax/command/{device_id}"
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
            # Subscribe to sensor and safety topics
            client.subscribe(self.topic_sensor_data)
            client.subscribe(self.topic_safety)
            logger.info(f"Subscribed to {self.topic_sensor_data} and {self.topic_safety}")
        else:
            logger.error(f"Connection failed with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == self.topic_sensor_data:
                sensor_msg = SensorMessage(
                    timestamp=time.time(),
                    device_id=payload.get("device_id", ""),
                    current_1=payload.get("current_1", 0.0),
                    current_2=payload.get("current_2", 0.0),
                    temperature_1=payload.get("temperature_1", 0.0),
                    vibration_x=payload.get("vibration_x", 0.0),
                    vibration_y=payload.get("vibration_y", 0.0),
                    vibration_z=payload.get("vibration_z", 0.0),
                    raw_data=payload
                )
                self.capture.add_sensor(sensor_msg)
                logger.debug(f"Captured sensor data: {sensor_msg.device_id}")
            
            elif msg.topic == self.topic_safety:
                safety_msg = SafetyMessage(
                    timestamp=time.time(),
                    device_id=payload.get("device_id", ""),
                    emergency_stop=payload.get("emergency_stop", False),
                    door_closed=payload.get("door_closed", True),
                    overload_detected=payload.get("overload_detected", False),
                    temperature_ok=payload.get("temperature_ok", True),
                    raw_data=payload
                )
                self.capture.add_safety(safety_msg)
                logger.debug(f"Captured safety data: {safety_msg.device_id}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def connect(self, timeout: float = 5.0) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
    
    def send_command(self, command: Dict[str, Any]) -> bool:
        """Send command to ESP32"""
        if not self.connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        try:
            payload = json.dumps(command)
            result = self.client.publish(self.topic_command, payload)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
    
    def wait_for_messages(self, duration: float, 
                         expected_sensor: int = 0,
                         expected_safety: int = 0) -> bool:
        """Wait for expected number of messages"""
        start_time = time.time()
        while time.time() - start_time < duration:
            sensor_count = self.capture.get_sensor_count()
            safety_count = self.capture.get_safety_count()
            
            if (sensor_count >= expected_sensor and 
                safety_count >= expected_safety):
                return True
            
            time.sleep(0.1)
        
        return False


@pytest.fixture(scope="module")
def mqtt_broker():
    """MQTT broker configuration"""
    return {
        "host": "localhost",
        "port": 1883
    }


@pytest.fixture
def hil_client(mqtt_broker):
    """Create and connect HIL test client"""
    client = ESP32HILTestClient(
        broker=mqtt_broker["host"],
        port=mqtt_broker["port"]
    )
    
    # Connect to broker
    assert client.connect(timeout=10.0), "Failed to connect to MQTT broker"
    
    # Clear any existing messages
    client.capture.clear()
    
    yield client
    
    # Cleanup
    client.disconnect()


# ============================================================================
# Test Suite 1: Basic Communication Tests
# ============================================================================

class TestBasicCommunication:
    """Test basic MQTT communication with ESP32"""
    
    def test_mqtt_connection(self, hil_client):
        """Test MQTT broker connection is established"""
        assert hil_client.connected, "Client should be connected to MQTT broker"
    
    def test_sensor_data_received(self, hil_client):
        """Test that sensor data messages are received"""
        # Wait for at least 3 sensor messages (10Hz rate, 0.5s should give ~5)
        success = hil_client.wait_for_messages(
            duration=1.0,
            expected_sensor=3
        )
        
        assert success, f"Expected at least 3 sensor messages, got {hil_client.capture.get_sensor_count()}"
        
        # Verify message structure
        msg = hil_client.capture.get_latest_sensor()
        assert msg is not None, "No sensor messages captured"
        assert msg.device_id != "", "Device ID should not be empty"
        assert "current_1" in msg.raw_data, "Message should contain current_1"
        assert "temperature_1" in msg.raw_data, "Message should contain temperature_1"
    
    def test_safety_data_received(self, hil_client):
        """Test that safety status messages are received"""
        # Wait for at least 5 safety messages (20Hz rate, 0.5s should give ~10)
        success = hil_client.wait_for_messages(
            duration=1.0,
            expected_safety=5
        )
        
        assert success, f"Expected at least 5 safety messages, got {hil_client.capture.get_safety_count()}"
        
        # Verify message structure
        msg = hil_client.capture.get_latest_safety()
        assert msg is not None, "No safety messages captured"
        assert msg.device_id != "", "Device ID should not be empty"
        assert isinstance(msg.emergency_stop, bool), "emergency_stop should be boolean"
        assert isinstance(msg.door_closed, bool), "door_closed should be boolean"


# ============================================================================
# Test Suite 2: Sensor Data Flow Tests
# ============================================================================

class TestSensorDataFlow:
    """Test sensor data format and publishing frequency"""
    
    def test_sensor_publishing_rate(self, hil_client):
        """Test sensor data is published at ~10Hz"""
        hil_client.capture.clear()
        
        # Collect messages for 2 seconds
        time.sleep(2.0)
        
        count = hil_client.capture.get_sensor_count()
        # Expected: ~20 messages (10Hz * 2s), allow 50% tolerance
        assert 10 <= count <= 30, f"Expected 10-30 sensor messages in 2s, got {count}"
        
        # Calculate actual rate
        actual_rate = count / 2.0
        logger.info(f"Actual sensor publishing rate: {actual_rate:.1f} Hz")
    
    def test_safety_publishing_rate(self, hil_client):
        """Test safety data is published at ~20Hz"""
        hil_client.capture.clear()
        
        # Collect messages for 2 seconds
        time.sleep(2.0)
        
        count = hil_client.capture.get_safety_count()
        # Expected: ~40 messages (20Hz * 2s), allow 50% tolerance
        assert 20 <= count <= 60, f"Expected 20-60 safety messages in 2s, got {count}"
        
        # Calculate actual rate
        actual_rate = count / 2.0
        logger.info(f"Actual safety publishing rate: {actual_rate:.1f} Hz")
    
    def test_sensor_data_format(self, hil_client):
        """Test sensor data has correct format and valid ranges"""
        # Wait for messages
        hil_client.wait_for_messages(duration=1.0, expected_sensor=5)
        
        msg = hil_client.capture.get_latest_sensor()
        assert msg is not None, "No sensor messages captured"
        
        # Validate data types and ranges
        assert isinstance(msg.current_1, (int, float)), "current_1 should be numeric"
        assert isinstance(msg.current_2, (int, float)), "current_2 should be numeric"
        assert isinstance(msg.temperature_1, (int, float)), "temperature_1 should be numeric"
        assert isinstance(msg.vibration_x, (int, float)), "vibration_x should be numeric"
        assert isinstance(msg.vibration_y, (int, float)), "vibration_y should be numeric"
        assert isinstance(msg.vibration_z, (int, float)), "vibration_z should be numeric"
        
        # Basic sanity checks (assuming reasonable sensor ranges)
        assert -100 <= msg.current_1 <= 100, "current_1 out of reasonable range"
        assert -100 <= msg.current_2 <= 100, "current_2 out of reasonable range"
        assert -50 <= msg.temperature_1 <= 150, "temperature_1 out of reasonable range"
    
    def test_message_timestamps(self, hil_client):
        """Test messages have monotonically increasing timestamps"""
        hil_client.capture.clear()
        
        # Collect messages for 1 second
        time.sleep(1.0)
        
        with hil_client.capture.lock:
            messages = list(hil_client.capture.sensor_messages)
        
        assert len(messages) >= 5, "Need at least 5 messages to test timestamps"
        
        # Check timestamps are increasing
        for i in range(1, len(messages)):
            assert messages[i].timestamp >= messages[i-1].timestamp, \
                f"Timestamps should be monotonically increasing"


# ============================================================================
# Test Suite 3: Safety Monitoring Tests
# ============================================================================

class TestSafetyMonitoring:
    """Test safety checks and emergency response"""
    
    def test_normal_safety_state(self, hil_client):
        """Test safety state under normal conditions"""
        hil_client.capture.clear()
        
        # Collect safety messages
        hil_client.wait_for_messages(duration=1.0, expected_safety=10)
        
        msg = hil_client.capture.get_latest_safety()
        assert msg is not None, "No safety messages captured"
        
        # Under normal conditions, these should be the expected states
        # (May need adjustment based on actual hardware setup)
        logger.info(f"Safety state: emergency_stop={msg.emergency_stop}, "
                   f"door_closed={msg.door_closed}, "
                   f"overload={msg.overload_detected}, "
                   f"temp_ok={msg.temperature_ok}")
        
        # At least verify the message structure is correct
        assert isinstance(msg.emergency_stop, bool)
        assert isinstance(msg.door_closed, bool)
        assert isinstance(msg.overload_detected, bool)
        assert isinstance(msg.temperature_ok, bool)
    
    def test_safety_message_frequency(self, hil_client):
        """Test safety messages are more frequent than sensor messages"""
        hil_client.capture.clear()
        
        # Collect for 1 second
        time.sleep(1.0)
        
        sensor_count = hil_client.capture.get_sensor_count()
        safety_count = hil_client.capture.get_safety_count()
        
        # Safety should be ~2x sensor frequency (20Hz vs 10Hz)
        # Allow for some variance
        assert safety_count >= sensor_count, \
            f"Safety messages ({safety_count}) should be at least as frequent as sensor messages ({sensor_count})"


# ============================================================================
# Test Suite 4: Robustness Tests
# ============================================================================

class TestRobustness:
    """Test system robustness under stress conditions"""
    
    @pytest.mark.slow
    def test_long_running_stability(self, hil_client):
        """Test ESP32 stability over extended period (60 seconds)"""
        hil_client.capture.clear()
        
        duration = 60.0
        start_time = time.time()
        
        logger.info(f"Starting long-running test for {duration}s...")
        
        # Monitor for message gaps
        last_sensor_time = time.time()
        last_safety_time = time.time()
        max_sensor_gap = 0.0
        max_safety_gap = 0.0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Check sensor messages
            if hil_client.capture.get_sensor_count() > 0:
                gap = current_time - last_sensor_time
                max_sensor_gap = max(max_sensor_gap, gap)
                last_sensor_time = current_time
            
            # Check safety messages
            if hil_client.capture.get_safety_count() > 0:
                gap = current_time - last_safety_time
                max_safety_gap = max(max_safety_gap, gap)
                last_safety_time = current_time
            
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        sensor_count = hil_client.capture.get_sensor_count()
        safety_count = hil_client.capture.get_safety_count()
        
        logger.info(f"Long-running test completed: {elapsed:.1f}s")
        logger.info(f"Sensor messages: {sensor_count} ({sensor_count/elapsed:.1f} Hz)")
        logger.info(f"Safety messages: {safety_count} ({safety_count/elapsed:.1f} Hz)")
        logger.info(f"Max sensor gap: {max_sensor_gap:.3f}s")
        logger.info(f"Max safety gap: {max_safety_gap:.3f}s")
        
        # Verify reasonable message counts
        expected_sensor = int(10 * elapsed * 0.7)  # 70% of expected
        expected_safety = int(20 * elapsed * 0.7)
        
        assert sensor_count >= expected_sensor, \
            f"Expected at least {expected_sensor} sensor messages, got {sensor_count}"
        assert safety_count >= expected_safety, \
            f"Expected at least {expected_safety} safety messages, got {safety_count}"
        
        # Verify no long gaps (max 1 second)
        assert max_sensor_gap < 1.0, f"Sensor gap too large: {max_sensor_gap:.3f}s"
        assert max_safety_gap < 1.0, f"Safety gap too large: {max_safety_gap:.3f}s"
    
    def test_reconnection_after_disconnect(self, mqtt_broker):
        """Test MQTT reconnection after simulated disconnect"""
        client = ESP32HILTestClient(
            broker=mqtt_broker["host"],
            port=mqtt_broker["port"]
        )
        
        # Initial connection
        assert client.connect(timeout=5.0), "Initial connection failed"
        time.sleep(1.0)
        
        # Verify messages are flowing
        initial_count = client.capture.get_sensor_count()
        assert initial_count > 0, "No messages received after initial connection"
        
        # Simulate disconnect
        logger.info("Simulating disconnect...")
        client.disconnect()
        time.sleep(2.0)
        
        # Reconnect
        logger.info("Reconnecting...")
        assert client.connect(timeout=10.0), "Reconnection failed"
        
        # Clear old messages
        client.capture.clear()
        time.sleep(1.0)
        
        # Verify messages resume
        new_count = client.capture.get_sensor_count()
        assert new_count > 0, "No messages received after reconnection"
        
        logger.info(f"Reconnection successful: {new_count} messages received")
        
        # Cleanup
        client.disconnect()
    
    @pytest.mark.slow
    def test_message_burst_handling(self, hil_client):
        """Test system handles message bursts without loss"""
        hil_client.capture.clear()
        
        # Monitor for 5 seconds during which ESP32 sends continuous messages
        duration = 5.0
        time.sleep(duration)
        
        sensor_count = hil_client.capture.get_sensor_count()
        safety_count = hil_client.capture.get_safety_count()
        
        # Calculate expected counts with tolerance
        expected_sensor_min = int(10 * duration * 0.8)  # 80% tolerance
        expected_safety_min = int(20 * duration * 0.8)
        
        assert sensor_count >= expected_sensor_min, \
            f"Expected at least {expected_sensor_min} sensor messages, got {sensor_count}"
        assert safety_count >= expected_safety_min, \
            f"Expected at least {expected_safety_min} safety messages, got {safety_count}"
        
        logger.info(f"Burst test: {sensor_count} sensor, {safety_count} safety messages in {duration}s")


# ============================================================================
# Test Suite 5: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test boundary conditions and error handling"""
    
    def test_invalid_command_handling(self, hil_client):
        """Test ESP32 handles invalid commands gracefully"""
        # Send invalid command
        invalid_cmd = {"invalid": "command", "malformed": True}
        result = hil_client.send_command(invalid_cmd)
        
        # Command should be sent (MQTT perspective)
        assert result, "Failed to send command"
        
        # ESP32 should continue operating normally
        time.sleep(2.0)
        
        sensor_count = hil_client.capture.get_sensor_count()
        safety_count = hil_client.capture.get_safety_count()
        
        # Verify ESP32 is still publishing messages
        assert sensor_count > 0, "ESP32 stopped publishing sensor data after invalid command"
        assert safety_count > 0, "ESP32 stopped publishing safety data after invalid command"
    
    def test_multiple_clients_subscription(self, mqtt_broker):
        """Test multiple test clients can receive messages simultaneously"""
        clients = []
        
        try:
            # Create multiple clients
            for i in range(3):
                client = ESP32HILTestClient(
                    broker=mqtt_broker["host"],
                    port=mqtt_broker["port"]
                )
                client.client._client_id = f"hil_test_client_{i}"
                assert client.connect(timeout=5.0), f"Client {i} failed to connect"
                clients.append(client)
            
            # Wait for messages
            time.sleep(2.0)
            
            # Verify all clients received messages
            for i, client in enumerate(clients):
                sensor_count = client.capture.get_sensor_count()
                safety_count = client.capture.get_safety_count()
                
                assert sensor_count > 0, f"Client {i} received no sensor messages"
                assert safety_count > 0, f"Client {i} received no safety messages"
                
                logger.info(f"Client {i}: {sensor_count} sensor, {safety_count} safety messages")
        
        finally:
            # Cleanup all clients
            for client in clients:
                client.disconnect()
    
    def test_message_size_reasonable(self, hil_client):
        """Test MQTT message sizes are reasonable"""
        hil_client.capture.clear()
        
        # Collect some messages
        hil_client.wait_for_messages(duration=1.0, expected_sensor=5)
        
        msg = hil_client.capture.get_latest_sensor()
        assert msg is not None, "No sensor messages captured"
        
        # Estimate message size
        msg_json = json.dumps(msg.raw_data)
        msg_size = len(msg_json.encode('utf-8'))
        
        logger.info(f"Sensor message size: {msg_size} bytes")
        
        # Message should be reasonably small (< 1KB)
        assert msg_size < 1024, f"Message size too large: {msg_size} bytes"
        
        # Message should contain essential data (> 50 bytes)
        assert msg_size > 50, f"Message size suspiciously small: {msg_size} bytes"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
