"""Data writer service for TimescaleDB"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2.extras
from db_connection import get_db_pool

logger = logging.getLogger(__name__)


class DataWriter:
    """Service for writing data to TimescaleDB"""
    
    def __init__(self):
        """Initialize data writer"""
        self.db_pool = get_db_pool()
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.db_pool.is_available()
    
    def write_sensor_data(self, device_id: str, data: Dict) -> bool:
        """
        Write single sensor reading
        
        Args:
            device_id: Device identifier
            data: Sensor data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_pool.config.ENABLED:
            return False
        
        try:
            timestamp = datetime.fromtimestamp(data['timestamp'])
            
            with self.db_pool.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO sensor_data (
                        time, device_id, current_a, current_b, current_c,
                        vibration, temperature, rpm, power_kw
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    timestamp,
                    device_id,
                    data.get('current_a'),
                    data.get('current_b'),
                    data.get('current_c'),
                    data.get('vibration'),
                    data.get('temperature'),
                    data.get('rpm'),
                    data.get('power_kw')
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write sensor data: {e}")
            return False
    
    def write_sensor_data_batch(self, records: List[tuple]) -> bool:
        """
        Write multiple sensor readings efficiently
        
        Args:
            records: List of tuples containing sensor data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_pool.config.ENABLED:
            return False
        
        try:
            with self.db_pool.get_cursor(commit=True) as cursor:
                psycopg2.extras.execute_batch(cursor, """
                    INSERT INTO sensor_data (
                        time, device_id, current_a, current_b, current_c,
                        vibration, temperature, rpm, power_kw
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, records, page_size=1000)
            logger.info(f"Wrote {len(records)} sensor records")
            return True
        except Exception as e:
            logger.error(f"Failed to write batch sensor data: {e}")
            return False
    
    def write_safety_event(self, device_id: str, event: Dict) -> bool:
        """
        Write safety event
        
        Args:
            device_id: Device identifier
            event: Safety event data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_pool.config.ENABLED:
            return False
        
        try:
            with self.db_pool.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO safety_events (
                        time, device_id, event_type, is_safe,
                        emergency_stop, door_open, overload_detected,
                        temperature_alarm, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    device_id,
                    event.get('type', 'unknown'),
                    event.get('is_safe', True),
                    event.get('emergency_stop', False),
                    event.get('door_open', False),
                    event.get('overload_detected', False),
                    event.get('temperature_alarm', False),
                    event.get('description', '')
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write safety event: {e}")
            return False
    
    def write_ai_analysis(self, device_id: str, analysis: Dict) -> bool:
        """
        Write AI analysis result
        
        Args:
            device_id: Device identifier
            analysis: AI analysis results
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_pool.config.ENABLED:
            return False
        
        try:
            with self.db_pool.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO ai_analysis (
                        time, device_id, analysis_type, confidence,
                        is_anomaly, anomaly_score, wear_percentage,
                        remaining_hours, recommendations, model_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    device_id,
                    'combined',
                    analysis.get('confidence', 0.0),
                    analysis.get('is_anomaly', False),
                    analysis.get('anomaly_score', 0.0),
                    analysis.get('wear_percentage', 0.0),
                    analysis.get('remaining_hours', 0),
                    psycopg2.extras.Json(analysis.get('recommendations', [])),
                    '1.0.0'
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write AI analysis: {e}")
            return False
    
    def write_control_command(
        self,
        device_id: str,
        command: str,
        user_id: str,
        source: str,
        status: str,
        parameters: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Write control command to audit trail
        
        Args:
            device_id: Device identifier
            command: Command type
            user_id: User who issued the command
            source: Command source (hmi, api, automation)
            status: Command status (executed, blocked, failed)
            parameters: Command parameters
            reason: Reason for status (if blocked/failed)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_pool.config.ENABLED:
            return False
        
        try:
            with self.db_pool.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO control_commands (
                        time, device_id, command, parameters, user_id,
                        source, status, reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    device_id,
                    command,
                    psycopg2.extras.Json(parameters or {}),
                    user_id,
                    source,
                    status,
                    reason
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to write control command: {e}")
            return False


# Global data writer instance
_data_writer: Optional[DataWriter] = None


def get_data_writer() -> DataWriter:
    """Get or create the global data writer"""
    global _data_writer
    if _data_writer is None:
        _data_writer = DataWriter()
    return _data_writer


def set_data_writer(data_writer: DataWriter):
    """Set a custom data writer (for testing)"""
    global _data_writer
    _data_writer = data_writer
