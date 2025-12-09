"""Caching Manager for Control Layer API

This module provides a caching strategy to reduce CPU load by caching
frequently accessed data. It uses TTL-based caching to ensure data freshness
while reducing redundant computations.

Issue #011: Caching strategy for frequently accessed data
"""

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)

# Cache configuration
# TTL (Time To Live) in seconds - how long cached data remains valid
DEVICE_LIST_CACHE_TTL = 5  # Device list changes rarely
DEVICE_DATA_CACHE_TTL = 1  # Fresh sensor data needed more frequently
AI_ANALYSIS_CACHE_TTL = 10  # AI analysis is expensive, cache longer
SYSTEM_STATUS_CACHE_TTL = 2  # System status for dashboards


class CacheManager:
    """Manages caching for Control Layer API endpoints
    
    This class provides thread-safe TTL-based caching for frequently
    accessed data to reduce CPU load and improve response times.
    """
    
    def __init__(self):
        """Initialize cache manager with separate caches for different data types"""
        # Device list cache (maxsize=10 means max 10 different queries)
        self.device_list_cache = TTLCache(maxsize=10, ttl=DEVICE_LIST_CACHE_TTL)
        
        # Device data cache (maxsize=100 means max 100 devices)
        self.device_data_cache = TTLCache(maxsize=100, ttl=DEVICE_DATA_CACHE_TTL)
        
        # AI analysis cache (maxsize=50 for multiple devices)
        self.ai_analysis_cache = TTLCache(maxsize=50, ttl=AI_ANALYSIS_CACHE_TTL)
        
        # System status cache (maxsize=5 for different status queries)
        self.system_status_cache = TTLCache(maxsize=5, ttl=SYSTEM_STATUS_CACHE_TTL)
        
        # Thread locks for thread-safe access
        self._device_list_lock = threading.Lock()
        self._device_data_lock = threading.Lock()
        self._ai_analysis_lock = threading.Lock()
        self._system_status_lock = threading.Lock()
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        
        logger.info("CacheManager initialized with TTL-based caching")
        logger.info(f"Cache TTLs: devices={DEVICE_LIST_CACHE_TTL}s, "
                   f"data={DEVICE_DATA_CACHE_TTL}s, "
                   f"ai={AI_ANALYSIS_CACHE_TTL}s, "
                   f"status={SYSTEM_STATUS_CACHE_TTL}s")
    
    def get_device_list(self, cache_key: str = "default") -> Optional[List[str]]:
        """Get cached device list
        
        Args:
            cache_key: Cache key for different device list queries
            
        Returns:
            Cached device list or None if not in cache
        """
        with self._device_list_lock:
            if cache_key in self.device_list_cache:
                self.hits += 1
                logger.debug(f"Cache HIT: device_list (key={cache_key})")
                return self.device_list_cache[cache_key]
            self.misses += 1
            logger.debug(f"Cache MISS: device_list (key={cache_key})")
            return None
    
    def set_device_list(self, devices: List[str], cache_key: str = "default") -> None:
        """Cache device list
        
        Args:
            devices: List of device IDs
            cache_key: Cache key for different device list queries
        """
        with self._device_list_lock:
            self.device_list_cache[cache_key] = devices
            logger.debug(f"Cached device_list: {len(devices)} devices (key={cache_key})")
    
    def get_device_data(self, device_id: str, count: int = 1) -> Optional[Dict[str, Any]]:
        """Get cached device data
        
        Args:
            device_id: Device identifier
            count: Number of readings requested
            
        Returns:
            Cached device data or None if not in cache
        """
        cache_key = f"{device_id}_{count}"
        with self._device_data_lock:
            if cache_key in self.device_data_cache:
                self.hits += 1
                logger.debug(f"Cache HIT: device_data (key={cache_key})")
                return self.device_data_cache[cache_key]
            self.misses += 1
            logger.debug(f"Cache MISS: device_data (key={cache_key})")
            return None
    
    def set_device_data(self, device_id: str, data: Dict[str, Any], count: int = 1) -> None:
        """Cache device data
        
        Args:
            device_id: Device identifier
            data: Device data to cache
            count: Number of readings
        """
        cache_key = f"{device_id}_{count}"
        with self._device_data_lock:
            self.device_data_cache[cache_key] = data
            logger.debug(f"Cached device_data (key={cache_key})")
    
    def get_ai_analysis(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get cached AI analysis
        
        Args:
            device_id: Device identifier
            
        Returns:
            Cached AI analysis or None if not in cache
        """
        with self._ai_analysis_lock:
            if device_id in self.ai_analysis_cache:
                self.hits += 1
                logger.debug(f"Cache HIT: ai_analysis (device={device_id})")
                return self.ai_analysis_cache[device_id]
            self.misses += 1
            logger.debug(f"Cache MISS: ai_analysis (device={device_id})")
            return None
    
    def set_ai_analysis(self, device_id: str, analysis: Dict[str, Any]) -> None:
        """Cache AI analysis
        
        Args:
            device_id: Device identifier
            analysis: AI analysis results to cache
        """
        with self._ai_analysis_lock:
            self.ai_analysis_cache[device_id] = analysis
            logger.debug(f"Cached ai_analysis (device={device_id})")
    
    def get_system_status(self, cache_key: str = "default") -> Optional[Dict[str, Any]]:
        """Get cached system status
        
        Args:
            cache_key: Cache key for different status queries
            
        Returns:
            Cached system status or None if not in cache
        """
        with self._system_status_lock:
            if cache_key in self.system_status_cache:
                self.hits += 1
                logger.debug(f"Cache HIT: system_status (key={cache_key})")
                return self.system_status_cache[cache_key]
            self.misses += 1
            logger.debug(f"Cache MISS: system_status (key={cache_key})")
            return None
    
    def set_system_status(self, status: Dict[str, Any], cache_key: str = "default") -> None:
        """Cache system status
        
        Args:
            status: System status to cache
            cache_key: Cache key for different status queries
        """
        with self._system_status_lock:
            self.system_status_cache[cache_key] = status
            logger.debug(f"Cached system_status (key={cache_key})")
    
    def invalidate_device(self, device_id: str) -> None:
        """Invalidate all caches for a specific device
        
        This should be called when device data is updated to ensure
        cache consistency.
        
        Args:
            device_id: Device identifier
        """
        with self._device_data_lock:
            # Remove all cached entries for this device
            keys_to_remove = [k for k in self.device_data_cache.keys() 
                            if k.startswith(f"{device_id}_")]
            for key in keys_to_remove:
                del self.device_data_cache[key]
        
        with self._ai_analysis_lock:
            if device_id in self.ai_analysis_cache:
                del self.ai_analysis_cache[device_id]
        
        logger.debug(f"Invalidated cache for device {device_id}")
    
    def clear_all(self) -> None:
        """Clear all caches
        
        This should be used sparingly, only when necessary (e.g., system restart)
        """
        with self._device_list_lock:
            self.device_list_cache.clear()
        with self._device_data_lock:
            self.device_data_cache.clear()
        with self._ai_analysis_lock:
            self.ai_analysis_cache.clear()
        with self._system_status_lock:
            self.system_status_cache.clear()
        
        logger.info("All caches cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache hit/miss statistics and sizes
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_sizes": {
                "device_list": len(self.device_list_cache),
                "device_data": len(self.device_data_cache),
                "ai_analysis": len(self.ai_analysis_cache),
                "system_status": len(self.system_status_cache)
            },
            "ttl_config": {
                "device_list": DEVICE_LIST_CACHE_TTL,
                "device_data": DEVICE_DATA_CACHE_TTL,
                "ai_analysis": AI_ANALYSIS_CACHE_TTL,
                "system_status": SYSTEM_STATUS_CACHE_TTL
            }
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance
    
    Returns:
        Global CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
