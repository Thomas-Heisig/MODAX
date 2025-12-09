"""
Abstract Device Interface for MODAX Control Layer

This module defines the abstract interface that all device drivers must implement,
providing a unified way to communicate with different types of industrial devices:
- ESP32 field devices (MQTT)
- GRBL-based CNC machines (Serial/G-Code)
- Arduino with Modbus TCP (Ethernet)
- Other industrial controllers

The abstraction enables easy integration of new device types while maintaining
a consistent interface for the control layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Supported device types"""
    ESP32_FIELD = "esp32_field"
    GRBL_CNC = "grbl_cnc"
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    MQTT_GENERIC = "mqtt_generic"
    OPC_UA = "opc_ua"


class DeviceState(Enum):
    """Device operational states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDLE = "idle"
    RUNNING = "running"
    HOMING = "homing"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"
    MAINTENANCE = "maintenance"


@dataclass
class DeviceCapabilities:
    """Device capability flags"""
    supports_sensor_data: bool = True
    supports_safety_monitoring: bool = True
    supports_motion_control: bool = False
    supports_gcode: bool = False
    supports_configuration: bool = False
    supports_diagnostics: bool = False
    max_update_rate_hz: float = 10.0
    

@dataclass
class DeviceInfo:
    """Device identification and metadata"""
    device_id: str
    device_type: DeviceType
    manufacturer: str
    model: str
    firmware_version: str
    capabilities: DeviceCapabilities
    connection_string: str  # e.g., "serial:/dev/ttyUSB0" or "tcp://192.168.1.100:502"
    metadata: Dict[str, Any]


@dataclass
class DeviceCommand:
    """Generic device command"""
    command_type: str  # e.g., "gcode", "register_write", "configuration"
    command_data: Any
    timeout_seconds: float = 5.0
    requires_ack: bool = True


@dataclass
class DeviceResponse:
    """Generic device response"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[int] = None
    timestamp: float = 0.0


@dataclass
class SensorData:
    """Generic sensor data from device"""
    device_id: str
    timestamp: float
    values: Dict[str, float]  # Sensor name -> value mapping
    units: Dict[str, str]  # Sensor name -> unit mapping
    metadata: Dict[str, Any]


@dataclass
class SafetyData:
    """Generic safety status from device"""
    device_id: str
    timestamp: float
    is_safe: bool
    emergency_stop_active: bool
    door_open: bool
    overload_detected: bool
    temperature_ok: bool
    safety_flags: Dict[str, bool]
    metadata: Dict[str, Any]


