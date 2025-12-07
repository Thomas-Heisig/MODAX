"""Data Aggregator - Collects and aggregates sensor data from field layer"""
import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class SensorReading:
    """Individual sensor reading"""
    timestamp: float
    device_id: str
    motor_currents: List[float]
    vibration: Dict[str, float]
    temperatures: List[float]

    @classmethod
    def from_json(cls, data: str) -> 'SensorReading':
        """Create from JSON string"""
        obj = json.loads(data)
        return cls(
            timestamp=obj['timestamp'],
            device_id=obj['device_id'],
            motor_currents=obj['motor_currents'],
            vibration=obj['vibration'],
            temperatures=obj['temperatures']
        )


@dataclass
class SafetyStatus:
    """Safety system status"""
    timestamp: float
    device_id: str
    emergency_stop: bool
    door_closed: bool
    overload_detected: bool
    temperature_ok: bool

    @classmethod
    def from_json(cls, data: str) -> 'SafetyStatus':
        """Create from JSON string"""
        obj = json.loads(data)
        return cls(
            timestamp=obj['timestamp'],
            device_id=obj['device_id'],
            emergency_stop=obj['emergency_stop'],
            door_closed=obj['door_closed'],
            overload_detected=obj['overload_detected'],
            temperature_ok=obj['temperature_ok']
        )

    def is_safe(self) -> bool:
        """Check if system is in safe state"""
        return (not self.emergency_stop
                and self.door_closed
                and not self.overload_detected
                and self.temperature_ok)


@dataclass
class AggregatedData:
    """Aggregated sensor statistics for AI analysis"""
    device_id: str
    time_window_start: float
    time_window_end: float

    # Current statistics
    current_mean: List[float] = field(default_factory=list)
    current_std: List[float] = field(default_factory=list)
    current_max: List[float] = field(default_factory=list)

    # Vibration statistics
    vibration_mean: Dict[str, float] = field(default_factory=dict)
    vibration_std: Dict[str, float] = field(default_factory=dict)
    vibration_max: Dict[str, float] = field(default_factory=dict)

    # Temperature statistics
    temperature_mean: List[float] = field(default_factory=list)
    temperature_max: List[float] = field(default_factory=list)

    # Sample count
    sample_count: int = 0


class DataAggregator:
    """Aggregates sensor data for AI analysis"""

    def __init__(self, window_size_seconds: int = 10, max_points: int = 1000):
        self.window_size = window_size_seconds
        self.max_points = max_points

        # Ring buffers for each device
        self.sensor_data: Dict[str, deque] = {}
        self.safety_status: Dict[str, SafetyStatus] = {}

    def add_sensor_reading(self, reading: SensorReading):
        """Add a new sensor reading"""
        device_id = reading.device_id

        if device_id not in self.sensor_data:
            self.sensor_data[device_id] = deque(maxlen=self.max_points)

        self.sensor_data[device_id].append(reading)

        # Remove old data outside the window
        self._cleanup_old_data(device_id)

    def update_safety_status(self, status: SafetyStatus):
        """Update safety status for a device"""
        self.safety_status[status.device_id] = status

    def get_latest_safety_status(self, device_id: str) -> Optional[SafetyStatus]:
        """Get most recent safety status"""
        return self.safety_status.get(device_id)

    def is_system_safe(self) -> bool:
        """Check if all devices are in safe state"""
        if not self.safety_status:
            return False
        return all(status.is_safe() for status in self.safety_status.values())

    def aggregate_for_ai(self, device_id: str,
                         window_seconds: Optional[int] = None) -> Optional[AggregatedData]:
        """
        Aggregate recent sensor data for AI analysis.
        Returns statistical summaries suitable for ML models.

        Performance optimizations:
        - Uses numpy array operations for vectorized computation
        - Pre-allocates arrays for better memory efficiency
        - Single-pass data extraction
        """
        if device_id not in self.sensor_data or not self.sensor_data[device_id]:
            return None

        window = window_seconds or self.window_size
        current_time = time.time()
        cutoff_time = current_time - window

        # Filter data within time window
        recent_data = [r for r in self.sensor_data[device_id]
                       if r.timestamp / 1000.0 >= cutoff_time]  # Convert ms to seconds

        if not recent_data:
            return None

        # Pre-determine array dimensions for efficiency
        num_samples = len(recent_data)
        num_motors = len(recent_data[0].motor_currents)
        num_temps = len(recent_data[0].temperatures)

        # Pre-allocate numpy arrays for better performance
        currents_array = np.zeros((num_samples, num_motors), dtype=np.float32)
        vibrations_array = np.zeros((num_samples, 4), dtype=np.float32)  # x, y, z, magnitude
        temperatures_array = np.zeros((num_samples, num_temps), dtype=np.float32)

        # Single-pass data extraction into pre-allocated arrays
        for i, reading in enumerate(recent_data):
            currents_array[i] = reading.motor_currents
            vibrations_array[i] = [
                reading.vibration['x'],
                reading.vibration['y'],
                reading.vibration['z'],
                reading.vibration['magnitude']
            ]
            temperatures_array[i] = reading.temperatures

        # Calculate statistics using vectorized numpy operations
        aggregated = AggregatedData(
            device_id=device_id,
            time_window_start=recent_data[0].timestamp / 1000.0,
            time_window_end=recent_data[-1].timestamp / 1000.0,
            sample_count=num_samples
        )

        # Current statistics - vectorized computation
        aggregated.current_mean = currents_array.mean(axis=0).tolist()
        aggregated.current_std = currents_array.std(axis=0).tolist()
        aggregated.current_max = currents_array.max(axis=0).tolist()

        # Vibration statistics - vectorized computation
        vib_keys = ['x', 'y', 'z', 'magnitude']
        aggregated.vibration_mean = {
            key: float(vibrations_array[:, i].mean())
            for i, key in enumerate(vib_keys)
        }
        aggregated.vibration_std = {
            key: float(vibrations_array[:, i].std())
            for i, key in enumerate(vib_keys)
        }
        aggregated.vibration_max = {
            key: float(vibrations_array[:, i].max())
            for i, key in enumerate(vib_keys)
        }

        # Temperature statistics - vectorized computation
        aggregated.temperature_mean = temperatures_array.mean(axis=0).tolist()
        aggregated.temperature_max = temperatures_array.max(axis=0).tolist()

        return aggregated

    def get_recent_readings(self, device_id: str, count: int = 100) -> List[SensorReading]:
        """Get most recent N readings for a device"""
        if device_id not in self.sensor_data:
            return []

        data = list(self.sensor_data[device_id])
        return data[-count:]

    def _cleanup_old_data(self, device_id: str):
        """Remove data outside the time window"""
        if device_id not in self.sensor_data:
            return

        current_time = time.time()
        cutoff_time = current_time - (self.window_size * 10)  # Keep 10x window for history

        data = self.sensor_data[device_id]
        while data and data[0].timestamp / 1000.0 < cutoff_time:
            data.popleft()

    def get_device_ids(self) -> List[str]:
        """Get all known device IDs"""
        return list(self.sensor_data.keys())
