"""Load tests for multi-device scenarios in MODAX"""
import unittest
import sys
import os
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict

# Add paths to system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-control-layer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-ai-layer'))

from data_aggregator import DataAggregator, SensorReading
from anomaly_detector import StatisticalAnomalyDetector
from wear_predictor import SimpleWearPredictor
from test_utils import calculate_p95


@dataclass
class LoadTestResult:
    """Results from a load test"""
    total_time: float
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class TestMultiDeviceLoad(unittest.TestCase):
    """Load tests for multiple devices"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = DataAggregator(window_size_seconds=10)
        self.anomaly_detector = StatisticalAnomalyDetector()
        self.wear_predictor = SimpleWearPredictor()
    
    def _generate_sensor_reading(self, device_id: str, timestamp: float) -> SensorReading:
        """Generate a realistic sensor reading with some variance"""
        base_current = 5.0
        base_vibration = 1.5
        base_temp = 50.0
        
        # Add realistic variance
        variance = random.gauss(0, 0.1)
        
        return SensorReading(
            timestamp=int(timestamp * 1000),
            device_id=device_id,
            motor_currents=[
                base_current + variance,
                base_current + variance + 0.1,
                base_current + variance - 0.1
            ],
            vibration={
                "x": base_vibration + variance,
                "y": base_vibration + variance + 0.1,
                "z": base_vibration + variance - 0.1,
                "magnitude": base_vibration * 1.5
            },
            temperatures=[
                base_temp + variance * 2,
                base_temp + variance * 2 + 1.0,
                base_temp + variance * 2 - 1.0
            ]
        )
    
    def test_10_devices_sustained_load(self):
        """Test sustained load with 10 devices"""
        num_devices = 10
        duration_seconds = 10
        readings_per_second = 10  # Per device
        
        devices = [f"device_{i:03d}" for i in range(num_devices)]
        
        start_time = time.time()
        total_readings = 0
        
        print(f"\n=== Load Test: {num_devices} devices, {duration_seconds}s, {readings_per_second} readings/s/device ===")
        
        # Simulate sustained load
        elapsed = 0
        while elapsed < duration_seconds:
            iteration_start = time.time()
            
            for device_id in devices:
                reading = self._generate_sensor_reading(device_id, time.time())
                self.aggregator.add_sensor_reading(reading)
                total_readings += 1
            
            # Maintain reading rate
            iteration_time = time.time() - iteration_start
            sleep_time = (1.0 / readings_per_second) - iteration_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            elapsed = time.time() - start_time
        
        total_time = time.time() - start_time
        
        print(f"Total readings: {total_readings}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Throughput: {total_readings/total_time:.1f} readings/second")
        
        # Verify all devices have data
        device_ids = self.aggregator.get_device_ids()
        self.assertEqual(len(device_ids), num_devices)
        
        # Test aggregation for all devices
        for device_id in devices:
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            self.assertIsNotNone(aggregated)
            self.assertGreater(aggregated.sample_count, 0)
        
        # Performance assertions
        self.assertGreater(total_readings/total_time, 50, "Should sustain > 50 readings/second")
    
    def test_50_devices_concurrent_analysis(self):
        """Test concurrent analysis of 50 devices"""
        num_devices = 50
        readings_per_device = 20
        
        devices = [f"device_{i:03d}" for i in range(num_devices)]
        
        print(f"\n=== Load Test: {num_devices} devices concurrent analysis ===")
        
        # Populate data for all devices
        setup_start = time.time()
        for device_id in devices:
            for i in range(readings_per_device):
                reading = self._generate_sensor_reading(
                    device_id,
                    time.time() - (readings_per_device - i) * 0.1
                )
                self.aggregator.add_sensor_reading(reading)
        
        setup_time = time.time() - setup_start
        print(f"Setup time: {setup_time:.2f}s")
        print(f"Total readings: {num_devices * readings_per_device}")
        
        def analyze_device(device_id):
            """Analyze a single device"""
            try:
                start = time.time()
                
                aggregated = self.aggregator.aggregate_for_ai(device_id)
                if not aggregated:
                    return None, time.time() - start
                
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
                
                # All AI analyses
                current_anomaly = self.anomaly_detector.detect_current_anomaly(
                    aggregated.current_mean, aggregated.current_max, device_id
                )
                wear = self.wear_predictor.predict_wear(sensor_data, device_id)
                
                latency = time.time() - start
                return (aggregated, current_anomaly, wear), latency
            except Exception as e:
                print(f"Error analyzing {device_id}: {e}")
                return None, 0
        
        # Concurrent analysis
        analysis_start = time.time()
        latencies = []
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=min(num_devices, 20)) as executor:
            futures = {executor.submit(analyze_device, device_id): device_id 
                      for device_id in devices}
            
            for future in as_completed(futures):
                result, latency = future.result()
                if result:
                    successful += 1
                    latencies.append(latency * 1000)  # Convert to ms
                else:
                    failed += 1
        
        total_time = time.time() - analysis_start
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies) if latencies else 0
        p95_latency = calculate_p95(latencies)
        ops_per_second = successful / total_time if total_time > 0 else 0
        
        print(f"\nResults:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Ops/second: {ops_per_second:.1f}")
        print(f"  Avg latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        
        # Assertions
        self.assertEqual(failed, 0, "No failures should occur")
        self.assertEqual(successful, num_devices)
        self.assertLess(total_time, 10, f"Should analyze {num_devices} devices in < 10s")
        self.assertGreater(ops_per_second, 5, "Should achieve > 5 analyses/second")
    
    def test_burst_load_handling(self):
        """Test handling of burst loads"""
        num_devices = 20
        burst_size = 100  # readings per device in burst
        num_bursts = 5
        
        devices = [f"device_{i:03d}" for i in range(num_devices)]
        
        print(f"\n=== Burst Load Test: {num_bursts} bursts of {burst_size} readings ===")
        
        burst_times = []
        
        for burst_num in range(num_bursts):
            burst_start = time.time()
            
            # Send burst of data
            for device_id in devices:
                for i in range(burst_size):
                    reading = self._generate_sensor_reading(device_id, time.time())
                    self.aggregator.add_sensor_reading(reading)
            
            burst_time = time.time() - burst_start
            burst_times.append(burst_time)
            
            total_readings = burst_size * num_devices
            print(f"Burst {burst_num + 1}: {burst_time:.2f}s "
                  f"({total_readings/burst_time:.0f} readings/s)")
            
            # Short pause between bursts
            time.sleep(0.1)
        
        avg_burst_time = statistics.mean(burst_times)
        max_burst_time = max(burst_times)
        
        print(f"\nBurst Statistics:")
        print(f"  Average burst time: {avg_burst_time:.2f}s")
        print(f"  Max burst time: {max_burst_time:.2f}s")
        
        # Verify data is accessible after bursts
        for device_id in devices:
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            self.assertIsNotNone(aggregated)
        
        # Performance assertions
        total_readings_per_burst = burst_size * num_devices
        # Tighter threshold: 2000 readings should be handled in < 3 seconds
        self.assertLess(avg_burst_time, 3, 
                       f"Should handle {total_readings_per_burst} readings in < 3s")
    
    def test_gradual_device_scaling(self):
        """Test system behavior as device count gradually increases"""
        max_devices = 30
        readings_per_device = 10
        
        print(f"\n=== Gradual Scaling Test: 0 to {max_devices} devices ===")
        
        processing_times = []
        
        for num_devices in range(5, max_devices + 1, 5):
            devices = [f"device_{i:03d}" for i in range(num_devices)]
            
            # Add data for new devices
            for device_id in devices[-5:]:  # Only new devices
                for i in range(readings_per_device):
                    reading = self._generate_sensor_reading(
                        device_id,
                        time.time() - (readings_per_device - i) * 0.1
                    )
                    self.aggregator.add_sensor_reading(reading)
            
            # Measure processing time for all devices
            start_time = time.time()
            for device_id in devices:
                aggregated = self.aggregator.aggregate_for_ai(device_id)
                self.assertIsNotNone(aggregated)
            
            processing_time = time.time() - start_time
            processing_times.append((num_devices, processing_time))
            
            ops_per_second = num_devices / processing_time if processing_time > 0 else 0
            print(f"Devices: {num_devices:2d}, Time: {processing_time:.3f}s, "
                  f"Rate: {ops_per_second:.1f} devices/s")
        
        # Check that processing time scales reasonably
        # Time should increase roughly linearly with device count
        first_time = processing_times[0][1]
        last_time = processing_times[-1][1]
        time_ratio = last_time / first_time if first_time > 0 else 0
        device_ratio = processing_times[-1][0] / processing_times[0][0]
        
        print(f"\nScaling Analysis:")
        print(f"  Device ratio: {device_ratio:.1f}x")
        print(f"  Time ratio: {time_ratio:.1f}x")
        
        # Time should not grow much faster than device count
        self.assertLess(time_ratio, device_ratio * 1.5,
                       "Processing time should scale near-linearly")
    
    def test_sustained_multi_device_operation(self):
        """Test sustained operation with realistic multi-device scenario"""
        num_devices = 25
        duration_seconds = 30
        base_reading_rate = 1.0  # readings per second per device
        
        devices = [f"factory_device_{i:03d}" for i in range(num_devices)]
        
        print(f"\n=== Sustained Operation Test: {num_devices} devices for {duration_seconds}s ===")
        
        start_time = time.time()
        iteration_count = 0
        readings_sent = 0
        analyses_performed = 0
        
        while time.time() - start_time < duration_seconds:
            iteration_start = time.time()
            iteration_count += 1
            
            # Send readings from all devices
            for device_id in devices:
                reading = self._generate_sensor_reading(device_id, time.time())
                self.aggregator.add_sensor_reading(reading)
                readings_sent += 1
            
            # Periodically analyze some devices
            if iteration_count % 5 == 0:
                # Analyze random subset of devices
                sample_devices = random.sample(devices, min(5, num_devices))
                for device_id in sample_devices:
                    aggregated = self.aggregator.aggregate_for_ai(device_id)
                    if aggregated:
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
                        self.wear_predictor.predict_wear(sensor_data, device_id)
                        analyses_performed += 1
            
            # Maintain reading rate
            iteration_time = time.time() - iteration_start
            sleep_time = (1.0 / base_reading_rate) - iteration_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        total_time = time.time() - start_time
        
        print(f"\nResults:")
        print(f"  Duration: {total_time:.2f}s")
        print(f"  Readings sent: {readings_sent}")
        print(f"  Reading rate: {readings_sent/total_time:.1f} readings/s")
        print(f"  Analyses performed: {analyses_performed}")
        print(f"  Analysis rate: {analyses_performed/total_time:.2f} analyses/s")
        print(f"  Iterations: {iteration_count}")
        
        # Verify all devices are operational
        device_ids = self.aggregator.get_device_ids()
        self.assertEqual(len(device_ids), num_devices)
        
        # Final health check - all devices should be analyzable
        successful_analyses = 0
        for device_id in devices:
            aggregated = self.aggregator.aggregate_for_ai(device_id)
            if aggregated and aggregated.sample_count > 0:
                successful_analyses += 1
        
        print(f"  Final health check: {successful_analyses}/{num_devices} devices analyzable")
        
        # All devices should be analyzable
        self.assertEqual(successful_analyses, num_devices)
        
        # Performance assertions
        self.assertGreater(readings_sent/total_time, num_devices * 0.8,
                          "Should maintain at least 80% of target reading rate")


class TestStressScenarios(unittest.TestCase):
    """Stress tests for extreme scenarios"""
    
    def test_rapid_device_connection_disconnection(self):
        """Test rapid device connection and disconnection"""
        aggregator = DataAggregator(window_size_seconds=10)
        
        print(f"\n=== Stress Test: Rapid device churn ===")
        
        num_cycles = 20
        devices_per_cycle = 5
        
        for cycle in range(num_cycles):
            # Add devices
            devices = [f"temp_device_{cycle}_{i}" for i in range(devices_per_cycle)]
            
            for device_id in devices:
                for j in range(10):
                    reading = SensorReading(
                        timestamp=int(time.time() * 1000),
                        device_id=device_id,
                        motor_currents=[5.0, 5.1, 4.9],
                        vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                        temperatures=[45.0, 46.0, 44.5]
                    )
                    aggregator.add_sensor_reading(reading)
            
            # Verify devices are present
            device_ids = aggregator.get_device_ids()
            for device_id in devices:
                self.assertIn(device_id, device_ids)
        
        # Final device count
        final_devices = aggregator.get_device_ids()
        print(f"Total unique devices seen: {len(final_devices)}")
        
        self.assertGreaterEqual(len(final_devices), num_cycles * devices_per_cycle)
    
    def test_extreme_data_variance(self):
        """Test system with extreme variance in sensor readings"""
        aggregator = DataAggregator(window_size_seconds=10)
        anomaly_detector = StatisticalAnomalyDetector()
        device_id = "extreme_variance_device"
        
        print(f"\n=== Stress Test: Extreme data variance ===")
        
        # Add readings with extreme variance
        for i in range(100):
            # Alternate between very different values
            if i % 2 == 0:
                currents = [2.0, 2.1, 1.9]
                temps = [30.0, 31.0, 29.0]
            else:
                currents = [12.0, 12.1, 11.9]
                temps = [80.0, 81.0, 79.0]
            
            reading = SensorReading(
                timestamp=int((time.time() - (100 - i) * 0.1) * 1000),
                device_id=device_id,
                motor_currents=currents,
                vibration={"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
                temperatures=temps
            )
            aggregator.add_sensor_reading(reading)
        
        # System should still be able to aggregate
        aggregated = aggregator.aggregate_for_ai(device_id)
        self.assertIsNotNone(aggregated)
        
        # Anomaly detection should handle extreme variance
        anomaly = anomaly_detector.detect_temperature_anomaly(
            aggregated.temperature_mean,
            aggregated.temperature_max,
            device_id
        )
        
        print(f"Temperature variance handled: mean={aggregated.temperature_mean:.1f}, "
              f"max={aggregated.temperature_max:.1f}")
        
        self.assertIsNotNone(anomaly)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
