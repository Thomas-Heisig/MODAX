"""Unit tests for Anomaly Detector module"""
import unittest
from anomaly_detector import StatisticalAnomalyDetector, AnomalyResult


class TestAnomalyResult(unittest.TestCase):
    """Tests for AnomalyResult dataclass"""

    def test_creation(self):
        """Test creating AnomalyResult"""
        result = AnomalyResult(
            is_anomaly=True,
            score=0.85,
            description="High current detected",
            confidence=0.92
        )

        self.assertTrue(result.is_anomaly)
        self.assertEqual(result.score, 0.85)
        self.assertEqual(result.confidence, 0.92)


class TestStatisticalAnomalyDetector(unittest.TestCase):
    """Tests for StatisticalAnomalyDetector class"""

    def setUp(self):
        """Set up test fixtures"""
        self.detector = StatisticalAnomalyDetector(z_threshold=3.0)
        self.device_id = "test_device_001"

    def test_initialization(self):
        """Test detector initialization"""
        self.assertEqual(self.detector.z_threshold, 3.0)
        self.assertEqual(len(self.detector.baseline_stats), 0)

    def test_detect_current_anomaly_normal(self):
        """Test current anomaly detection with normal values"""
        current_mean = [5.0, 5.1, 4.9]
        current_max = [6.0, 6.2, 5.8]

        result = self.detector.detect_current_anomaly(
            current_mean, current_max, self.device_id
        )

        self.assertIsInstance(result, AnomalyResult)
        self.assertFalse(result.is_anomaly)

    def test_detect_current_anomaly_high_current(self):
        """Test detection of high current anomaly"""
        current_mean = [13.0, 13.5, 12.8]  # Above threshold
        current_max = [14.0, 14.5, 13.8]

        result = self.detector.detect_current_anomaly(
            current_mean, current_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertGreater(result.score, 0.5)

    def test_detect_current_anomaly_imbalance(self):
        """Test detection of current imbalance"""
        current_mean = [5.0, 8.5, 5.1]  # Significant imbalance
        current_max = [6.0, 9.5, 6.1]

        result = self.detector.detect_current_anomaly(
            current_mean, current_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertIn("imbalance", result.description.lower())

    def test_detect_vibration_anomaly_normal(self):
        """Test vibration anomaly detection with normal values"""
        vibration_mean = {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8}
        vibration_max = {"x": 2.0, "y": 2.1, "z": 1.9, "magnitude": 3.0}

        result = self.detector.detect_vibration_anomaly(
            vibration_mean, vibration_max, self.device_id
        )

        self.assertFalse(result.is_anomaly)

    def test_detect_vibration_anomaly_high(self):
        """Test detection of high vibration"""
        vibration_mean = {"x": 8.0, "y": 8.5, "z": 7.5, "magnitude": 12.0}
        vibration_max = {"x": 10.0, "y": 11.0, "z": 9.5, "magnitude": 15.0}

        result = self.detector.detect_vibration_anomaly(
            vibration_mean, vibration_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertGreater(result.score, 0.5)

    def test_detect_vibration_anomaly_imbalance(self):
        """Test detection of vibration axis imbalance"""
        vibration_mean = {"x": 1.0, "y": 5.0, "z": 0.9, "magnitude": 5.2}
        vibration_max = {"x": 2.0, "y": 7.0, "z": 1.9, "magnitude": 7.5}

        result = self.detector.detect_vibration_anomaly(
            vibration_mean, vibration_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertIn("imbalance", result.description.lower())

    def test_detect_temperature_anomaly_normal(self):
        """Test temperature anomaly detection with normal values"""
        temperature_mean = [45.0, 46.0, 44.5]
        temperature_max = [48.0, 49.0, 47.5]

        result = self.detector.detect_temperature_anomaly(
            temperature_mean, temperature_max, self.device_id
        )

        self.assertFalse(result.is_anomaly)

    def test_detect_temperature_anomaly_high(self):
        """Test detection of high temperature"""
        temperature_mean = [72.0, 73.0, 71.5]  # Above threshold
        temperature_max = [75.0, 76.0, 74.5]

        result = self.detector.detect_temperature_anomaly(
            temperature_mean, temperature_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertGreater(result.score, 0.5)
        self.assertIn("high", result.description.lower())

    def test_detect_temperature_anomaly_elevated(self):
        """Test detection of elevated temperature"""
        temperature_mean = [65.0, 66.0, 64.5]  # Elevated but not high
        temperature_max = [68.0, 69.0, 67.5]

        result = self.detector.detect_temperature_anomaly(
            temperature_mean, temperature_max, self.device_id
        )

        self.assertTrue(result.is_anomaly)
        self.assertIn("elevated", result.description.lower())

    def test_update_baseline(self):
        """Test updating baseline statistics"""
        sensor_data = {
            "device_id": self.device_id,
            "current_mean": [5.0, 5.1, 4.9],
            "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            "temperature_mean": [45.0, 46.0, 44.5]
        }

        self.detector.update_baseline(self.device_id, sensor_data)

        self.assertIn(self.device_id, self.detector.baseline_stats)
        self.assertIn('current_0', self.detector.baseline_stats[self.device_id])

    def test_detect_with_baseline(self):
        """Test anomaly detection with established baseline"""
        # Set baseline
        sensor_data = {
            "device_id": self.device_id,
            "current_mean": [5.0, 5.1, 4.9],
            "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            "temperature_mean": [45.0, 46.0, 44.5]
        }
        self.detector.update_baseline(self.device_id, sensor_data)

        # Test with values significantly different from baseline
        current_mean = [8.0, 8.1, 7.9]  # Much higher than baseline
        current_max = [9.0, 9.2, 8.8]

        result = self.detector.detect_current_anomaly(
            current_mean, current_max, self.device_id
        )

        # Should detect anomaly due to deviation from baseline
        self.assertTrue(result.is_anomaly)


if __name__ == '__main__':
    unittest.main()