class DeviceInterface(ABC):
    """
    Abstract base class for all device drivers
    
    All device drivers must inherit from this class and implement
    the required methods. This ensures consistent behavior across
    different device types.
    """
    
    def __init__(self, device_info: DeviceInfo):
        """
        Initialize device interface
        
        Args:
            device_info: Device identification and capabilities
        """
        self.device_info = device_info
        self.state = DeviceState.DISCONNECTED
        self._callbacks: Dict[str, List[Callable]] = {
            'sensor_data': [],
            'safety_data': [],
            'state_change': [],
            'error': []
        }
        self.logger = logging.getLogger(f"{__name__}.{device_info.device_id}")
    
    # ========================================================================
    # Connection Management (Required)
    # ========================================================================
    
    @abstractmethod
    def connect(self, timeout: float = 10.0) -> bool:
        """
        Establish connection to device
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to device
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if device is currently connected
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def reconnect(self, timeout: float = 10.0) -> bool:
        """
        Attempt to reconnect to device
        
        Args:
            timeout: Reconnection timeout in seconds
            
        Returns:
            True if reconnection successful, False otherwise
        """
        pass
    
    # ========================================================================
    # Data Reading (Required for devices with sensors)
    # ========================================================================
    
    def read_sensor_data(self) -> Optional[SensorData]:
        """
        Read current sensor data from device
        
        Returns:
            SensorData object or None if not available/supported
        """
        if not self.device_info.capabilities.supports_sensor_data:
            return None
        return self._read_sensor_data_impl()
    
    @abstractmethod
    def _read_sensor_data_impl(self) -> Optional[SensorData]:
        """Implementation-specific sensor data reading"""
        pass
    
    def read_safety_status(self) -> Optional[SafetyData]:
        """
        Read current safety status from device
        
        Returns:
            SafetyData object or None if not available/supported
        """
        if not self.device_info.capabilities.supports_safety_monitoring:
            return None
        return self._read_safety_status_impl()
    
    @abstractmethod
    def _read_safety_status_impl(self) -> Optional[SafetyData]:
        """Implementation-specific safety status reading"""
        pass
    
    # ========================================================================
    # Command Execution (Required for controllable devices)
    # ========================================================================
    
    def send_command(self, command: DeviceCommand) -> DeviceResponse:
        """
        Send command to device
        
        Args:
            command: Command to send
            
        Returns:
            DeviceResponse with result
        """
        if not self.is_connected():
            return DeviceResponse(
                success=False,
                message="Device not connected",
                error_code=1
            )
        
        return self._send_command_impl(command)
    
    @abstractmethod
    def _send_command_impl(self, command: DeviceCommand) -> DeviceResponse:
        """Implementation-specific command sending"""
        pass
    
    # ========================================================================
    # State Management
    # ========================================================================
    
    def get_state(self) -> DeviceState:
        """Get current device state"""
        return self.state
    
    def set_state(self, new_state: DeviceState):
        """
        Set device state and notify callbacks
        
        Args:
            new_state: New device state
        """
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"State change: {old_state.value} -> {new_state.value}")
            self._notify_state_change(old_state, new_state)
    
    # ========================================================================
    # Configuration (Optional)
    # ========================================================================
    
    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Get device configuration
        
        Returns:
            Configuration dictionary or None if not supported
        """
        if not self.device_info.capabilities.supports_configuration:
            return None
        return self._get_configuration_impl()
    
    def _get_configuration_impl(self) -> Dict[str, Any]:
        """Implementation-specific configuration retrieval"""
        return {}
    
    def set_configuration(self, config: Dict[str, Any]) -> DeviceResponse:
        """
        Set device configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            DeviceResponse with result
        """
        if not self.device_info.capabilities.supports_configuration:
            return DeviceResponse(
                success=False,
                message="Configuration not supported by this device"
            )
        return self._set_configuration_impl(config)
    
    def _set_configuration_impl(self, config: Dict[str, Any]) -> DeviceResponse:
        """Implementation-specific configuration setting"""
        return DeviceResponse(success=False, message="Not implemented")
    
    # ========================================================================
    # Diagnostics (Optional)
    # ========================================================================
    
    def get_diagnostics(self) -> Optional[Dict[str, Any]]:
        """
        Get device diagnostics information
        
        Returns:
            Diagnostics dictionary or None if not supported
        """
        if not self.device_info.capabilities.supports_diagnostics:
            return None
        return self._get_diagnostics_impl()
    
    def _get_diagnostics_impl(self) -> Dict[str, Any]:
        """Implementation-specific diagnostics retrieval"""
        return {}
    
    # ========================================================================
    # Callback Management
    # ========================================================================
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register callback for device events
        
        Args:
            event_type: Type of event ('sensor_data', 'safety_data', 'state_change', 'error')
            callback: Callback function
        """
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
            self.logger.debug(f"Registered callback for {event_type}")
        else:
            self.logger.warning(f"Unknown event type: {event_type}")
    
    def unregister_callback(self, event_type: str, callback: Callable):
        """
        Unregister callback for device events
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
            self.logger.debug(f"Unregistered callback for {event_type}")
    
    def _notify_sensor_data(self, data: SensorData):
        """Notify all sensor data callbacks"""
        for callback in self._callbacks['sensor_data']:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in sensor_data callback: {e}")
    
    def _notify_safety_data(self, data: SafetyData):
        """Notify all safety data callbacks"""
        for callback in self._callbacks['safety_data']:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in safety_data callback: {e}")
    
    def _notify_state_change(self, old_state: DeviceState, new_state: DeviceState):
        """Notify all state change callbacks"""
        for callback in self._callbacks['state_change']:
            try:
                callback(old_state, new_state)
            except Exception as e:
                self.logger.error(f"Error in state_change callback: {e}")
    
    def _notify_error(self, error_message: str, error_code: Optional[int] = None):
        """Notify all error callbacks"""
        for callback in self._callbacks['error']:
            try:
                callback(error_message, error_code)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_info(self) -> DeviceInfo:
        """Get device information"""
        return self.device_info
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.device_info.device_type.value}:{self.device_info.device_id} [{self.state.value}]"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"DeviceInterface(id={self.device_info.device_id}, "
                f"type={self.device_info.device_type.value}, "
                f"state={self.state.value})")
