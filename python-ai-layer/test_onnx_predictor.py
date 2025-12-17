"""Tests for ONNX RUL Predictor"""

import unittest
import numpy as np
from onnx_predictor import (
    ONNXRULPredictor,
    RULPrediction,
    ModelMetadata,
    get_rul_predictor
)


class TestONNXRULPredictor(unittest.TestCase):
    """Test ONNX RUL Predictor functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.predictor = ONNXRULPredictor(
            model_path="nonexistent_model.onnx",  # Will use fallback
            sequence_length=10,
            feature_count=6
        )

        self.sample_sensor_data = {
            'current_mean': [5.0, 5.2, 5.1],
            'current_std': [0.3, 0.4, 0.35],
            'vibration_mean': {'x': 2.0, 'y': 2.5, 'z': 1.8},
            'vibration_std': {'x': 0.5, 'y': 0.6, 'z': 0.4},
            'temperature_mean': [45.0, 46.0, 45.5],
            'temperature_max': [50.0, 51.0, 50.5],
            'load_factor': 0.6
        }

    def test_initialization(self):
        """Test predictor initialization"""
        self.assertEqual(self.predictor.sequence_length, 10)
        self.assertEqual(self.predictor.feature_count, 6)
        self.assertIsNotNone(self.predictor.data_buffer)
        self.assertEqual(len(self.predictor.data_buffer), 0)

    def test_prepare_features(self):
        """Test feature extraction from sensor data"""
        features = self.predictor._prepare_features(self.sample_sensor_data)

        self.assertEqual(len(features), 6)
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.dtype, np.float32)

        # Verify feature values
        self.assertAlmostEqual(features[0], 5.1, places=1)  # current mean
        self.assertAlmostEqual(features[1], 2.0, places=1)  # vib_x
        self.assertAlmostEqual(features[2], 2.5, places=1)  # vib_y
        self.assertAlmostEqual(features[3], 1.8, places=1)  # vib_z
        self.assertAlmostEqual(features[4], 45.5, places=1)  # temp mean
        self.assertAlmostEqual(features[5], 0.6, places=1)  # load factor

    def test_build_sequence_insufficient_data(self):
        """Test sequence building with insufficient data"""
        device_id = "TEST_001"
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        # Add only 5 samples (need 10)
        for _ in range(5):
            sequence = self.predictor._build_sequence(device_id, features)

        self.assertIsNone(sequence)

    def test_build_sequence_sufficient_data(self):
        """Test sequence building with sufficient data"""
        device_id = "TEST_001"
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        # Add 10 samples
        for i in range(10):
            sequence = self.predictor._build_sequence(
                device_id,
                features * (i + 1)  # Different values each time
            )

        self.assertIsNotNone(sequence)
        self.assertEqual(sequence.shape, (1, 10, 6))

    def test_fallback_prediction_normal_conditions(self):
        """Test fallback prediction under normal conditions"""
        device_id = "TEST_001"

        result = self.predictor._fallback_prediction(
            self.sample_sensor_data,
            device_id
        )

        self.assertIsInstance(result, RULPrediction)
        self.assertGreater(result.predicted_rul_hours, 0)
        self.assertEqual(result.health_status, "normal")
        self.assertGreaterEqual(result.confidence, 0.1)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertTrue(len(result.contributing_factors) > 0)
        self.assertEqual(result.model_version, "fallback-v1.0")

    def test_fallback_prediction_high_wear(self):
        """Test fallback prediction with high wear conditions"""
        device_id = "TEST_002"

        high_wear_data = {
            'current_mean': [12.0, 12.5, 12.2],  # High current
            'vibration_mean': {'x': 8.0, 'y': 8.5, 'z': 7.8},  # High vibration
            'temperature_mean': [90.0, 92.0, 91.0],  # High temperature
            'load_factor': 0.9
        }

        result = self.predictor._fallback_prediction(high_wear_data, device_id)

        self.assertIsInstance(result, RULPrediction)
        self.assertLess(
            result.predicted_rul_hours,
            5000  # Should be significantly reduced from 10000 nominal
        )
        self.assertIn(result.health_status, ["critical", "warning"])

    def test_calculate_confidence_complete_data(self):
        """Test confidence calculation with complete data"""
        confidence = self.predictor._calculate_confidence(
            self.sample_sensor_data,
            predicted_rul=1000.0
        )

        self.assertGreaterEqual(confidence, 0.1)
        self.assertLessEqual(confidence, 0.95)

    def test_calculate_confidence_incomplete_data(self):
        """Test confidence calculation with incomplete data"""
        incomplete_data = {
            'current_mean': [5.0],
            # Missing vibration and temperature
        }

        confidence = self.predictor._calculate_confidence(
            incomplete_data,
            predicted_rul=1000.0
        )

        # Confidence should be lower due to missing data
        complete_confidence = self.predictor._calculate_confidence(
            self.sample_sensor_data,
            predicted_rul=1000.0
        )

        self.assertLess(confidence, complete_confidence)

    def test_identify_contributing_factors_normal(self):
        """Test factor identification under normal conditions"""
        factors = self.predictor._identify_contributing_factors(
            self.sample_sensor_data,
            predicted_rul=5000.0
        )

        self.assertIsInstance(factors, list)
        self.assertTrue(len(factors) > 0)
        self.assertIn("Normal operating conditions", factors)

    def test_identify_contributing_factors_high_load(self):
        """Test factor identification with high load"""
        high_load_data = self.sample_sensor_data.copy()
        high_load_data['current_mean'] = [9.0, 9.5, 9.2]

        factors = self.predictor._identify_contributing_factors(
            high_load_data,
            predicted_rul=2000.0
        )

        self.assertTrue(
            any("High current" in f for f in factors),
            "Should identify high current load"
        )

    def test_identify_contributing_factors_high_vibration(self):
        """Test factor identification with excessive vibration"""
        high_vib_data = self.sample_sensor_data.copy()
        high_vib_data['vibration_mean'] = {'x': 6.0, 'y': 6.5, 'z': 6.0}

        factors = self.predictor._identify_contributing_factors(
            high_vib_data,
            predicted_rul=2000.0
        )

        self.assertTrue(
            any("vibration" in f.lower() for f in factors),
            "Should identify excessive vibration"
        )

    def test_identify_contributing_factors_high_temperature(self):
        """Test factor identification with high temperature"""
        high_temp_data = self.sample_sensor_data.copy()
        high_temp_data['temperature_mean'] = [85.0, 87.0, 86.0]

        factors = self.predictor._identify_contributing_factors(
            high_temp_data,
            predicted_rul=2000.0
        )

        self.assertTrue(
            any("temperature" in f.lower() for f in factors),
            "Should identify high temperature"
        )

    def test_reset_buffer(self):
        """Test data buffer reset"""
        device_id = "TEST_003"
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        # Build up buffer
        for _ in range(10):
            self.predictor._build_sequence(device_id, features)

        self.assertIn(device_id, self.predictor.data_buffer)
        self.assertEqual(len(self.predictor.data_buffer[device_id]), 10)

        # Reset buffer
        self.predictor.reset_buffer(device_id)

        self.assertNotIn(device_id, self.predictor.data_buffer)

    def test_predict_rul_without_model(self):
        """Test RUL prediction when ONNX model is not loaded"""
        device_id = "TEST_004"

        result = self.predictor.predict_rul(self.sample_sensor_data, device_id)

        self.assertIsInstance(result, RULPrediction)
        self.assertGreater(result.predicted_rul_hours, 0)
        self.assertIn(result.health_status, ["critical", "warning", "normal"])
        self.assertGreaterEqual(result.confidence, 0.1)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertEqual(result.model_version, "fallback-v1.0")

    def test_get_model_info_not_loaded(self):
        """Test model info when model is not loaded"""
        info = self.predictor.get_model_info()

        self.assertEqual(info["status"], "not_loaded")
        self.assertIn("message", info)

    def test_health_status_thresholds(self):
        """Test health status determination based on RUL thresholds"""
        device_id = "TEST_005"

        # Critical threshold
        critical_data = self.sample_sensor_data.copy()
        critical_data['current_mean'] = [15.0, 15.5, 15.2]
        critical_data['temperature_mean'] = [95.0, 97.0, 96.0]

        result = self.predictor.predict_rul(critical_data, device_id)
        # Should be critical or warning due to high stress
        self.assertIn(result.health_status, ["critical", "warning"])

    def test_normalize_features_without_params(self):
        """Test feature normalization without loaded parameters"""
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)
        normalized = self.predictor._normalize_features(features)

        # Without normalization params, should return unchanged
        np.testing.assert_array_equal(features, normalized)

    def test_normalize_features_with_params(self):
        """Test feature normalization with loaded parameters"""
        self.predictor.feature_mean = np.array([5.0, 2.0, 2.5, 2.0, 50.0, 0.5])
        self.predictor.feature_std = np.array([2.0, 1.0, 1.0, 1.0, 10.0, 0.2])

        features = np.array([7.0, 3.0, 3.5, 3.0, 60.0, 0.7], dtype=np.float32)
        normalized = self.predictor._normalize_features(features)

        expected = (features - self.predictor.feature_mean) / (self.predictor.feature_std + 1e-8)
        np.testing.assert_array_almost_equal(normalized, expected, decimal=5)

    def test_buffer_size_management(self):
        """Test that data buffer doesn't grow unbounded"""
        device_id = "TEST_006"
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        # Add many samples (more than 2 * sequence_length)
        for i in range(50):
            self.predictor._build_sequence(device_id, features * (i + 1))

        # Buffer should be capped at 2 * sequence_length
        max_size = self.predictor.sequence_length * 2
        self.assertLessEqual(len(self.predictor.data_buffer[device_id]), max_size)

    def test_multiple_devices(self):
        """Test handling multiple devices simultaneously"""
        device_ids = ["TEST_007", "TEST_008", "TEST_009"]
        features = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        # Add data for multiple devices
        for device_id in device_ids:
            for _ in range(10):
                self.predictor._build_sequence(device_id, features)

        # All devices should have buffers
        for device_id in device_ids:
            self.assertIn(device_id, self.predictor.data_buffer)
            self.assertEqual(len(self.predictor.data_buffer[device_id]), 10)


