"""End-to-end tests for complete MODAX data flow chain"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import time
import asyncio

# Add paths to system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-control-layer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-ai-layer'))

from data_aggregator import DataAggregator, SensorReading, SafetyStatus
from anomaly_detector import StatisticalAnomalyDetector
from wear_predictor import SimpleWearPredictor
from optimizer import OptimizationRecommender


class TestEndToEndDataFlow(unittest.TestCase):
    """End-to-end tests for complete MODAX data flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = DataAggregator(window_size_seconds=10)
        self.anomaly_detector = StatisticalAnomalyDetector()
        self.wear_predictor = SimpleWearPredictor()
        self.device_id = "test_device_001"
    
    def test_complete_flow_normal_operation(self):
        """Test complete data flow under normal operating conditions"""
        # Step 1: Simulate sensor data collection
        for i in range(10):
            reading = SensorReading(
                timestamp=int((time.time() - (10 - i)) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0 + i * 0.05, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0 + i * 0.5, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Aggregate data for AI analysis
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        
        self.assertIsNotNone(aggregated)
        self.assertGreaterEqual(aggregated.sample_count, 9)  # Allow for timing variance
        
        # Step 3: Perform anomaly detection
        current_anomaly = self.anomaly_detector.detect_current_anomaly(
            aggregated.current_mean, 
            aggregated.current_max,
            self.device_id
        )
        
        vibration_anomaly = self.anomaly_detector.detect_vibration_anomaly(
            aggregated.vibration_mean,
            aggregated.vibration_max,
            self.device_id
        )
        
        temperature_anomaly = self.anomaly_detector.detect_temperature_anomaly(
            aggregated.temperature_mean,
            aggregated.temperature_max,
            self.device_id
        )
        
        # Under normal conditions, no anomalies should be detected
        self.assertFalse(current_anomaly.is_anomaly)
        self.assertFalse(vibration_anomaly.is_anomaly)
        self.assertFalse(temperature_anomaly.is_anomaly)
        
        # Step 4: Predict wear
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": aggregated.time_window_start,
            "time_window_end": aggregated.time_window_end,
            "current_mean": aggregated.current_mean,
            "current_max": aggregated.current_max,
            "vibration_mean": aggregated.vibration_mean,
            "vibration_max": aggregated.vibration_max,
            "temperature_mean": aggregated.temperature_mean,
            "temperature_max": aggregated.temperature_max
        }
        
        wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
        
        # Wear should be low under normal conditions
        self.assertLess(wear_prediction.wear_level, 0.1)
        self.assertGreater(wear_prediction.estimated_remaining_hours, 0)
        self.assertGreater(wear_prediction.confidence, 0.5)
    
    def test_complete_flow_high_stress_operation(self):
        """Test complete data flow under high stress conditions"""
        # Step 1: Simulate high stress sensor data
        for i in range(10):
            reading = SensorReading(
                timestamp=int((time.time() - (10 - i)) * 1000),
                device_id=self.device_id,
                motor_currents=[10.0, 10.5, 9.8],  # High current
                vibration={"x": 8.0, "y": 8.5, "z": 7.5, "magnitude": 12.0},  # High vibration
                temperatures=[70.0, 71.0, 69.5]  # High temperature
            )
            self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Aggregate data
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        self.assertIsNotNone(aggregated)
        
        # Step 3: Anomaly detection should detect issues
        current_anomaly = self.anomaly_detector.detect_current_anomaly(
            aggregated.current_mean,
            aggregated.current_max,
            self.device_id
        )
        
        vibration_anomaly = self.anomaly_detector.detect_vibration_anomaly(
            aggregated.vibration_mean,
            aggregated.vibration_max,
            self.device_id
        )
        
        temperature_anomaly = self.anomaly_detector.detect_temperature_anomaly(
            aggregated.temperature_mean,
            aggregated.temperature_max,
            self.device_id
        )
        
        # High stress should trigger anomalies
        self.assertTrue(current_anomaly.is_anomaly or 
                       vibration_anomaly.is_anomaly or 
                       temperature_anomaly.is_anomaly)
        
        # Step 4: Wear prediction should show higher wear
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": aggregated.time_window_start,
            "time_window_end": aggregated.time_window_end,
            "current_mean": aggregated.current_mean,
            "current_max": aggregated.current_max,
            "vibration_mean": aggregated.vibration_mean,
            "vibration_max": aggregated.vibration_max,
            "temperature_mean": aggregated.temperature_mean,
            "temperature_max": aggregated.temperature_max
        }
        
        wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
        
        # Should have contributing factors under stress
        self.assertGreater(len(wear_prediction.contributing_factors), 0)
    
    def test_complete_flow_with_safety_check(self):
        """Test complete flow including safety system integration"""
        # Step 1: Add sensor data
        reading = SensorReading(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            motor_currents=[5.0, 5.1, 4.9],
            vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            temperatures=[45.0, 46.0, 44.5]
        )
        self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Update safety status
        safe_status = SafetyStatus(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            emergency_stop=False,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )
        self.aggregator.update_safety_status(safe_status)
        
        # Step 3: Verify system is safe before proceeding
        self.assertTrue(self.aggregator.is_system_safe())
        
        # Step 4: Simulate unsafe condition
        unsafe_status = SafetyStatus(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            emergency_stop=True,  # Emergency stop activated
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )
        self.aggregator.update_safety_status(unsafe_status)
        
        # System should now be unsafe
        self.assertFalse(self.aggregator.is_system_safe())
    
    def test_multi_device_flow(self):
        """Test data flow with multiple devices"""
        devices = ["device_001", "device_002", "device_003"]
        
        # Step 1: Add data for multiple devices
        for device_id in devices:
            for i in range(5):
                reading = SensorReading(
                    timestamp=int((time.time() - (5 - i)) * 1000),
                    device_id=device_id,
                    motor_currents=[5.0, 5.1, 4.9],
                    vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                    temperatures=[45.0, 46.0, 44.5]
                )
                self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Verify all devices are tracked
        device_ids = self.aggregator.get_device_ids()
        self.assertEqual(len(device_ids), 3)
        for device_id in devices:
            self.assertIn(device_id, device_ids)
        
        # Step 3: Aggregate and analyze each device independently
        for device_id in devices:
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            self.assertIsNotNone(aggregated)
            self.assertEqual(aggregated.device_id, device_id)
            self.assertEqual(aggregated.sample_count, 5)
    
    def test_baseline_learning_over_time(self):
        """Test that anomaly detector learns baseline over time"""
        # Phase 1: Normal operation - establish baseline
        for i in range(20):
            reading = SensorReading(
                timestamp=int((time.time() - (20 - i)) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
            
            if i % 5 == 0:  # Update baseline periodically
                aggregated = self.aggregator.aggregate_for_ai(self.device_id)
                if aggregated:
                    sensor_data = {
                        "device_id": self.device_id,
                        "current_mean": aggregated.current_mean,
                        "vibration_mean": aggregated.vibration_mean,
                        "temperature_mean": aggregated.temperature_mean
                    }
                    self.anomaly_detector.update_baseline(self.device_id, sensor_data)
        
        # Baseline should now be established
        self.assertIn(self.device_id, self.anomaly_detector.baseline_stats)
        
        # Phase 2: Significantly different operation should trigger anomaly
        reading = SensorReading(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            motor_currents=[10.0, 10.1, 9.9],  # Much higher than baseline
            vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            temperatures=[45.0, 46.0, 44.5]
        )
        self.aggregator.add_sensor_reading(reading)
        
        aggregated = self.aggregator.aggregate_for_ai(self.device_id, window_seconds=1)
        if aggregated:
            anomaly = self.anomaly_detector.detect_current_anomaly(
                aggregated.current_mean,
                aggregated.current_max,
                self.device_id
            )
            # Deviation from baseline should be detected
            self.assertTrue(anomaly.is_anomaly)


    def test_complete_ai_pipeline(self):
        """Test complete AI pipeline with anomaly detection, wear prediction, and optimization"""
        # Step 1: Simulate extended operation period
        for i in range(50):
            reading = SensorReading(
                timestamp=int((time.time() - (50 - i)) * 1000),
                device_id=self.device_id,
                motor_currents=[6.0 + (i * 0.1) % 2, 6.1, 5.9],
                vibration={"x": 1.5 + (i * 0.05) % 1, "y": 1.6, "z": 1.4, "magnitude": 2.5},
                temperatures=[50.0 + (i * 0.2) % 5, 51.0, 49.5]
            )
            self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Aggregate data
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        self.assertIsNotNone(aggregated)
        
        # Step 3: Run all AI analyses
        sensor_data = {
            "device_id": self.device_id,
            "time_window_start": aggregated.time_window_start,
            "time_window_end": aggregated.time_window_end,
            "current_mean": aggregated.current_mean,
            "current_max": aggregated.current_max,
            "vibration_mean": aggregated.vibration_mean,
            "vibration_max": aggregated.vibration_max,
            "temperature_mean": aggregated.temperature_mean,
            "temperature_max": aggregated.temperature_max
        }
        
        # Anomaly detection
        current_anomaly = self.anomaly_detector.detect_current_anomaly(
            aggregated.current_mean, aggregated.current_max, self.device_id
        )
        
        # Wear prediction
        wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
        
        # Optimization recommendations
        optimizer = OptimizationRecommender()
        recommendations = optimizer.recommend_optimizations(sensor_data)
        
        # Verify all components returned results
        self.assertIsNotNone(current_anomaly)
        self.assertIsNotNone(wear_prediction)
        self.assertIsNotNone(recommendations)
        self.assertIsInstance(recommendations, list)
    
    def test_data_flow_with_gaps(self):
        """Test system behavior with data gaps (simulating network interruptions)"""
        # Step 1: Add first batch of data
        for i in range(5):
            reading = SensorReading(
                timestamp=int((time.time() - 20 + i) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Simulate data gap (no data for 10 seconds)
        
        # Step 3: Add second batch of data
        for i in range(5):
            reading = SensorReading(
                timestamp=int((time.time() + i) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
        
        # Step 4: System should still be able to aggregate recent data
        aggregated = self.aggregator.aggregate_for_ai(self.device_id, window_seconds=5)
        self.assertIsNotNone(aggregated)
        
        # Should have the recent 5 samples
        self.assertEqual(aggregated.sample_count, 5)
    
    def test_concurrent_device_analysis(self):
        """Test concurrent analysis of multiple devices"""
        num_devices = 5
        devices = [f"device_{i:03d}" for i in range(num_devices)]
        
        # Step 1: Add data for all devices simultaneously
        for i in range(10):
            for device_id in devices:
                reading = SensorReading(
                    timestamp=int((time.time() - (10 - i)) * 1000),
                    device_id=device_id,
                    motor_currents=[5.0 + i * 0.1, 5.1, 4.9],
                    vibration={"x": 1.0 + i * 0.05, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                    temperatures=[45.0 + i * 0.3, 46.0, 44.5]
                )
                self.aggregator.add_sensor_reading(reading)
        
        # Step 2: Analyze all devices
        results = {}
        for device_id in devices:
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            self.assertIsNotNone(aggregated)
            
            sensor_data = {
                "device_id": device_id,
                "current_mean": aggregated.current_mean,
                "temperature_mean": aggregated.temperature_mean,
                "vibration_mean": aggregated.vibration_mean
            }
            
            wear_prediction = self.wear_predictor.predict_wear(
                {**sensor_data, 
                 "time_window_start": aggregated.time_window_start,
                 "time_window_end": aggregated.time_window_end,
                 "current_max": aggregated.current_max,
                 "vibration_max": aggregated.vibration_max,
                 "temperature_max": aggregated.temperature_max}, 
                device_id
            )
            
            results[device_id] = {
                "aggregated": aggregated,
                "wear": wear_prediction
            }
        
        # Step 3: Verify all devices were analyzed
        self.assertEqual(len(results), num_devices)
        for device_id in devices:
            self.assertIn(device_id, results)
            self.assertGreater(results[device_id]["aggregated"].sample_count, 0)
    
    def test_gradual_wear_accumulation(self):
        """Test wear accumulation over extended operation"""
        # Simulate 100 measurement cycles
        for cycle in range(100):
            # Gradually increasing stress
            stress_factor = 1.0 + (cycle / 100.0) * 0.5
            
            reading = SensorReading(
                timestamp=int((time.time() - (100 - cycle)) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0 * stress_factor, 5.1 * stress_factor, 4.9 * stress_factor],
                vibration={
                    "x": 1.0 * stress_factor, 
                    "y": 1.1 * stress_factor, 
                    "z": 0.9 * stress_factor, 
                    "magnitude": 1.8 * stress_factor
                },
                temperatures=[45.0 + cycle * 0.2, 46.0 + cycle * 0.2, 44.5 + cycle * 0.2]
            )
            self.aggregator.add_sensor_reading(reading)
            
            # Analyze every 10 cycles
            if cycle % 10 == 0:
                aggregated = self.aggregator.aggregate_for_ai(self.device_id)
                if aggregated:
                    sensor_data = {
                        "device_id": self.device_id,
                        "time_window_start": aggregated.time_window_start,
                        "time_window_end": aggregated.time_window_end,
                        "current_mean": aggregated.current_mean,
                        "current_max": aggregated.current_max,
                        "vibration_mean": aggregated.vibration_mean,
                        "vibration_max": aggregated.vibration_max,
                        "temperature_mean": aggregated.temperature_mean,
                        "temperature_max": aggregated.temperature_max
                    }
                    wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
                    
                    # Early cycles should show low wear
                    if cycle < 20:
                        self.assertLess(wear_prediction.wear_level, 0.3)
        
        # Final check - wear should have accumulated
        final_aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        final_sensor_data = {
            "device_id": self.device_id,
            "time_window_start": final_aggregated.time_window_start,
            "time_window_end": final_aggregated.time_window_end,
            "current_mean": final_aggregated.current_mean,
            "current_max": final_aggregated.current_max,
            "vibration_mean": final_aggregated.vibration_mean,
            "vibration_max": final_aggregated.vibration_max,
            "temperature_mean": final_aggregated.temperature_mean,
            "temperature_max": final_aggregated.temperature_max
        }
        final_wear = self.wear_predictor.predict_wear(final_sensor_data, self.device_id)
        
        # Wear should be higher after extended high-stress operation
        self.assertGreater(final_wear.wear_level, 0.0)
        self.assertGreater(len(final_wear.contributing_factors), 0)
    
    def test_emergency_shutdown_flow(self):
        """Test complete flow when emergency shutdown is triggered"""
        # Step 1: Normal operation
        reading = SensorReading(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            motor_currents=[5.0, 5.1, 4.9],
            vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
            temperatures=[45.0, 46.0, 44.5]
        )
        self.aggregator.add_sensor_reading(reading)
        
        safe_status = SafetyStatus(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            emergency_stop=False,
            door_closed=True,
            overload_detected=False,
            temperature_ok=True
        )
        self.aggregator.update_safety_status(safe_status)
        
        # Verify system is safe
        self.assertTrue(self.aggregator.is_system_safe())
        
        # Step 2: Simulate critical condition triggering emergency shutdown
        critical_reading = SensorReading(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            motor_currents=[15.0, 15.1, 14.9],  # Very high current
            vibration={"x": 10.0, "y": 10.1, "z": 9.9, "magnitude": 15.0},  # Extreme vibration
            temperatures=[95.0, 96.0, 94.5]  # Dangerous temperature
        )
        self.aggregator.add_sensor_reading(critical_reading)
        
        # Step 3: Update safety status to emergency
        emergency_status = SafetyStatus(
            timestamp=int(time.time() * 1000),
            device_id=self.device_id,
            emergency_stop=True,
            door_closed=True,
            overload_detected=True,
            temperature_ok=False
        )
        self.aggregator.update_safety_status(emergency_status)
        
        # Step 4: Verify system is now unsafe
        self.assertFalse(self.aggregator.is_system_safe())
        
        # Step 5: AI analysis should detect multiple issues
        aggregated = self.aggregator.aggregate_for_ai(self.device_id, window_seconds=1)
        if aggregated:
            current_anomaly = self.anomaly_detector.detect_current_anomaly(
                aggregated.current_mean, aggregated.current_max, self.device_id
            )
            temp_anomaly = self.anomaly_detector.detect_temperature_anomaly(
                aggregated.temperature_mean, aggregated.temperature_max, self.device_id
            )
            vib_anomaly = self.anomaly_detector.detect_vibration_anomaly(
                aggregated.vibration_mean, aggregated.vibration_max, self.device_id
            )
            
            # At least one anomaly should be detected
            self.assertTrue(
                current_anomaly.is_anomaly or 
                temp_anomaly.is_anomaly or 
                vib_anomaly.is_anomaly
            )


if __name__ == '__main__':
    unittest.main()
