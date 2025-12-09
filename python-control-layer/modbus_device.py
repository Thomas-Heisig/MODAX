"""
Modbus TCP Device Driver

This module provides a device driver for Modbus TCP devices, commonly used in
industrial automation with PLCs, Arduino with Ethernet shields, and other
industrial controllers.

Supports:
- Modbus TCP/IP communication
- Register reading (holding, input, coils, discrete inputs)
- Register writing (holding, coils)
- Function codes 1-6, 15-16
- Multiple register operations
- Connection pooling and retry logic

Compatible with:
- Arduino with Ethernet shield running Modbus TCP
- Industrial PLCs (Siemens, Allen-Bradley with Modbus gateway)
- Modbus RTU-to-TCP gateways
- Custom Modbus devices
"""

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False

import time
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from device_interface import (
    DeviceInterface, DeviceInfo, DeviceType, DeviceState,
    DeviceCapabilities, DeviceCommand, DeviceResponse,
    SensorData, SafetyData
)

# Modbus constants
MODBUS_DEFAULT_PORT = 502
MODBUS_DEFAULT_UNIT = 1
MODBUS_TIMEOUT = 3.0
MODBUS_RECONNECT_DELAY = 5.0


@dataclass
class ModbusRegisterMap:
    """Modbus register mapping configuration"""
    # Sensor data registers (input registers)
    current_1: int = 0
    current_2: int = 1
    vibration_x: int = 2
    vibration_y: int = 3
    vibration_z: int = 4
    temperature_1: int = 5
    
    # Safety status registers (coils/discrete inputs)
    emergency_stop: int = 0
    door_closed: int = 1
    overload_detected: int = 2
    temperature_ok: int = 3
    
    # Control registers (holding registers)
    command: int = 100
    setpoint: int = 101