class TestGlobalPredictor(unittest.TestCase):
    """Test global predictor singleton"""

    def test_get_rul_predictor_singleton(self):
        """Test that get_rul_predictor returns singleton instance"""
        predictor1 = get_rul_predictor()
        predictor2 = get_rul_predictor()

        self.assertIs(predictor1, predictor2)

    def test_get_rul_predictor_returns_instance(self):
        """Test that get_rul_predictor returns valid instance"""
        predictor = get_rul_predictor()

        self.assertIsInstance(predictor, ONNXRULPredictor)


class TestModelMetadata(unittest.TestCase):
    """Test ModelMetadata dataclass"""

    def test_metadata_creation(self):
        """Test creating ModelMetadata instance"""
        metadata = ModelMetadata(
            model_path="models/test_model.onnx",
            model_version="1.0.0",
            model_type="LSTM",
            input_shape=(1, 50, 6),
            output_shape=(1, 1),
            feature_names=["current", "vib_x", "vib_y", "vib_z", "temp", "load"],
            training_date="2025-12-09",
            performance_metrics={"mae": 8.5, "rmse": 12.3}
        )

        self.assertEqual(metadata.model_version, "1.0.0")
        self.assertEqual(metadata.model_type, "LSTM")
        self.assertEqual(len(metadata.feature_names), 6)
        self.assertEqual(metadata.performance_metrics["mae"], 8.5)


class TestRULPrediction(unittest.TestCase):
    """Test RULPrediction dataclass"""

    def test_rul_prediction_creation(self):
        """Test creating RULPrediction instance"""
        prediction = RULPrediction(
            predicted_rul_hours=1250.5,
            confidence=0.85,
            health_status="normal",
            contributing_factors=["Normal operating conditions"],
            model_version="1.0.0",
            raw_prediction=1250.5,
            uncertainty=50.2
        )

        self.assertAlmostEqual(prediction.predicted_rul_hours, 1250.5)
        self.assertEqual(prediction.confidence, 0.85)
        self.assertEqual(prediction.health_status, "normal")
        self.assertEqual(prediction.uncertainty, 50.2)


if __name__ == '__main__':
    unittest.main()
