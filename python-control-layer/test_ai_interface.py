"""Unit tests for AI Interface module"""
import unittest
from unittest.mock import Mock, patch
import requests
from ai_interface import request_ai_analysis
from data_aggregator import AggregatedData


class TestAIInterface(unittest.TestCase):
    """Tests for AI Interface module"""

    def setUp(self):
        """Set up test fixtures"""
        self.device_id = "test_device_001"
        self.aggregated_data = AggregatedData(
            device_id=self.device_id,
            time_window_start=1234567890.0,
            time_window_end=1234567900.0,
            current_mean=[5.0, 5.1, 4.9],
            current_std=[0.1, 0.2, 0.15],
            current_max=[6.0, 6.2, 5.8],
            vibration_mean={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            vibration_std={"x": 0.1, "y": 0.15, "z": 0.12, "magnitude": 0.2},
            vibration_max={"x": 2.0, "y": 2.1, "z": 1.9, "magnitude": 3.0},
            temperature_mean=[45.0, 46.0, 44.5],
            temperature_max=[48.0, 49.0, 47.5],
            sample_count=10
        )

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_success(self, mock_post):
        """Test successful AI analysis request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "anomaly_detected": False,
            "anomaly_score": 0.2,
            "predicted_wear_level": 0.3,
            "recommendations": ["System operating normally"]
        }
        mock_post.return_value = mock_response

        # Call function
        result = request_ai_analysis(self.aggregated_data)

        # Assertions
        self.assertIsNotNone(result)
        self.assertFalse(result['anomaly_detected'])
        self.assertEqual(result['anomaly_score'], 0.2)

        # Verify request was made correctly
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        self.assertIn('json', call_kwargs)
        self.assertIn('timeout', call_kwargs)
        payload = call_kwargs['json']
        self.assertEqual(payload['device_id'], self.device_id)

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_http_error(self, mock_post):
        """Test AI analysis request with HTTP error"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Call function
        result = request_ai_analysis(self.aggregated_data)

        # Should return None on error
        self.assertIsNone(result)

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_connection_error(self, mock_post):
        """Test AI analysis request with connection error"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Call function
        result = request_ai_analysis(self.aggregated_data)

        # Should return None on connection error
        self.assertIsNone(result)

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_timeout(self, mock_post):
        """Test AI analysis request with timeout"""
        # Mock timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call function
        result = request_ai_analysis(self.aggregated_data)

        # Should return None on timeout
        self.assertIsNone(result)

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_payload_structure(self, mock_post):
        """Test that payload has correct structure"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        # Call function
        request_ai_analysis(self.aggregated_data)

        # Verify payload structure
        payload = mock_post.call_args[1]['json']

        # Check all required fields are present
        required_fields = [
            'device_id', 'time_window_start', 'time_window_end',
            'current_mean', 'current_std', 'current_max',
            'vibration_mean', 'vibration_std', 'vibration_max',
            'temperature_mean', 'temperature_max', 'sample_count'
        ]

        for field in required_fields:
            self.assertIn(field, payload)

        # Verify values match
        self.assertEqual(payload['device_id'], self.device_id)
        self.assertEqual(payload['sample_count'], 10)

    @patch('ai_interface.requests.post')
    def test_request_ai_analysis_general_exception(self, mock_post):
        """Test AI analysis request with general exception"""
        # Mock general exception
        mock_post.side_effect = Exception("Unexpected error")

        # Call function
        result = request_ai_analysis(self.aggregated_data)

        # Should return None on exception
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
