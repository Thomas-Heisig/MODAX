"""Unit tests for MQTT Handler module"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import json
from config import MQTTConfig
from mqtt_handler import MQTTHandler
from data_aggregator import SensorReading, SafetyStatus


class TestMQTTHandler(unittest.TestCase):
    """Tests for MQTTHandler class"""
    
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
        
        # Mock paho mqtt client
        with patch('mqtt_handler.mqtt.Client'):
            self.handler = MQTTHandler(self.config)
            self.handler.client = Mock()
    
    def test_initialization(self):
        """Test MQTT handler initialization"""
        self.assertIsNotNone(self.handler)
        self.assertEqual(self.handler.config, self.config)
        self.assertFalse(self.handler._is_connected)
    
    def test_publish_ai_analysis(self):
        """Test publishing AI analysis results"""
        analysis = {
            "device_id": "device_001",
            "anomaly_detected": True,
            "wear_level": 0.35
        }
        
        self.handler.publish_ai_analysis(analysis)
        
        self.handler.client.publish.assert_called_once()
        call_args = self.handler.client.publish.call_args
        self.assertEqual(call_args[0][0], self.config.topic_ai_analysis)
        self.assertIn("device_001", call_args[0][1])
    
    def test_publish_control_command(self):
        """Test publishing control command"""
        command = {
            "command_type": "set_speed",
            "parameters": {"speed": 1500}
        }
        
        self.handler.publish_control_command(command)
        
        self.handler.client.publish.assert_called_once()
        call_args = self.handler.client.publish.call_args
        self.assertEqual(call_args[0][0], self.config.topic_control_commands)
    
    def test_on_connect_success(self):
        """Test successful connection callback"""
        self.handler._on_connect(self.handler.client, None, None, 0)
        
        self.assertTrue(self.handler._is_connected)
        self.handler.client.subscribe.assert_called()
    
    def test_on_connect_failure(self):
        """Test failed connection callback"""
        self.handler._on_connect(self.handler.client, None, None, 1)
        
        self.assertFalse(self.handler._is_connected)
    
    def test_on_disconnect_unexpected(self):
        """Test unexpected disconnect callback"""
        self.handler._is_connected = True
        self.handler._on_disconnect(self.handler.client, None, 1)
        
        self.assertFalse(self.handler._is_connected)
    
    def test_handle_sensor_data(self):
        """Test handling sensor data message"""
        sensor_data_json = json.dumps({
            "timestamp": 1234567890000,
            "device_id": "device_001",
            "motor_currents": [5.5, 5.3, 5.4],
            "vibration": {"x": 1.2, "y": 1.3, "z": 1.1, "magnitude": 2.1},
            "temperatures": [45.0, 46.5, 44.8]
        })
        
        callback_mock = Mock()
        self.handler.on_sensor_data = callback_mock
        
        self.handler._handle_sensor_data(sensor_data_json)
        
        callback_mock.assert_called_once()
        reading = callback_mock.call_args[0][0]
        self.assertIsInstance(reading, SensorReading)
        self.assertEqual(reading.device_id, "device_001")
    
    def test_handle_safety_status(self):
        """Test handling safety status message"""
        safety_json = json.dumps({
            "timestamp": 1234567890000,
            "device_id": "device_001",
            "emergency_stop": False,
            "door_closed": True,
            "overload_detected": False,
            "temperature_ok": True
        })
        
        callback_mock = Mock()
        self.handler.on_safety_status = callback_mock
        
        self.handler._handle_safety_status(safety_json)
        
        callback_mock.assert_called_once()
        status = callback_mock.call_args[0][0]
        self.assertIsInstance(status, SafetyStatus)
        self.assertEqual(status.device_id, "device_001")
    
    def test_handle_ai_analysis(self):
        """Test handling AI analysis message"""
        analysis_json = json.dumps({
            "device_id": "device_001",
            "anomaly_detected": True,
            "wear_level": 0.45
        })
        
        callback_mock = Mock()
        self.handler.on_ai_analysis = callback_mock
        
        self.handler._handle_ai_analysis(analysis_json)
        
        callback_mock.assert_called_once()
        analysis = callback_mock.call_args[0][0]
        self.assertEqual(analysis['device_id'], "device_001")
        self.assertTrue(analysis['anomaly_detected'])


if __name__ == '__main__':
    unittest.main()
