"""
GRBL Device Driver

This module provides a device driver for GRBL-based CNC machines and 3D printers.
GRBL is an open-source G-Code parser and CNC controller widely used in DIY CNC
and 3D printing applications.

Supports:
- Serial communication (USB/UART)
- G-Code command execution
- Real-time status monitoring
- Machine position tracking
- Feed rate control
- Spindle/extruder control
- Soft reset and safety features

Compatible with:
- GRBL v1.1 and later
- Arduino CNC Shield
- DIY CNC routers
- Laser engravers
- 3D printer controllers running GRBL
"""

import serial
import time
import threading
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from device_interface import (
    DeviceInterface, DeviceInfo, DeviceType, DeviceState,
    DeviceCapabilities, DeviceCommand, DeviceResponse,
    SensorData, SafetyData
)

# GRBL Constants
GRBL_BAUD_RATES = [115200, 250000, 19200, 9600]  # Common GRBL baud rates
GRBL_DEFAULT_BAUD = 115200
GRBL_TIMEOUT = 2.0  # Serial timeout in seconds
GRBL_STATUS_INTERVAL = 0.1  # Status query interval (10Hz)

# GRBL Real-time commands (single byte, no line ending)
GRBL_CMD_STATUS = b'?'
GRBL_CMD_CYCLE_START = b'~'
GRBL_CMD_FEED_HOLD = b'!'
GRBL_CMD_SOFT_RESET = b'\x18'  # Ctrl-X
GRBL_CMD_DOOR = b'\x84'
GRBL_CMD_JOG_CANCEL = b'\x85'
GRBL_CMD_FEED_OVR_RESET = b'\x90'
GRBL_CMD_FEED_OVR_PLUS_10 = b'\x91'
GRBL_CMD_FEED_OVR_MINUS_10 = b'\x92'
GRBL_CMD_FEED_OVR_PLUS_1 = b'\x93'
GRBL_CMD_FEED_OVR_MINUS_1 = b'\x94'

# Response patterns
GRBL_RESPONSE_OK = 'ok'
GRBL_RESPONSE_ERROR = 'error:'
GRBL_RESPONSE_ALARM = 'ALARM:'
GRBL_RESPONSE_STATUS = '<'  # Status reports start with '<'

@dataclass
class GRBLStatus:
    """Parsed GRBL status report"""
    state: str  # Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
    machine_position: Dict[str, float]  # MPos
    work_position: Dict[str, float]  # WPos
    feed_rate: float
    spindle_speed: float
    buffer_available: int
    line_number: int


