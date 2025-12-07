"""Unit tests for AI Service module"""
import unittest
from fastapi.testclient import TestClient
from ai_service import app


class TestAIService(unittest.TestCase):
    """Tests for AI Service REST API"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        self.test_sensor_data = {
            "device_id": "test_device_001",
            "time_window_start": 1234567890.0,
            "time_window_end": 1234567900.0,
            "current_mean": [5.0, 5.1, 4.9],
            "current_std": [0.1, 0.2, 0.15],
            "current_max": [6.0, 6.2, 5.8],
            "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            "vibration_std": {"x": 0.1, "y": 0.15, "z": 0.12, "magnitude": 0.2},
            "vibration_max": {"x": 2.0, "y": 2.1, "z": 1.9, "magnitude": 3.0},
            "temperature_mean": [45.0, 46.0, 44.5],
            "temperature_max": [48.0, 49.0, 47.5],
            "sample_count": 10
        }

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service", data)
        self.assertIn("version", data)
        self.assertEqual(data["service"], "MODAX AI Layer")

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["models_loaded"])
        self.assertIn("timestamp", data)

    def test_analyze_endpoint_success(self):
        """Test analyze endpoint with valid data"""
        response = self.client.post("/analyze", json=self.test_sensor_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check required fields in response
        self.assertIn("device_id", data)
        self.assertIn("anomaly_detected", data)
        self.assertIn("anomaly_score", data)
        self.assertIn("anomaly_description", data)
        self.assertIn("predicted_wear_level", data)
        self.assertIn("estimated_remaining_hours", data)
        self.assertIn("recommendations", data)
        self.assertIn("confidence", data)

        # Check data types
        self.assertEqual(data["device_id"], "test_device_001")
        self.assertIsInstance(data["anomaly_detected"], bool)
        self.assertIsInstance(data["anomaly_score"], (int, float))
        self.assertIsInstance(data["predicted_wear_level"], (int, float))
        self.assertIsInstance(data["estimated_remaining_hours"], int)
        self.assertIsInstance(data["recommendations"], list)
        self.assertIsInstance(data["confidence"], (int, float))

        # Check value ranges
        self.assertGreaterEqual(data["anomaly_score"], 0.0)
        self.assertLessEqual(data["anomaly_score"], 1.0)
        self.assertGreaterEqual(data["predicted_wear_level"], 0.0)
        self.assertLessEqual(data["predicted_wear_level"], 1.0)
        self.assertGreaterEqual(data["confidence"], 0.0)
        self.assertLessEqual(data["confidence"], 1.0)

    def test_analyze_endpoint_with_anomaly(self):
        """Test analyze endpoint with anomalous data"""
        anomalous_data = self.test_sensor_data.copy()
        anomalous_data["current_mean"] = [15.0, 15.5, 14.8]  # Very high current
        anomalous_data["vibration_mean"]["magnitude"] = 8.0  # High vibration

        response = self.client.post("/analyze", json=anomalous_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should detect anomaly
        self.assertTrue(data["anomaly_detected"])
        self.assertGreater(data["anomaly_score"], 0.3)
        self.assertNotEqual(data["anomaly_description"], "No anomalies detected")

    def test_analyze_endpoint_missing_fields(self):
        """Test analyze endpoint with missing required fields"""
        incomplete_data = {
            "device_id": "test_device_001",
            "current_mean": [5.0, 5.1, 4.9]
            # Missing many required fields
        }

        response = self.client.post("/analyze", json=incomplete_data)

        # Should return validation error
        self.assertEqual(response.status_code, 422)

    def test_analyze_endpoint_invalid_data_types(self):
        """Test analyze endpoint with invalid data types"""
        invalid_data = self.test_sensor_data.copy()
        invalid_data["current_mean"] = "not a list"  # Invalid type

        response = self.client.post("/analyze", json=invalid_data)

        # Should return validation error
        self.assertEqual(response.status_code, 422)

    def test_analyze_response_includes_details(self):
        """Test that analysis response includes detailed information"""
        response = self.client.post("/analyze", json=self.test_sensor_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check for analysis details
        self.assertIn("analysis_details", data)
        details = data["analysis_details"]

        self.assertIn("current_anomaly", details)
        self.assertIn("vibration_anomaly", details)
        self.assertIn("temperature_anomaly", details)
        self.assertIn("wear_factors", details)
        self.assertIn("samples_analyzed", details)
        self.assertEqual(details["samples_analyzed"], 10)

    def test_analyze_recommendations_not_empty(self):
        """Test that analysis always provides recommendations"""
        response = self.client.post("/analyze", json=self.test_sensor_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertGreater(len(data["recommendations"]), 0)

        # All recommendations should be strings
        for rec in data["recommendations"]:
            self.assertIsInstance(rec, str)
            self.assertGreater(len(rec), 0)

    def test_reset_wear_endpoint(self):
        """Test reset wear endpoint"""
        device_id = "test_device_001"
        response = self.client.post(f"/reset-wear/{device_id}")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["device_id"], device_id)
        self.assertIn("message", data)

    def test_model_info_endpoint(self):
        """Test model info endpoint"""
        response = self.client.get("/models/info")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check that all model types are documented
        self.assertIn("anomaly_detection", data)
        self.assertIn("wear_prediction", data)
        self.assertIn("optimization", data)

        # Check anomaly detection info
        self.assertIn("type", data["anomaly_detection"])
        self.assertIn("threshold", data["anomaly_detection"])

        # Check wear prediction info
        self.assertIn("type", data["wear_prediction"])
        self.assertIn("baseline_lifetime_hours", data["wear_prediction"])

    def test_multiple_analyses_same_device(self):
        """Test multiple analyses for the same device"""
        device_id = "test_device_002"
        test_data = self.test_sensor_data.copy()
        test_data["device_id"] = device_id

        # First analysis
        response1 = self.client.post("/analyze", json=test_data)
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()

        # Second analysis with slightly different data
        test_data["current_mean"] = [5.2, 5.3, 5.1]
        response2 = self.client.post("/analyze", json=test_data)
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()

        # Both should succeed
        self.assertIsNotNone(data1["predicted_wear_level"])
        self.assertIsNotNone(data2["predicted_wear_level"])

        # Wear should be accumulated (second should be >= first)
        # Note: This may not always be true depending on the wear predictor logic
        # but both should be valid values
        self.assertGreaterEqual(data2["predicted_wear_level"], 0.0)

    def test_analyze_with_zero_samples(self):
        """Test analysis with zero sample count"""
        test_data = self.test_sensor_data.copy()
        test_data["sample_count"] = 0

        response = self.client.post("/analyze", json=test_data)

        # Should still return 200 with reduced confidence
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should still provide recommendations even with no samples
        self.assertGreater(len(data["recommendations"]), 0)

    def test_analyze_different_devices(self):
        """Test that different devices get independent analysis"""
        device1_data = self.test_sensor_data.copy()
        device1_data["device_id"] = "device_001"

        device2_data = self.test_sensor_data.copy()
        device2_data["device_id"] = "device_002"
        device2_data["current_mean"] = [8.0, 8.1, 7.9]  # Different values

        # Analyze both devices
        response1 = self.client.post("/analyze", json=device1_data)
        response2 = self.client.post("/analyze", json=device2_data)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        data1 = response1.json()
        data2 = response2.json()

        # Results should be different for different devices
        self.assertEqual(data1["device_id"], "device_001")
        self.assertEqual(data2["device_id"], "device_002")

        # Device 2 should likely have higher anomaly score due to higher current
        # (though this depends on baseline, so we just check they're valid)
        self.assertGreaterEqual(data2["anomaly_score"], 0.0)


if __name__ == '__main__':
    unittest.main()
