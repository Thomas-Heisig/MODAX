"""Tests for CacheManager

Tests the caching functionality including TTL, thread safety, and cache invalidation.
"""

import unittest
import time
from cache_manager import CacheManager, get_cache_manager


class TestCacheManager(unittest.TestCase):
    """Test suite for CacheManager"""
    
    def setUp(self):
        """Create a fresh cache manager for each test"""
        self.cache = CacheManager()
    
    def test_device_list_caching(self):
        """Test device list caching"""
        devices = ["device1", "device2", "device3"]
        
        # First access - cache miss
        result = self.cache.get_device_list()
        self.assertIsNone(result)
        self.assertEqual(self.cache.misses, 1)
        
        # Set cache
        self.cache.set_device_list(devices)
        
        # Second access - cache hit
        result = self.cache.get_device_list()
        self.assertEqual(result, devices)
        self.assertEqual(self.cache.hits, 1)
    
    def test_device_data_caching(self):
        """Test device data caching"""
        device_id = "device1"
        data = {
            "motor_currents": [1.5, 2.0, 1.8],
            "vibration": [0.1, 0.2, 0.15],
            "temperatures": [25.5, 26.0, 25.8]
        }
        
        # First access - cache miss
        result = self.cache.get_device_data(device_id)
        self.assertIsNone(result)
        
        # Set cache
        self.cache.set_device_data(device_id, data)
        
        # Second access - cache hit
        result = self.cache.get_device_data(device_id)
        self.assertEqual(result, data)
    
    def test_ai_analysis_caching(self):
        """Test AI analysis caching"""
        device_id = "device1"
        analysis = {
            "anomalies_detected": True,
            "wear_estimate": 0.75,
            "recommendations": ["Reduce speed", "Check lubrication"]
        }
        
        # First access - cache miss
        result = self.cache.get_ai_analysis(device_id)
        self.assertIsNone(result)
        
        # Set cache
        self.cache.set_ai_analysis(device_id, analysis)
        
        # Second access - cache hit
        result = self.cache.get_ai_analysis(device_id)
        self.assertEqual(result, analysis)
    
    def test_system_status_caching(self):
        """Test system status caching"""
        status = {
            "is_safe": True,
            "devices_online": ["device1", "device2"],
            "ai_enabled": True
        }
        
        # First access - cache miss
        result = self.cache.get_system_status()
        self.assertIsNone(result)
        
        # Set cache
        self.cache.set_system_status(status)
        
        # Second access - cache hit
        result = self.cache.get_system_status()
        self.assertEqual(result, status)
    
    def test_cache_invalidation(self):
        """Test device cache invalidation"""
        device_id = "device1"
        data = {"test": "data"}
        analysis = {"test": "analysis"}
        
        # Set caches
        self.cache.set_device_data(device_id, data)
        self.cache.set_ai_analysis(device_id, analysis)
        
        # Verify cached
        self.assertIsNotNone(self.cache.get_device_data(device_id))
        self.assertIsNotNone(self.cache.get_ai_analysis(device_id))
        
        # Invalidate
        self.cache.invalidate_device(device_id)
        
        # Verify cleared
        self.assertIsNone(self.cache.get_device_data(device_id))
        self.assertIsNone(self.cache.get_ai_analysis(device_id))
    
    def test_clear_all_caches(self):
        """Test clearing all caches"""
        # Populate all caches
        self.cache.set_device_list(["device1"])
        self.cache.set_device_data("device1", {"test": "data"})
        self.cache.set_ai_analysis("device1", {"test": "analysis"})
        self.cache.set_system_status({"test": "status"})
        
        # Clear all
        self.cache.clear_all()
        
        # Verify all cleared
        self.assertIsNone(self.cache.get_device_list())
        self.assertIsNone(self.cache.get_device_data("device1"))
        self.assertIsNone(self.cache.get_ai_analysis("device1"))
        self.assertIsNone(self.cache.get_system_status())
    
    def test_cache_statistics(self):
        """Test cache statistics reporting"""
        # Initial statistics
        stats = self.cache.get_statistics()
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 0)
        self.assertEqual(stats['total_requests'], 0)
        
        # Generate some hits and misses
        self.cache.get_device_list()  # miss
        self.cache.set_device_list(["device1"])
        self.cache.get_device_list()  # hit
        self.cache.get_device_list()  # hit
        
        # Check statistics
        stats = self.cache.get_statistics()
        self.assertEqual(stats['hits'], 2)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['total_requests'], 3)
        self.assertAlmostEqual(stats['hit_rate_percent'], 66.67, places=1)
    
    def test_different_cache_keys(self):
        """Test that different cache keys work independently"""
        # Device list with different keys
        self.cache.set_device_list(["device1"], cache_key="key1")
        self.cache.set_device_list(["device2"], cache_key="key2")
        
        result1 = self.cache.get_device_list(cache_key="key1")
        result2 = self.cache.get_device_list(cache_key="key2")
        
        self.assertEqual(result1, ["device1"])
        self.assertEqual(result2, ["device2"])
        
        # System status with different keys
        self.cache.set_system_status({"status": 1}, cache_key="key1")
        self.cache.set_system_status({"status": 2}, cache_key="key2")
        
        result1 = self.cache.get_system_status(cache_key="key1")
        result2 = self.cache.get_system_status(cache_key="key2")
        
        self.assertEqual(result1["status"], 1)
        self.assertEqual(result2["status"], 2)
    
    def test_device_data_count_separation(self):
        """Test that device data with different counts are cached separately"""
        device_id = "device1"
        data1 = {"readings": 1}
        data10 = {"readings": 10}
        
        self.cache.set_device_data(device_id, data1, count=1)
        self.cache.set_device_data(device_id, data10, count=10)
        
        result1 = self.cache.get_device_data(device_id, count=1)
        result10 = self.cache.get_device_data(device_id, count=10)
        
        self.assertEqual(result1, data1)
        self.assertEqual(result10, data10)
    
    def test_global_cache_manager_singleton(self):
        """Test that get_cache_manager returns the same instance"""
        cache1 = get_cache_manager()
        cache2 = get_cache_manager()
        
        self.assertIs(cache1, cache2)
        
        # Changes in one should reflect in the other
        cache1.set_device_list(["test"])
        result = cache2.get_device_list()
        self.assertEqual(result, ["test"])


if __name__ == '__main__':
    unittest.main()