class GRBLDevice(DeviceInterface):
    """
    GRBL Device Driver
    
    Communicates with GRBL-based CNC controllers via serial connection.
    Provides G-Code execution, status monitoring, and safety features.
    """
    
    def __init__(self, device_id: str, port: str, baud_rate: int = GRBL_DEFAULT_BAUD):
        """
        Initialize GRBL device
        
        Args:
            device_id: Unique device identifier
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baud_rate: Serial baud rate (default: 115200)
        """
        # Create device info
        device_info = DeviceInfo(
            device_id=device_id,
            device_type=DeviceType.GRBL_CNC,
            manufacturer="GRBL Community",
            model="GRBL Generic",
            firmware_version="unknown",
            capabilities=DeviceCapabilities(
                supports_sensor_data=True,  # Position, feed rate, etc.
                supports_safety_monitoring=True,  # Alarm states, limits
                supports_motion_control=True,
                supports_gcode=True,
                supports_configuration=True,
                supports_diagnostics=True,
                max_update_rate_hz=10.0
            ),
            connection_string=f"serial:{port}@{baud_rate}",
            metadata={"port": port, "baud_rate": baud_rate}
        )
        
        super().__init__(device_info)
        
        self.port = port
        self.baud_rate = baud_rate
        self.serial: Optional[serial.Serial] = None
        
        # Status monitoring
        self.status_thread: Optional[threading.Thread] = None
        self.status_running = False
        self.last_status: Optional[GRBLStatus] = None
        self.status_lock = threading.Lock()
        
        # Response buffer
        self.response_buffer: List[str] = []
        self.response_lock = threading.Lock()
        
        # Safety tracking
        self.alarm_active = False
        self.alarm_code = None
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def connect(self, timeout: float = 10.0) -> bool:
        """Establish serial connection to GRBL"""
        try:
            self.logger.info(f"Connecting to GRBL at {self.port}@{self.baud_rate}")
            self.set_state(DeviceState.CONNECTING)
            
            # Open serial connection
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=GRBL_TIMEOUT,
                write_timeout=GRBL_TIMEOUT
            )
            
            # Wait for GRBL initialization
            time.sleep(2.0)
            
            # Clear any startup messages
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Request version/build info
            self._send_line("$I")
            response = self._read_until_ok(timeout=2.0)
            
            # Parse version if available
            for line in response:
                if 'GRBL' in line.upper() or 'VERSION' in line.upper():
                    self.device_info.firmware_version = line.strip()
                    self.logger.info(f"Detected: {self.device_info.firmware_version}")
            
            # Check if in alarm state
            self._send_line("?")  # Request status
            time.sleep(0.1)
            status_response = self._read_available()
            if any('ALARM' in line for line in status_response):
                self.logger.warning("GRBL in ALARM state - requires homing or alarm clear")
                self.alarm_active = True
                self.set_state(DeviceState.ERROR)
            else:
                self.set_state(DeviceState.CONNECTED)
            
            # Start status monitoring thread
            self._start_status_monitoring()
            
            self.logger.info("Connected to GRBL successfully")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Serial connection failed: {e}")
            self.set_state(DeviceState.DISCONNECTED)
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}", exc_info=True)
            self.set_state(DeviceState.DISCONNECTED)
            return False
    
    def disconnect(self) -> bool:
        """Close serial connection"""
        try:
            self.logger.info("Disconnecting from GRBL")
            
            # Stop status monitoring
            self._stop_status_monitoring()
            
            # Close serial port
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            self.set_state(DeviceState.DISCONNECTED)
            self.logger.info("Disconnected from GRBL")
            return True
            
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if serial connection is active"""
        return self.serial is not None and self.serial.is_open
    
    def reconnect(self, timeout: float = 10.0) -> bool:
        """Attempt to reconnect"""
        self.disconnect()
        time.sleep(1.0)
        return self.connect(timeout)
    
    # ========================================================================
    # Data Reading
    # ========================================================================
    
    def _read_sensor_data_impl(self) -> Optional[SensorData]:
        """Read current position and status as sensor data"""
        with self.status_lock:
            if self.last_status is None:
                return None
            
            status = self.last_status
            
            return SensorData(
                device_id=self.device_info.device_id,
                timestamp=time.time(),
                values={
                    'pos_x': status.machine_position.get('X', 0.0),
                    'pos_y': status.machine_position.get('Y', 0.0),
                    'pos_z': status.machine_position.get('Z', 0.0),
                    'feed_rate': status.feed_rate,
                    'spindle_speed': status.spindle_speed,
                    'buffer_available': float(status.buffer_available),
                },
                units={
                    'pos_x': 'mm',
                    'pos_y': 'mm',
                    'pos_z': 'mm',
                    'feed_rate': 'mm/min',
                    'spindle_speed': 'RPM',
                    'buffer_available': 'blocks'
                },
                metadata={
                    'state': status.state,
                    'work_position': status.work_position,
                    'line_number': status.line_number
                }
            )
    
    def _read_safety_status_impl(self) -> Optional[SafetyData]:
        """Read safety status from GRBL"""
        with self.status_lock:
            if self.last_status is None:
                return None
            
            status = self.last_status
            is_alarm = status.state in ['Alarm', 'Door']
            
            return SafetyData(
                device_id=self.device_info.device_id,
                timestamp=time.time(),
                is_safe=not is_alarm,
                emergency_stop_active=status.state == 'Alarm',
                door_open=status.state == 'Door',
                overload_detected=False,  # GRBL doesn't report this directly
                temperature_ok=True,  # GRBL doesn't have temp monitoring
                safety_flags={
                    'alarm_active': is_alarm,
                    'homing_required': self.alarm_active,
                    'feed_hold': status.state == 'Hold'
                },
                metadata={
                    'state': status.state,
                    'alarm_code': self.alarm_code
                }
            )
    
    # ========================================================================
    # Command Execution
    # ========================================================================
    
    def _send_command_impl(self, command: DeviceCommand) -> DeviceResponse:
        """Send command to GRBL"""
        try:
            if command.command_type == "gcode":
                return self._execute_gcode(command.command_data, command.timeout_seconds)
            elif command.command_type == "realtime":
                return self._execute_realtime_command(command.command_data)
            elif command.command_type == "setting":
                return self._set_grbl_setting(command.command_data)
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
    
    def _execute_gcode(self, gcode: str, timeout: float) -> DeviceResponse:
        """Execute G-Code command"""
        self.logger.debug(f"Executing G-Code: {gcode}")
        
        # Send G-Code
        self._send_line(gcode)
        
        # Wait for response
        response_lines = self._read_until_ok(timeout)
        
        # Check for errors
        errors = [line for line in response_lines if 'error' in line.lower()]
        if errors:
            return DeviceResponse(
                success=False,
                message=f"G-Code error: {errors[0]}",
                data={'response': response_lines}
            )
        
        return DeviceResponse(
            success=True,
            message="G-Code executed successfully",
            data={'response': response_lines},
            timestamp=time.time()
        )
    
    def _execute_realtime_command(self, cmd: str) -> DeviceResponse:
        """Execute real-time command (single byte, no line ending)"""
        cmd_map = {
            'status': GRBL_CMD_STATUS,
            'cycle_start': GRBL_CMD_CYCLE_START,
            'feed_hold': GRBL_CMD_FEED_HOLD,
            'soft_reset': GRBL_CMD_SOFT_RESET,
            'door': GRBL_CMD_DOOR,
            'jog_cancel': GRBL_CMD_JOG_CANCEL
        }
        
        if cmd not in cmd_map:
            return DeviceResponse(
                success=False,
                message=f"Unknown realtime command: {cmd}"
            )
        
        try:
            self.serial.write(cmd_map[cmd])
            self.serial.flush()
            return DeviceResponse(
                success=True,
                message=f"Realtime command '{cmd}' sent",
                timestamp=time.time()
            )
        except Exception as e:
            return DeviceResponse(
                success=False,
                message=f"Failed to send realtime command: {e}"
            )
    
    def _set_grbl_setting(self, setting: Dict[str, Any]) -> DeviceResponse:
        """Set GRBL $ setting"""
        param = setting.get('parameter')
        value = setting.get('value')
        
        if param is None or value is None:
            return DeviceResponse(
                success=False,
                message="Setting requires 'parameter' and 'value'"
            )
        
        # Send setting command
        setting_cmd = f"${param}={value}"
        self._send_line(setting_cmd)
        response = self._read_until_ok(timeout=2.0)
        
        errors = [line for line in response if 'error' in line.lower()]
        if errors:
            return DeviceResponse(
                success=False,
                message=f"Setting error: {errors[0]}"
            )
        
        return DeviceResponse(
            success=True,
            message=f"Setting ${param} set to {value}",
            timestamp=time.time()
        )
    
    # ========================================================================
    # Status Monitoring
    # ========================================================================
    
    def _start_status_monitoring(self):
        """Start background status monitoring thread"""
        if not self.status_running:
            self.status_running = True
            self.status_thread = threading.Thread(target=self._status_loop, daemon=True)
            self.status_thread.start()
            self.logger.info("Status monitoring started")
    
    def _stop_status_monitoring(self):
        """Stop background status monitoring thread"""
        if self.status_running:
            self.status_running = False
            if self.status_thread:
                self.status_thread.join(timeout=2.0)
            self.logger.info("Status monitoring stopped")
    
    def _status_loop(self):
        """Background thread for periodic status queries"""
        while self.status_running:
            try:
                # Query status
                self.serial.write(GRBL_CMD_STATUS)
                self.serial.flush()
                time.sleep(0.05)  # Brief delay for response
                
                # Read response
                status_line = self._read_line(timeout=0.1)
                if status_line and status_line.startswith('<'):
                    # Parse status
                    status = self._parse_status(status_line)
                    if status:
                        with self.status_lock:
                            old_state = self.last_status.state if self.last_status else None
                            self.last_status = status
                            
                            # Update device state
                            if status.state == 'Alarm':
                                self.set_state(DeviceState.ERROR)
                                self.alarm_active = True
                            elif status.state == 'Home':
                                self.set_state(DeviceState.HOMING)
                            elif status.state in ['Run', 'Jog']:
                                self.set_state(DeviceState.RUNNING)
                            elif status.state == 'Idle':
                                self.set_state(DeviceState.IDLE)
                            
                            # Notify callbacks if state changed
                            if old_state != status.state:
                                sensor_data = self._read_sensor_data_impl()
                                if sensor_data:
                                    self._notify_sensor_data(sensor_data)
                
                time.sleep(GRBL_STATUS_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Status monitoring error: {e}")
                time.sleep(1.0)
    
    def _parse_status(self, status_line: str) -> Optional[GRBLStatus]:
        """Parse GRBL status report"""
        try:
            # Status format: <Idle|MPos:0.000,0.000,0.000|FS:0,0>
            # Remove < and >
            status_line = status_line.strip('<>')
            
            parts = status_line.split('|')
            state = parts[0]
            
            machine_pos = {}
            work_pos = {}
            feed_rate = 0.0
            spindle_speed = 0.0
            buffer_available = 0
            line_number = 0
            
            for part in parts[1:]:
                if part.startswith('MPos:'):
                    coords = part[5:].split(',')
                    machine_pos = {
                        'X': float(coords[0]) if len(coords) > 0 else 0.0,
                        'Y': float(coords[1]) if len(coords) > 1 else 0.0,
                        'Z': float(coords[2]) if len(coords) > 2 else 0.0
                    }
                elif part.startswith('WPos:'):
                    coords = part[5:].split(',')
                    work_pos = {
                        'X': float(coords[0]) if len(coords) > 0 else 0.0,
                        'Y': float(coords[1]) if len(coords) > 1 else 0.0,
                        'Z': float(coords[2]) if len(coords) > 2 else 0.0
                    }
                elif part.startswith('FS:'):
                    values = part[3:].split(',')
                    feed_rate = float(values[0]) if len(values) > 0 else 0.0
                    spindle_speed = float(values[1]) if len(values) > 1 else 0.0
                elif part.startswith('Bf:'):
                    values = part[3:].split(',')
                    buffer_available = int(values[0]) if values else 0
                elif part.startswith('Ln:'):
                    line_number = int(part[3:])
            
            return GRBLStatus(
                state=state,
                machine_position=machine_pos,
                work_position=work_pos,
                feed_rate=feed_rate,
                spindle_speed=spindle_speed,
                buffer_available=buffer_available,
                line_number=line_number
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse status: {e}")
            return None
    
    # ========================================================================
    # Serial Communication Helpers
    # ========================================================================
    
    def _send_line(self, line: str):
        """Send line with newline"""
        if self.serial and self.serial.is_open:
            self.serial.write((line + '\n').encode('utf-8'))
            self.serial.flush()
    
    def _read_line(self, timeout: float = GRBL_TIMEOUT) -> Optional[str]:
        """Read single line from serial"""
        if self.serial and self.serial.is_open:
            old_timeout = self.serial.timeout
            self.serial.timeout = timeout
            try:
                line = self.serial.readline().decode('utf-8').strip()
                return line if line else None
            finally:
                self.serial.timeout = old_timeout
        return None
    
    def _read_available(self) -> List[str]:
        """Read all available lines"""
        lines = []
        while self.serial and self.serial.in_waiting > 0:
            line = self._read_line(timeout=0.1)
            if line:
                lines.append(line)
        return lines
    
    def _read_until_ok(self, timeout: float) -> List[str]:
        """Read lines until 'ok' or timeout"""
        lines = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = self._read_line(timeout=0.1)
            if line:
                lines.append(line)
                if line.lower() == 'ok':
                    break
                if 'error' in line.lower():
                    break
            time.sleep(0.01)
        
        return lines
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    def _get_configuration_impl(self) -> Dict[str, Any]:
        """Get GRBL $ settings"""
        self._send_line("$$")
        response = self._read_until_ok(timeout=3.0)
        
        settings = {}
        for line in response:
            if line.startswith('$'):
                # Parse $123=45.6 format
                match = re.match(r'\$(\d+)=(.+)', line)
                if match:
                    param = int(match.group(1))
                    value = match.group(2)
                    settings[f"${param}"] = value
        
        return settings
    
    # ========================================================================
    # Diagnostics
    # ========================================================================
    
    def _get_diagnostics_impl(self) -> Dict[str, Any]:
        """Get GRBL diagnostics"""
        diagnostics = {
            'connected': self.is_connected(),
            'state': self.state.value,
            'alarm_active': self.alarm_active,
            'firmware_version': self.device_info.firmware_version
        }
        
        if self.last_status:
            diagnostics.update({
                'grbl_state': self.last_status.state,
                'machine_position': self.last_status.machine_position,
                'feed_rate': self.last_status.feed_rate,
                'spindle_speed': self.last_status.spindle_speed,
                'buffer_available': self.last_status.buffer_available
            })
        
        return diagnostics
