"""Integration tests for MQTT communication"""
import unittest
from unittest.mock import Mock, patch
import json
import time
from config import MQTTConfig
from mqtt_handler import MQTTHandler
from data_aggregator import SensorReading, SafetyStatus


class TestMQTTIntegration(unittest.TestCase):
    """Integration tests for MQTT communication flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            topic_sensor_data="modax/sensor_data",
            topic_safety="modax/safety",
            topic_ai_analysis="modax/ai_analysis",
            topic_control_commands="modax/control",
            username=None,
            password=None
        )

        with patch('mqtt_handler.mqtt.Client'):
            self.handler = MQTTHandler(self.config)
            self.handler.client = Mock()

    def test_sensor_data_flow(self):
        """Test sensor data flow from MQTT to callback"""
        # Create mock callback
        callback_mock = Mock()
        self.handler.on_sensor_data = callback_mock

        # Simulate MQTT message
        msg = Mock()
        msg.topic = "modax/sensor_data"
        msg.payload = json.dumps({
            "timestamp": int(time.time() * 1000),
            "device_id": "device_001",
            "motor_currents": [5.5, 5.3, 5.4],
            "vibration": {"x": 1.2, "y": 1.3, "z": 1.1, "magnitude": 2.1},
            "temperatures": [45.0, 46.5, 44.8]
        }).encode('utf-8')

        # Process message
        self.handler._on_message(self.handler.client, None, msg)

        # Verify callback was called with correct data
        callback_mock.assert_called_once()
        reading = callback_mock.call_args[0][0]
        self.assertIsInstance(reading, SensorReading)
        self.assertEqual(reading.device_id, "device_001")
        self.assertEqual(len(reading.motor_currents), 3)

    def test_safety_status_flow(self):
        """Test safety status flow from MQTT to callback"""
        # Create mock callback
        callback_mock = Mock()
        self.handler.on_safety_status = callback_mock

        # Simulate MQTT message with unsafe condition
        msg = Mock()
        msg.topic = "modax/safety"
        msg.payload = json.dumps({
            "timestamp": int(time.time() * 1000),
            "device_id": "device_001",
            "emergency_stop": True,  # Unsafe!
            "door_closed": True,
            "overload_detected": False,
            "temperature_ok": True
        }).encode('utf-8')

        # Process message
        self.handler._on_message(self.handler.client, None, msg)

        # Verify callback was called
        callback_mock.assert_called_once()
        status = callback_mock.call_args[0][0]
        self.assertIsInstance(status, SafetyStatus)
        self.assertFalse(status.is_safe())
        self.assertTrue(status.emergency_stop)

    def test_ai_analysis_publishing(self):
        """Test publishing AI analysis results"""
        analysis = {
            "timestamp": int(time.time() * 1000),
            "device_id": "device_001",
            "anomaly_detected": True,
            "anomaly_score": 0.85,
            "predicted_wear_level": 0.45,
            "recommendations": ["Check vibration levels", "Inspect bearings"]
        }

        self.handler.publish_ai_analysis(analysis)

        # Verify MQTT publish was called
        self.handler.client.publish.assert_called_once()
        call_args = self.handler.client.publish.call_args

        # Check topic
        self.assertEqual(call_args[0][0], self.config.topic_ai_analysis)

        # Check payload contains analysis data
        payload = call_args[0][1]
        self.assertIn("device_001", payload)
        self.assertIn("anomaly_detected", payload)

    def test_control_command_publishing(self):
        """Test publishing control commands"""
        command = {
            "timestamp": int(time.time() * 1000),
            "command_type": "set_speed",
            "parameters": {"speed": 1500, "ramp_time": 5}
        }

        self.handler.publish_control_command(command)

        # Verify MQTT publish was called
        self.handler.client.publish.assert_called_once()
        call_args = self.handler.client.publish.call_args

        # Check topic
        self.assertEqual(call_args[0][0], self.config.topic_control_commands)

        # Check payload contains command data
        payload = call_args[0][1]
        self.assertIn("set_speed", payload)

    def test_multiple_messages_sequence(self):
        """Test handling sequence of multiple messages"""
        sensor_callback = Mock()
        safety_callback = Mock()
        ai_callback = Mock()

        self.handler.on_sensor_data = sensor_callback
        self.handler.on_safety_status = safety_callback
        self.handler.on_ai_analysis = ai_callback

        # Simulate sequence of messages
        messages = [
            ("modax/sensor_data", {
                "timestamp": int(time.time() * 1000),
                "device_id": "device_001",
                "motor_currents": [5.5, 5.3, 5.4],
                "vibration": {"x": 1.2, "y": 1.3, "z": 1.1, "magnitude": 2.1},
                "temperatures": [45.0, 46.5, 44.8]
            }),
            ("modax/safety", {
                "timestamp": int(time.time() * 1000),
                "device_id": "device_001",
                "emergency_stop": False,
                "door_closed": True,
                "overload_detected": False,
                "temperature_ok": True
            }),
            ("modax/ai_analysis", {
                "device_id": "device_001",
                "anomaly_detected": False,
                "wear_level": 0.25
            })
        ]

        for topic, payload in messages:
            msg = Mock()
            msg.topic = topic
            msg.payload = json.dumps(payload).encode('utf-8')
            self.handler._on_message(self.handler.client, None, msg)

        # Verify all callbacks were called
        sensor_callback.assert_called_once()
        safety_callback.assert_called_once()
        ai_callback.assert_called_once()

    def test_malformed_message_handling(self):
        """Test handling of malformed JSON messages"""
        callback_mock = Mock()
        self.handler.on_sensor_data = callback_mock

        # Simulate message with invalid JSON
        msg = Mock()
        msg.topic = "modax/sensor_data"
        msg.payload = b"invalid json {not valid"

        # Process message - should not crash
        self.handler._on_message(self.handler.client, None, msg)

        # Callback should not have been called due to parse error
        callback_mock.assert_not_called()

    def test_reconnection_state_tracking(self):
        """Test that reconnection state is properly tracked"""
        # Initial state
        self.assertFalse(self.handler._is_connected)

        # Simulate connection
        self.handler._on_connect(self.handler.client, None, None, 0)
        self.assertTrue(self.handler._is_connected)

        # Simulate disconnect
        self.handler._on_disconnect(self.handler.client, None, 1)
        self.assertFalse(self.handler._is_connected)


if __name__ == '__main__':
    unittest.main()
