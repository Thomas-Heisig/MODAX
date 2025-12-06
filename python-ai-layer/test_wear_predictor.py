"""Unit tests for Wear Predictor module"""
import unittest
from wear_predictor import SimpleWearPredictor, WearPrediction


class TestWearPrediction(unittest.TestCase):
    """Tests for WearPrediction dataclass"""
    
    def test_creation(self):
        """Test creating WearPrediction"""
        prediction = WearPrediction(
            wear_level=0.35,
            estimated_remaining_hours=5000,
            contributing_factors=["High current", "Elevated temperature"],
            confidence=0.85
        )
        
        self.assertEqual(prediction.wear_level, 0.35)
        self.assertEqual(prediction.estimated_remaining_hours, 5000)
        self.assertEqual(len(prediction.contributing_factors), 2)


class TestSimpleWearPredictor(unittest.TestCase):
    """Tests for SimpleWearPredictor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = SimpleWearPredictor()
        self.device_id = "test_device_001"
    
    def test_initialization(self):
        """Test predictor initialization"""
        self.assertGreater(self.predictor.nominal_lifetime, 0)
        self.assertEqual(len(self.predictor.wear_rates), 0)
    
    def test_predict_wear_normal_conditions(self):
        """Test wear prediction under normal operating conditions"""
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [5.0, 5.1, 4.9],
            "current_max": [6.0, 6.2, 5.8],
            "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            "vibration_max": {"x": 2.0, "y": 2.1, "z": 1.9, "magnitude": 3.0},
            "temperature_mean": [45.0, 46.0, 44.5],
            "temperature_max": [48.0, 49.0, 47.5]
        }
        
        prediction = self.predictor.predict_wear(sensor_data, self.device_id)
        
        self.assertIsInstance(prediction, WearPrediction)
        self.assertGreaterEqual(prediction.wear_level, 0.0)
        self.assertLessEqual(prediction.wear_level, 1.0)
        self.assertGreater(prediction.estimated_remaining_hours, 0)
        self.assertGreater(prediction.confidence, 0.0)
    
    def test_predict_wear_high_stress(self):
        """Test wear prediction under high stress conditions"""
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [10.0, 10.5, 9.8],  # High current
            "current_max": [12.0, 12.5, 11.8],
            "vibration_mean": {"x": 8.0, "y": 8.5, "z": 7.5, "magnitude": 12.0},  # High vibration
            "vibration_max": {"x": 10.0, "y": 11.0, "z": 9.5, "magnitude": 15.0},
            "temperature_mean": [70.0, 71.0, 69.5],  # High temperature
            "temperature_max": [75.0, 76.0, 74.5]
        }
        
        prediction = self.predictor.predict_wear(sensor_data, self.device_id)
        
        # Should have higher wear under stress
        self.assertGreater(prediction.wear_level, 0.0)
        # Should have contributing factors
        self.assertGreater(len(prediction.contributing_factors), 0)
    
    def test_predict_wear_accumulation(self):
        """Test that wear accumulates over multiple predictions"""
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [7.0, 7.1, 6.9],
            "current_max": [8.0, 8.2, 7.8],
            "vibration_mean": {"x": 3.0, "y": 3.1, "z": 2.9, "magnitude": 5.0},
            "vibration_max": {"x": 4.0, "y": 4.1, "z": 3.9, "magnitude": 6.5},
            "temperature_mean": [55.0, 56.0, 54.5],
            "temperature_max": [60.0, 61.0, 59.5]
        }
        
        # First prediction
        prediction1 = self.predictor.predict_wear(sensor_data, self.device_id)
        wear_level1 = prediction1.wear_level
        
        # Second prediction (same conditions)
        prediction2 = self.predictor.predict_wear(sensor_data, self.device_id)
        wear_level2 = prediction2.wear_level
        
        # Wear should increase
        self.assertGreaterEqual(wear_level2, wear_level1)
    
    def test_reset_wear(self):
        """Test resetting wear counter after maintenance"""
        # Accumulate some wear
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [7.0, 7.1, 6.9],
            "current_max": [8.0, 8.2, 7.8],
            "vibration_mean": {"x": 3.0, "y": 3.1, "z": 2.9, "magnitude": 5.0},
            "vibration_max": {"x": 4.0, "y": 4.1, "z": 3.9, "magnitude": 6.5},
            "temperature_mean": [55.0, 56.0, 54.5],
            "temperature_max": [60.0, 61.0, 59.5]
        }
        
        self.predictor.predict_wear(sensor_data, self.device_id)
        
        # Reset wear
        self.predictor.reset_wear(self.device_id)
        
        # Check that wear was reset
        if self.device_id in self.predictor.wear_rates:
            self.assertEqual(self.predictor.wear_rates[self.device_id], 0.0)
    
    def test_contributing_factors_high_current(self):
        """Test that high current is identified as contributing factor"""
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [10.0, 10.5, 9.8],
            "current_max": [12.0, 12.5, 11.8],
            "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            "vibration_max": {"x": 2.0, "y": 2.1, "z": 1.9, "magnitude": 3.0},
            "temperature_mean": [45.0, 46.0, 44.5],
            "temperature_max": [48.0, 49.0, 47.5]
        }
        
        prediction = self.predictor.predict_wear(sensor_data, self.device_id)
        
        # Check if high current is mentioned in contributing factors
        factors_text = " ".join(prediction.contributing_factors).lower()
        self.assertIn("current", factors_text)
    
    def test_contributing_factors_high_vibration(self):
        """Test that high vibration is identified as contributing factor"""
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": 0.0,
            "time_window_end": 10.0,
            "current_mean": [5.0, 5.1, 4.9],
            "current_max": [6.0, 6.2, 5.8],
            "vibration_mean": {"x": 8.0, "y": 8.5, "z": 7.5, "magnitude": 12.0},
            "vibration_max": {"x": 10.0, "y": 11.0, "z": 9.5, "magnitude": 15.0},
            "temperature_mean": [45.0, 46.0, 44.5],
            "temperature_max": [48.0, 49.0, 47.5]
        }
        
        prediction = self.predictor.predict_wear(sensor_data, self.device_id)
        
        # Check if vibration is mentioned in contributing factors
        factors_text = " ".join(prediction.contributing_factors).lower()
        self.assertIn("vibration", factors_text)


if __name__ == '__main__':
    unittest.main()
