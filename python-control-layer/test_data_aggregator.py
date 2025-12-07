"""Unit tests for Data Aggregator module"""
import unittest
import time
from data_aggregator import (
    DataAggregator, SensorReading, SafetyStatus
)


class TestSensorReading(unittest.TestCase):
    """Tests for SensorReading dataclass"""

    def test_from_json(self):
        """Test creating SensorReading from JSON"""
        json_str = '''{
            "timestamp": 1234567890000,
            "device_id": "device_001",
            "motor_currents": [5.5, 5.3, 5.4],
            "vibration": {"x": 1.2, "y": 1.3, "z": 1.1, "magnitude": 2.1},
            "temperatures": [45.0, 46.5, 44.8]
        }'''

        reading = SensorReading.from_json(json_str)

        self.assertEqual(reading.timestamp, 1234567890000)
        self.assertEqual(reading.device_id, "device_001")
        self.assertEqual(reading.motor_currents, [5.5, 5.3, 5.4])
        self.assertEqual(reading.vibration['magnitude'], 2.1)
        self.assertEqual(len(reading.temperatures), 3)


class TestSafetyStatus(unittest.TestCase):
    """Tests for SafetyStatus dataclass"""

    def test_from_json(self):
        """Test creating SafetyStatus from JSON"""
        json_str = '''{
            "timestamp": 1234567890000,
            "device_id": "device_001",
            "emergency_stop": false,
            "door_closed": true,
            "overload_detected": false,
            "temperature_ok": true
        }'''

        status = SafetyStatus.from_json(json_str)

        self.assertEqual(status.device_id, "device_001")
        self.assertFalse(status.emergency_stop)
        self.assertTrue(status.door_closed)

    def test_is_safe_all_ok(self):
        """Test is_safe returns True when all conditions are OK"""
        status = SafetyStatus(
            timestamp=time.time() * 1000,
            device_id="device_001",
            emergency_stop=False,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )

        self.assertTrue(status.is_safe())

    def test_is_safe_emergency_stop(self):
        """Test is_safe returns False when emergency stop is active"""
        status = SafetyStatus(
            timestamp=time.time() * 1000,
            device_id="device_001",
            emergency_stop=True,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )

        self.assertFalse(status.is_safe())


class TestDataAggregator(unittest.TestCase):
    """Tests for DataAggregator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = DataAggregator(window_size_seconds=10, max_points=100)
        self.device_id = "test_device_001"

    def _create_test_reading(self, timestamp_ms=None):
        """Helper to create a test sensor reading"""
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        return SensorReading(
            timestamp=timestamp_ms,
            device_id=self.device_id,
            motor_currents=[5.0, 5.1, 4.9],
            vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            temperatures=[45.0, 46.0, 44.5]
        )

    def test_add_sensor_reading(self):
        """Test adding sensor readings"""
        reading = self._create_test_reading()
        self.aggregator.add_sensor_reading(reading)

        self.assertIn(self.device_id, self.aggregator.sensor_data)
        self.assertEqual(len(self.aggregator.sensor_data[self.device_id]), 1)

    def test_update_safety_status(self):
        """Test updating safety status"""
        status = SafetyStatus(
            timestamp=time.time() * 1000,
            device_id=self.device_id,
            emergency_stop=False,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )

        self.aggregator.update_safety_status(status)

        retrieved = self.aggregator.get_latest_safety_status(self.device_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.device_id, self.device_id)

    def test_is_system_safe_no_devices(self):
        """Test is_system_safe returns False when no devices registered"""
        self.assertFalse(self.aggregator.is_system_safe())

    def test_is_system_safe_all_ok(self):
        """Test is_system_safe returns True when all devices are safe"""
        status = SafetyStatus(
            timestamp=time.time() * 1000,
            device_id=self.device_id,
            emergency_stop=False,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )
        self.aggregator.update_safety_status(status)

        self.assertTrue(self.aggregator.is_system_safe())

    def test_aggregate_for_ai(self):
        """Test aggregating data for AI analysis"""
        # Add multiple readings
        current_time_ms = int(time.time() * 1000)
        for i in range(5):
            reading = SensorReading(
                timestamp=current_time_ms - (i * 1000),
                device_id=self.device_id,
                motor_currents=[5.0 + i * 0.1, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0 + i, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)

        # Aggregate
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)

        self.assertIsNotNone(aggregated)
        self.assertEqual(aggregated.device_id, self.device_id)
        self.assertEqual(aggregated.sample_count, 5)
        self.assertEqual(len(aggregated.current_mean), 3)
        self.assertIn('magnitude', aggregated.vibration_mean)

    def test_aggregate_for_ai_no_data(self):
        """Test aggregating when no data available"""
        aggregated = self.aggregator.aggregate_for_ai("nonexistent_device")
        self.assertIsNone(aggregated)

    def test_get_recent_readings(self):
        """Test getting recent readings"""
        # Add readings
        for i in range(10):
            reading = self._create_test_reading()
            self.aggregator.add_sensor_reading(reading)

        recent = self.aggregator.get_recent_readings(self.device_id, count=5)

        self.assertEqual(len(recent), 5)

    def test_get_device_ids(self):
        """Test getting all device IDs"""
        devices = ["device_001", "device_002", "device_003"]

        for device_id in devices:
            reading = SensorReading(
                timestamp=int(time.time() * 1000),
                device_id=device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)

        device_ids = self.aggregator.get_device_ids()

        self.assertEqual(len(device_ids), 3)
        for device_id in devices:
            self.assertIn(device_id, device_ids)


if __name__ == '__main__':
    unittest.main()
