"""Data reader service for TimescaleDB"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db_connection import get_db_pool

logger = logging.getLogger(__name__)


class DataReader:
    """Service for querying historical data from TimescaleDB"""
    
    def __init__(self):
        """Initialize data reader"""
        self.db_pool = get_db_pool()
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.db_pool.is_available()
    
    def get_recent_sensor_data(
        self,
        device_id: str,
        minutes: int = 5
    ) -> List[Dict]:
        """
        Get recent sensor data for a device
        
        Args:
            device_id: Device identifier
            minutes: Number of minutes of history to fetch
            
        Returns:
            List of sensor readings
        """
        if not self.db_pool.config.ENABLED:
            return []
        
        try:
            with self.db_pool.get_cursor() as cursor:
                cursor.execute("""
                    SELECT time, current_a, current_b, current_c,
                           vibration, temperature, rpm, power_kw
                    FROM sensor_data
                    WHERE device_id = %s
                      AND time > NOW() - INTERVAL '%s minutes'
                    ORDER BY time DESC
                """, (device_id, minutes))
                
                return [
                    {
                        'timestamp': row[0].timestamp(),
                        'current_a': row[1],
                        'current_b': row[2],
                        'current_c': row[3],
                        'vibration': row[4],
                        'temperature': row[5],
                        'rpm': row[6],
                        'power_kw': row[7]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get recent sensor data: {e}")
            return []
    
    def get_hourly_statistics(
        self,
        device_id: str,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get hourly aggregated statistics
        
        Args:
            device_id: Device identifier
            hours: Number of hours of history to fetch
            
        Returns:
            List of hourly statistics
        """
        if not self.db_pool.config.ENABLED:
            return []
        
        try:
            with self.db_pool.get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        hour,
                        avg_current_a,
                        max_current_a,
                        avg_vibration,
                        max_vibration,
                        avg_temperature,
                        sample_count
                    FROM sensor_data_hourly
                    WHERE device_id = %s
                      AND hour > NOW() - INTERVAL '%s hours'
                    ORDER BY hour DESC
                """, (device_id, hours))
                
                return [
                    {
                        'hour': row[0],
                        'avg_current': row[1],
                        'max_current': row[2],
                        'avg_vibration': row[3],
                        'max_vibration': row[4],
                        'avg_temperature': row[5],
                        'sample_count': row[6]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get hourly statistics: {e}")
            return []
    
    def get_safety_events(
        self,
        device_id: Optional[str] = None,
        hours: int = 24,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get safety events with optional filters
        
        Args:
            device_id: Optional device identifier
            hours: Number of hours of history to fetch
            event_type: Optional event type filter
            
        Returns:
            List of safety events
        """
        if not self.db_pool.config.ENABLED:
            return []
        
        try:
            query = """
                SELECT time, device_id, event_type, is_safe, description
                FROM safety_events
                WHERE time > NOW() - INTERVAL %s
            """
            params = [f'{hours} hours']
            
            if device_id:
                query += " AND device_id = %s"
                params.append(device_id)
            
            if event_type:
                query += " AND event_type = %s"
                params.append(event_type)
            
            query += " ORDER BY time DESC LIMIT 100"
            
            with self.db_pool.get_cursor() as cursor:
                cursor.execute(query, params)
                return [
                    {
                        'timestamp': row[0],
                        'device_id': row[1],
                        'event_type': row[2],
                        'is_safe': row[3],
                        'description': row[4]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get safety events: {e}")
            return []
    
    def get_device_uptime(self, device_id: str, days: int = 7) -> Dict:
        """
        Calculate device uptime statistics
        
        Args:
            device_id: Device identifier
            days: Number of days to calculate uptime for
            
        Returns:
            Dictionary with uptime statistics
        """
        if not self.db_pool.config.ENABLED:
            return {}
        
        try:
            with self.db_pool.get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_samples,
                        COUNT(*) * 0.1 / 3600 as operating_hours,
                        MIN(time) as first_seen,
                        MAX(time) as last_seen
                    FROM sensor_data
                    WHERE device_id = %s
                      AND time > NOW() - INTERVAL '%s days'
                """, (device_id, days))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'total_samples': row[0],
                        'operating_hours': row[1],
                        'first_seen': row[2],
                        'last_seen': row[3]
                    }
                return {}
        except Exception as e:
            logger.error(f"Failed to get device uptime: {e}")
            return {}
    
    def get_data_for_export(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> List[Dict]:
        """
        Get sensor data for export (CSV/JSON)
        
        Args:
            device_id: Device identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of records to fetch
            
        Returns:
            List of sensor readings
        """
        if not self.db_pool.config.ENABLED:
            return []
        
        try:
            with self.db_pool.get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        time, device_id,
                        current_a, current_b, current_c,
                        vibration, temperature, rpm, power_kw
                    FROM sensor_data
                    WHERE device_id = %s
                      AND time >= %s
                      AND time <= %s
                    ORDER BY time ASC
                    LIMIT %s
                """, (device_id, start_time, end_time, limit))
                
                return [
                    {
                        'timestamp': row[0].isoformat(),
                        'device_id': row[1],
                        'current_a': row[2],
                        'current_b': row[3],
                        'current_c': row[4],
                        'vibration': row[5],
                        'temperature': row[6],
                        'rpm': row[7],
                        'power_kw': row[8]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get data for export: {e}")
            return []


# Global data reader instance
_data_reader: Optional[DataReader] = None


def get_data_reader() -> DataReader:
    """Get or create the global data reader"""
    global _data_reader
    if _data_reader is None:
        _data_reader = DataReader()
    return _data_reader


def set_data_reader(data_reader: DataReader):
    """Set a custom data reader (for testing)"""
    global _data_reader
    _data_reader = data_reader
