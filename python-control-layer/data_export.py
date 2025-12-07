"""Data export functionality for CSV and JSON formats"""
import csv
import json
import io
import logging
from datetime import datetime
from typing import List, Dict
from data_reader import get_data_reader

logger = logging.getLogger(__name__)


class DataExporter:
    """Handles data export in various formats"""
    
    def __init__(self):
        """Initialize data exporter"""
        self.data_reader = get_data_reader()
    
    def export_to_csv(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> str:
        """
        Export sensor data to CSV format
        
        Args:
            device_id: Device identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of records
            
        Returns:
            CSV string
        """
        data = self.data_reader.get_data_for_export(
            device_id, start_time, end_time, limit
        )
        
        if not data:
            return ""
        
        # Create CSV in memory
        output = io.StringIO()
        
        # Get field names from first record
        fieldnames = data[0].keys()
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"Exported {len(data)} records to CSV for device {device_id}")
        return csv_content
    
    def export_to_json(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> str:
        """
        Export sensor data to JSON format
        
        Args:
            device_id: Device identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of records
            
        Returns:
            JSON string
        """
        data = self.data_reader.get_data_for_export(
            device_id, start_time, end_time, limit
        )
        
        if not data:
            return "[]"
        
        json_content = json.dumps(data, indent=2)
        
        logger.info(f"Exported {len(data)} records to JSON for device {device_id}")
        return json_content
    
    def export_statistics_to_json(
        self,
        device_id: str,
        hours: int = 24
    ) -> str:
        """
        Export hourly statistics to JSON format
        
        Args:
            device_id: Device identifier
            hours: Number of hours of statistics
            
        Returns:
            JSON string
        """
        data = self.data_reader.get_hourly_statistics(device_id, hours)
        
        if not data:
            return "[]"
        
        # Convert datetime objects to ISO format strings
        for record in data:
            if 'hour' in record and isinstance(record['hour'], datetime):
                record['hour'] = record['hour'].isoformat()
        
        json_content = json.dumps(data, indent=2)
        
        logger.info(f"Exported {len(data)} hourly statistics to JSON for device {device_id}")
        return json_content


# Global data exporter instance
_data_exporter: DataExporter = None


def get_data_exporter() -> DataExporter:
    """Get or create the global data exporter"""
    global _data_exporter
    if _data_exporter is None:
        _data_exporter = DataExporter()
    return _data_exporter


def set_data_exporter(data_exporter: DataExporter):
    """Set a custom data exporter (for testing)"""
    global _data_exporter
    _data_exporter = data_exporter
