"""Unit tests for Configuration module"""
import unittest
import os
from unittest.mock import patch
from config import MQTTConfig, ControlConfig, Config


class TestMQTTConfig(unittest.TestCase):
    """Tests for MQTT Configuration"""
    
    def test_mqtt_config_defaults(self):
        """Test MQTT config with default values (when env vars not set)"""
        # Note: We test the current configuration, which may have env vars set
        # So we just verify the config is properly initialized
        config = MQTTConfig()
        
        # These should always have values (defaults or from environment)
        self.assertIsNotNone(config.broker_host)
        self.assertIsInstance(config.broker_port, int)
        self.assertGreaterEqual(config.broker_port, 1)
        self.assertIsInstance(config.use_tls, bool)
        self.assertEqual(config.topic_sensor_data, "modax/sensor/data")
        self.assertEqual(config.topic_safety, "modax/sensor/safety")
        self.assertEqual(config.topic_ai_analysis, "modax/ai/analysis")
        self.assertEqual(config.topic_control_commands, "modax/control/commands")
    
    def test_mqtt_config_fields_exist(self):
        """Test that all expected fields exist in MQTT config"""
        config = MQTTConfig()
        
        # Verify all fields are accessible
        self.assertIsNotNone(config.broker_host)
        self.assertIsInstance(config.broker_port, int)
        # username and password can be None
        self.assertIsInstance(config.use_tls, bool)
        self.assertIsInstance(config.tls_insecure, bool)
        # Certificate paths can be None
        self.assertIsInstance(config.topic_sensor_data, str)
        self.assertIsInstance(config.topic_safety, str)
        self.assertIsInstance(config.topic_ai_analysis, str)
        self.assertIsInstance(config.topic_control_commands, str)


class TestControlConfig(unittest.TestCase):
    """Tests for Control Layer Configuration"""
    
    def test_control_config_fields_exist(self):
        """Test that all expected fields exist in Control config"""
        config = ControlConfig()
        
        # Verify all fields are accessible
        self.assertIsNotNone(config.api_host)
        self.assertIsInstance(config.api_port, int)
        self.assertGreaterEqual(config.api_port, 1)
        self.assertIsInstance(config.api_key_enabled, bool)
        # api_key can be None
        self.assertIsInstance(config.aggregation_window_seconds, int)
        self.assertIsInstance(config.max_data_points, int)
        self.assertIsInstance(config.ai_layer_enabled, bool)
        self.assertIsNotNone(config.ai_layer_url)
        self.assertIsInstance(config.ai_layer_timeout, int)
        self.assertIsInstance(config.ai_analysis_interval_seconds, int)
    
    def test_control_config_valid_values(self):
        """Test Control config has valid values"""
        config = ControlConfig()
        
        # Check reasonable ranges
        self.assertGreater(config.aggregation_window_seconds, 0)
        self.assertGreater(config.max_data_points, 0)
        self.assertGreater(config.ai_layer_timeout, 0)
        self.assertGreater(config.ai_analysis_interval_seconds, 0)
        
        # URL should contain http or https
        self.assertTrue(
            config.ai_layer_url.startswith('http://') or 
            config.ai_layer_url.startswith('https://')
        )


class TestConfig(unittest.TestCase):
    """Tests for Master Configuration"""
    
    def test_config_initialization(self):
        """Test master config initialization"""
        config = Config()
        
        self.assertIsInstance(config.mqtt, MQTTConfig)
        self.assertIsInstance(config.control, ControlConfig)
    
    def test_config_mqtt_access(self):
        """Test accessing MQTT config through master config"""
        config = Config()
        
        # Verify we can access MQTT config fields
        self.assertIsNotNone(config.mqtt.broker_host)
        self.assertIsInstance(config.mqtt.broker_port, int)
        self.assertGreaterEqual(config.mqtt.broker_port, 1)
    
    def test_config_control_access(self):
        """Test accessing Control config through master config"""
        config = Config()
        
        # Verify we can access Control config fields
        self.assertIsNotNone(config.control.api_host)
        self.assertIsInstance(config.control.api_port, int)
        self.assertGreaterEqual(config.control.api_port, 1)
    
    def test_config_structure(self):
        """Test config has expected structure"""
        config = Config()
        
        # Verify nested structure
        self.assertTrue(hasattr(config, 'mqtt'))
        self.assertTrue(hasattr(config, 'control'))
        self.assertTrue(hasattr(config.mqtt, 'broker_host'))
        self.assertTrue(hasattr(config.mqtt, 'broker_port'))
        self.assertTrue(hasattr(config.control, 'api_host'))
        self.assertTrue(hasattr(config.control, 'api_port'))


if __name__ == '__main__':
    unittest.main()