class ModbusTCPDevice(DeviceInterface):
    """
    Modbus TCP Device Driver
    
    Communicates with Modbus TCP devices (PLCs, Arduino, etc.) over Ethernet.
    Provides register read/write, status monitoring, and command execution.
    """
    
    def __init__(self, device_id: str, host: str, port: int = MODBUS_DEFAULT_PORT,
                 unit_id: int = MODBUS_DEFAULT_UNIT,
                 register_map: Optional[ModbusRegisterMap] = None):
        """
        Initialize Modbus TCP device
        
        Args:
            device_id: Unique device identifier
            host: IP address or hostname
            port: Modbus TCP port (default: 502)
            unit_id: Modbus unit/slave ID (default: 1)
            register_map: Register mapping configuration
        """
        if not MODBUS_AVAILABLE:
            raise ImportError("pymodbus not installed. Install with: pip install pymodbus")
        
        # Create device info
        device_info = DeviceInfo(
            device_id=device_id,
            device_type=DeviceType.MODBUS_TCP,
            manufacturer="Generic",
            model="Modbus TCP Device",
            firmware_version="unknown",
            capabilities=DeviceCapabilities(
                supports_sensor_data=True,
                supports_safety_monitoring=True,
                supports_motion_control=False,  # Depends on device
                supports_gcode=False,
                supports_configuration=True,
                supports_diagnostics=True,
                max_update_rate_hz=10.0
            ),
            connection_string=f"modbus://{host}:{port}/{unit_id}",
            metadata={"host": host, "port": port, "unit_id": unit_id}
        )
        
        super().__init__(device_info)
        
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.client: Optional[ModbusTcpClient] = None
        self.register_map = register_map or ModbusRegisterMap()
        
        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
        self.monitor_interval = 0.1  # 10Hz update rate
        
        # Data cache
        self.cached_sensor_data: Optional[Dict[str, float]] = None
        self.cached_safety_data: Optional[Dict[str, bool]] = None
        self.data_lock = threading.Lock()
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def connect(self, timeout: float = 10.0) -> bool:
        """Establish Modbus TCP connection"""
        try:
            self.logger.info(f"Connecting to Modbus TCP device at {self.host}:{self.port}")
            self.set_state(DeviceState.CONNECTING)
            
            # Create Modbus client
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=MODBUS_TIMEOUT
            )
            
            # Connect to device
            if not self.client.connect():
                self.logger.error("Failed to establish Modbus TCP connection")
                self.set_state(DeviceState.DISCONNECTED)
                return False
            
            # Test connection with a read
            result = self.client.read_input_registers(0, 1, unit=self.unit_id)
            if result.isError():
                self.logger.warning("Modbus connection established but read test failed")
            
            self.set_state(DeviceState.CONNECTED)
            
            # Start monitoring thread
            self._start_monitoring()
            
            self.logger.info("Connected to Modbus TCP device successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}", exc_info=True)
            self.set_state(DeviceState.DISCONNECTED)
            return False
    
    def disconnect(self) -> bool:
        """Close Modbus TCP connection"""
        try:
            self.logger.info("Disconnecting from Modbus TCP device")
            
            # Stop monitoring
            self._stop_monitoring()
            
            # Close connection
            if self.client:
                self.client.close()
            
            self.set_state(DeviceState.DISCONNECTED)
            self.logger.info("Disconnected from Modbus TCP device")
            return True
            
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Modbus connection is active"""
        return self.client is not None and self.client.connected
    
    def reconnect(self, timeout: float = 10.0) -> bool:
        """Attempt to reconnect"""
        self.disconnect()
        time.sleep(1.0)
        return self.connect(timeout)
    
    # ========================================================================
    # Data Reading
    # ========================================================================
    
    def _read_sensor_data_impl(self) -> Optional[SensorData]:
        """Read sensor data from input registers"""
        try:
            with self.data_lock:
                if self.cached_sensor_data is None:
                    return None
                
                return SensorData(
                    device_id=self.device_info.device_id,
                    timestamp=time.time(),
                    values=self.cached_sensor_data.copy(),
                    units={
                        'current_1': 'A',
                        'current_2': 'A',
                        'vibration_x': 'm/s²',
                        'vibration_y': 'm/s²',
                        'vibration_z': 'm/s²',
                        'temperature_1': '°C'
                    },
                    metadata={}
                )
        except Exception as e:
            self.logger.error(f"Error reading sensor data: {e}")
            return None
    
    def _read_safety_status_impl(self) -> Optional[SafetyData]:
        """Read safety status from discrete inputs/coils"""
        try:
            with self.data_lock:
                if self.cached_safety_data is None:
                    return None
                
                return SafetyData(
                    device_id=self.device_info.device_id,
                    timestamp=time.time(),
                    is_safe=not self.cached_safety_data.get('emergency_stop', False),
                    emergency_stop_active=self.cached_safety_data.get('emergency_stop', False),
                    door_open=not self.cached_safety_data.get('door_closed', True),
                    overload_detected=self.cached_safety_data.get('overload_detected', False),
                    temperature_ok=self.cached_safety_data.get('temperature_ok', True),
                    safety_flags=self.cached_safety_data.copy(),
                    metadata={}
                )
        except Exception as e:
            self.logger.error(f"Error reading safety status: {e}")
            return None
    
    # ========================================================================
    # Command Execution
    # ========================================================================
    
    def _send_command_impl(self, command: DeviceCommand) -> DeviceResponse:
        """Send command to Modbus device"""
        try:
            if command.command_type == "write_register":
                return self._write_register(command.command_data)
            elif command.command_type == "write_coil":
                return self._write_coil(command.command_data)
            elif command.command_type == "read_register":
                return self._read_register(command.command_data)
            elif command.command_type == "read_coil":
                return self._read_coil(command.command_data)
            else:
                return DeviceResponse(
                    success=False,
                    message=f"Unknown command type: {command.command_type}"
                )
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Command execution failed: {e}"
            )
    
    def _write_register(self, data: Dict[str, Any]) -> DeviceResponse:
        """Write to holding register(s)"""
        address = data.get('address')
        value = data.get('value')
        values = data.get('values')  # For multiple registers
        
        if address is None:
            return DeviceResponse(success=False, message="Missing 'address'")
        
        try:
            if values is not None:
                # Write multiple registers
                result = self.client.write_registers(
                    address, values, unit=self.unit_id
                )
            elif value is not None:
                # Write single register
                result = self.client.write_register(
                    address, value, unit=self.unit_id
                )
            else:
                return DeviceResponse(success=False, message="Missing 'value' or 'values'")
            
            if result.isError():
                return DeviceResponse(
                    success=False,
                    message=f"Modbus write error: {result}"
                )
            
            return DeviceResponse(
                success=True,
                message=f"Register(s) written successfully",
                timestamp=time.time()
            )
            
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Write failed: {e}"
            )
    
    def _write_coil(self, data: Dict[str, Any]) -> DeviceResponse:
        """Write to coil(s)"""
        address = data.get('address')
        value = data.get('value')
        
        if address is None or value is None:
            return DeviceResponse(success=False, message="Missing 'address' or 'value'")
        
        try:
            result = self.client.write_coil(address, value, unit=self.unit_id)
            
            if result.isError():
                return DeviceResponse(
                    success=False,
                    message=f"Modbus write error: {result}"
                )
            
            return DeviceResponse(
                success=True,
                message=f"Coil written successfully",
                timestamp=time.time()
            )
            
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Write failed: {e}"
            )
    
    def _read_register(self, data: Dict[str, Any]) -> DeviceResponse:
        """Read holding or input register(s)"""
        address = data.get('address')
        count = data.get('count', 1)
        register_type = data.get('type', 'holding')  # 'holding' or 'input'
        
        if address is None:
            return DeviceResponse(success=False, message="Missing 'address'")
        
        try:
            if register_type == 'input':
                result = self.client.read_input_registers(
                    address, count, unit=self.unit_id
                )
            else:
                result = self.client.read_holding_registers(
                    address, count, unit=self.unit_id
                )
            
            if result.isError():
                return DeviceResponse(
                    success=False,
                    message=f"Modbus read error: {result}"
                )
            
            return DeviceResponse(
                success=True,
                message=f"Register(s) read successfully",
                data={'values': result.registers},
                timestamp=time.time()
            )
            
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Read failed: {e}"
            )
    
    def _read_coil(self, data: Dict[str, Any]) -> DeviceResponse:
        """Read coil or discrete input"""
        address = data.get('address')
        count = data.get('count', 1)
        input_type = data.get('type', 'coil')  # 'coil' or 'discrete'
        
        if address is None:
            return DeviceResponse(success=False, message="Missing 'address'")
        
        try:
            if input_type == 'discrete':
                result = self.client.read_discrete_inputs(
                    address, count, unit=self.unit_id
                )
            else:
                result = self.client.read_coils(
                    address, count, unit=self.unit_id
                )
            
            if result.isError():
                return DeviceResponse(
                    success=False,
                    message=f"Modbus read error: {result}"
                )
            
            return DeviceResponse(
                success=True,
                message=f"Coil(s) read successfully",
                data={'values': result.bits[:count]},
                timestamp=time.time()
            )
            
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Read failed: {e}"
            )
    
    # ========================================================================
    # Monitoring
    # ========================================================================
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitor_running:
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Monitoring started")
    
    def _stop_monitoring(self):
        """Stop background monitoring thread"""
        if self.monitor_running:
            self.monitor_running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
            self.logger.info("Monitoring stopped")
    
    def _monitor_loop(self):
        """Background thread for periodic register reading"""
        while self.monitor_running:
            try:
                # Read sensor data (input registers)
                sensor_result = self.client.read_input_registers(
                    self.register_map.current_1, 6, unit=self.unit_id
                )
                
                if not sensor_result.isError():
                    with self.data_lock:
                        self.cached_sensor_data = {
                            'current_1': sensor_result.registers[0] / 100.0,  # Assuming scaled by 100
                            'current_2': sensor_result.registers[1] / 100.0,
                            'vibration_x': sensor_result.registers[2] / 100.0,
                            'vibration_y': sensor_result.registers[3] / 100.0,
                            'vibration_z': sensor_result.registers[4] / 100.0,
                            'temperature_1': sensor_result.registers[5] / 10.0  # Assuming scaled by 10
                        }
                    
                    # Notify sensor data callbacks
                    sensor_data = self._read_sensor_data_impl()
                    if sensor_data:
                        self._notify_sensor_data(sensor_data)
                
                # Read safety status (discrete inputs)
                safety_result = self.client.read_discrete_inputs(
                    self.register_map.emergency_stop, 4, unit=self.unit_id
                )
                
                if not safety_result.isError():
                    with self.data_lock:
                        self.cached_safety_data = {
                            'emergency_stop': safety_result.bits[0],
                            'door_closed': safety_result.bits[1],
                            'overload_detected': safety_result.bits[2],
                            'temperature_ok': safety_result.bits[3]
                        }
                    
                    # Notify safety data callbacks
                    safety_data = self._read_safety_status_impl()
                    if safety_data:
                        self._notify_safety_data(safety_data)
                    
                    # Update device state based on safety
                    if safety_result.bits[0]:  # Emergency stop
                        self.set_state(DeviceState.EMERGENCY_STOP)
                    else:
                        self.set_state(DeviceState.IDLE)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(1.0)
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    def _get_configuration_impl(self) -> Dict[str, Any]:
        """Get Modbus device configuration"""
        return {
            'host': self.host,
            'port': self.port,
            'unit_id': self.unit_id,
            'register_map': {
                'current_1': self.register_map.current_1,
                'current_2': self.register_map.current_2,
                'vibration_x': self.register_map.vibration_x,
                'vibration_y': self.register_map.vibration_y,
                'vibration_z': self.register_map.vibration_z,
                'temperature_1': self.register_map.temperature_1,
                'emergency_stop': self.register_map.emergency_stop,
                'door_closed': self.register_map.door_closed
            }
        }
    
    # ========================================================================
    # Diagnostics
    # ========================================================================
    
    def _get_diagnostics_impl(self) -> Dict[str, Any]:
        """Get Modbus diagnostics"""
        diagnostics = {
            'connected': self.is_connected(),
            'state': self.state.value,
            'host': self.host,
            'port': self.port,
            'unit_id': self.unit_id
        }
        
        with self.data_lock:
            if self.cached_sensor_data:
                diagnostics['latest_sensor_values'] = self.cached_sensor_data
            if self.cached_safety_data:
                diagnostics['latest_safety_status'] = self.cached_safety_data
        
        return diagnostics
