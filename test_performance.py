"""Performance tests for MODAX API endpoints"""
import unittest
import sys
import os
import time
import statistics
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add paths to system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-control-layer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-ai-layer'))

from data_aggregator import DataAggregator, SensorReading
from anomaly_detector import StatisticalAnomalyDetector
from wear_predictor import SimpleWearPredictor
from optimizer import OptimizationRecommender


class TestAPIPerformance(unittest.TestCase):
    """Performance tests for API operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = DataAggregator(window_size_seconds=10)
        self.anomaly_detector = StatisticalAnomalyDetector()
        self.wear_predictor = SimpleWearPredictor()
        self.optimizer = OptimizationRecommender()
        self.device_id = "perf_test_device"
        
        # Add baseline data
        for i in range(100):
            reading = SensorReading(
                timestamp=int((time.time() - (100 - i) * 0.1) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
    
    def test_data_aggregation_performance(self):
        """Test data aggregation performance"""
        iterations = 100
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            aggregated = self.aggregator.aggregate_for_ai(self.device_id)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)  # Convert to ms
            self.assertIsNotNone(aggregated)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        print(f"\nData Aggregation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 50, "Average aggregation time should be < 50ms")
        self.assertLess(p95_time, 100, "P95 aggregation time should be < 100ms")
    
    def test_anomaly_detection_performance(self):
        """Test anomaly detection performance"""
        iterations = 100
        times = []
        
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        
        for i in range(iterations):
            start_time = time.time()
            current_anomaly = self.anomaly_detector.detect_current_anomaly(
                aggregated.current_mean, aggregated.current_max, self.device_id
            )
            temp_anomaly = self.anomaly_detector.detect_temperature_anomaly(
                aggregated.temperature_mean, aggregated.temperature_max, self.device_id
            )
            vib_anomaly = self.anomaly_detector.detect_vibration_anomaly(
                aggregated.vibration_mean, aggregated.vibration_max, self.device_id
            )
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        print(f"\nAnomaly Detection Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 10, "Average anomaly detection should be < 10ms")
        self.assertLess(p95_time, 20, "P95 anomaly detection should be < 20ms")
    
    def test_wear_prediction_performance(self):
        """Test wear prediction performance"""
        iterations = 100
        times = []
        
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
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
        
        for i in range(iterations):
            start_time = time.time()
            wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)
            self.assertIsNotNone(wear_prediction)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        print(f"\nWear Prediction Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 15, "Average wear prediction should be < 15ms")
        self.assertLess(p95_time, 30, "P95 wear prediction should be < 30ms")
    
    def test_optimization_recommendation_performance(self):
        """Test optimization recommendation performance"""
        iterations = 100
        times = []
        
        aggregated = self.aggregator.aggregate_for_ai(self.device_id)
        sensor_data = {
            "device_id": self.device_id,
            "current_mean": aggregated.current_mean,
            "current_max": aggregated.current_max,
            "vibration_mean": aggregated.vibration_mean,
            "vibration_max": aggregated.vibration_max,
            "temperature_mean": aggregated.temperature_mean,
            "temperature_max": aggregated.temperature_max
        }
        
        for i in range(iterations):
            start_time = time.time()
            recommendations = self.optimizer.recommend_optimizations(sensor_data)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)
            self.assertIsNotNone(recommendations)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        print(f"\nOptimization Recommendation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 10, "Average optimization should be < 10ms")
        self.assertLess(p95_time, 20, "P95 optimization should be < 20ms")
    
    def test_complete_ai_analysis_pipeline_performance(self):
        """Test complete AI analysis pipeline performance"""
        iterations = 50
        times = []
        
        for i in range(iterations):
            # Add new data
            reading = SensorReading(
                timestamp=int(time.time() * 1000),
                device_id=self.device_id,
                motor_currents=[5.0 + i * 0.01, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0 + i * 0.05, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
            
            start_time = time.time()
            
            # Complete pipeline
            aggregated = self.aggregator.aggregate_for_ai(self.device_id)
            
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
            
            # All AI analyses
            current_anomaly = self.anomaly_detector.detect_current_anomaly(
                aggregated.current_mean, aggregated.current_max, self.device_id
            )
            wear_prediction = self.wear_predictor.predict_wear(sensor_data, self.device_id)
            recommendations = self.optimizer.recommend_optimizations(sensor_data)
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        print(f"\nComplete AI Pipeline Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 100, "Average complete pipeline should be < 100ms")
        self.assertLess(p95_time, 150, "P95 complete pipeline should be < 150ms")
    
    def test_concurrent_device_processing_performance(self):
        """Test concurrent processing of multiple devices"""
        num_devices = 10
        num_iterations = 20
        
        # Add data for all devices
        devices = [f"device_{i:03d}" for i in range(num_devices)]
        for device_id in devices:
            for i in range(50):
                reading = SensorReading(
                    timestamp=int((time.time() - (50 - i) * 0.1) * 1000),
                    device_id=device_id,
                    motor_currents=[5.0, 5.1, 4.9],
                    vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                    temperatures=[45.0, 46.0, 44.5]
                )
                self.aggregator.add_sensor_reading(reading)
        
        def process_device(device_id):
            """Process a single device"""
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            sensor_data = {
                "device_id": device_id,
                "time_window_start": aggregated.time_window_start,
                "time_window_end": aggregated.time_window_end,
                "current_mean": aggregated.current_mean,
                "current_max": aggregated.current_max,
                "vibration_mean": aggregated.vibration_mean,
                "vibration_max": aggregated.vibration_max,
                "temperature_mean": aggregated.temperature_mean,
                "temperature_max": aggregated.temperature_max
            }
            wear_prediction = self.wear_predictor.predict_wear(sensor_data, device_id)
            return wear_prediction
        
        times = []
        for iteration in range(num_iterations):
            start_time = time.time()
            
            # Process all devices concurrently
            with ThreadPoolExecutor(max_workers=num_devices) as executor:
                futures = [executor.submit(process_device, device_id) for device_id in devices]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
            
            self.assertEqual(len(results), num_devices)
        
        avg_time = statistics.mean(times)
        throughput = num_devices / (avg_time / 1000)
        
        print(f"\nConcurrent Device Processing Performance:")
        print(f"  Devices: {num_devices}")
        print(f"  Average time: {avg_time:.2f}ms")
        print(f"  Throughput: {throughput:.1f} devices/second")
        
        # Performance assertions
        self.assertLess(avg_time, 500, f"Processing {num_devices} devices should be < 500ms")
        self.assertGreater(throughput, 10, "Throughput should be > 10 devices/second")
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable under sustained load"""
        import gc
        import sys
        
        # Force garbage collection
        gc.collect()
        
        initial_objects = len(gc.get_objects())
        
        # Simulate sustained load
        for i in range(1000):
            reading = SensorReading(
                timestamp=int((time.time() + i * 0.01) * 1000),
                device_id=self.device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            self.aggregator.add_sensor_reading(reading)
            
            if i % 100 == 0:
                aggregated = self.aggregator.aggregate_for_ai(self.device_id)
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
                self.wear_predictor.predict_wear(sensor_data, self.device_id)
        
        # Force garbage collection again
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        print(f"\nMemory Stability Test:")
        print(f"  Initial objects: {initial_objects}")
        print(f"  Final objects: {final_objects}")
        print(f"  Object growth: {object_growth}")
        
        # Memory growth should be reasonable
        # Allow for some growth but not excessive
        self.assertLess(object_growth, 1000, "Object growth should be < 1000 objects")


class TestDataAggregationScalability(unittest.TestCase):
    """Test scalability of data aggregation"""
    
    def test_large_data_volume_handling(self):
        """Test handling of large data volumes"""
        aggregator = DataAggregator(window_size_seconds=60)
        device_id = "scale_test_device"
        
        num_readings = 10000
        start_time = time.time()
        
        for i in range(num_readings):
            reading = SensorReading(
                timestamp=int((time.time() - (num_readings - i) * 0.01) * 1000),
                device_id=device_id,
                motor_currents=[5.0, 5.1, 4.9],
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=[45.0, 46.0, 44.5]
            )
            aggregator.add_sensor_reading(reading)
        
        insertion_time = time.time() - start_time
        
        # Test aggregation
        agg_start = time.time()
        aggregated = aggregator.aggregate_for_ai(device_id)
        agg_time = time.time() - agg_start
        
        print(f"\nLarge Volume Handling:")
        print(f"  Readings: {num_readings}")
        print(f"  Insertion time: {insertion_time:.2f}s")
        print(f"  Insertion rate: {num_readings/insertion_time:.0f} readings/second")
        print(f"  Aggregation time: {agg_time*1000:.2f}ms")
        
        self.assertIsNotNone(aggregated)
        self.assertLess(agg_time, 1.0, "Aggregation should complete in < 1 second")
        self.assertGreater(num_readings/insertion_time, 1000, "Should handle > 1000 readings/second")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
