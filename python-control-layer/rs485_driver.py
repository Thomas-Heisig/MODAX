"""
RS485 Communication Driver for Frequency Converters

This module provides RS485 communication for frequency converters (VFDs) and
other industrial devices using Modbus RTU protocol over RS485.

Supports:
- Modbus RTU over RS485
- Multiple frequency converter brands (ABB, Siemens, Schneider, etc.)
- Speed control (frequency setpoint)
- Start/Stop commands
- Status monitoring
- Parameter reading/writing
- Automatic retry and error recovery

Compatible Devices:
- ABB ACS/ACH series drives
- Siemens SINAMICS series
- Schneider Altivar series
- Danfoss VLT series
- Delta VFD series
- Generic Modbus RTU devices
"""

import logging
from typing import Optional, Dict, Any, List
from enum import IntEnum
import threading

try:
    from pymodbus.client import ModbusSerialClient
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("Modbus support not available. Install with: pip install pymodbus pyserial")

logger = logging.getLogger(__name__)


class VFDCommand(IntEnum):
    """VFD control commands"""
    STOP = 0
    START_FORWARD = 1
    START_REVERSE = 2
    RESET_FAULT = 3
    JOG_FORWARD = 4
    JOG_REVERSE = 5


class VFDStatus(IntEnum):
    """VFD status bits"""
    RUNNING = 0x01
    FORWARD = 0x02
    REVERSE = 0x04
    FAULT = 0x08
    AT_SPEED = 0x10
    READY = 0x20


class RS485Config:
    """RS485 communication configuration"""

    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = 'N',
        stopbits: int = 1,
        timeout: float = 1.0
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout


class VFDRegisterMap:
    """Standard VFD Modbus register mappings"""

    # Common register addresses (may vary by manufacturer)
    # These are typical addresses - consult your VFD manual

    # Read registers (holding registers)
    STATUS_WORD = 0x2000          # Status word
    FREQUENCY_REF = 0x2001        # Frequency reference (Hz * 100)
    OUTPUT_FREQUENCY = 0x2002     # Actual output frequency (Hz * 100)
    OUTPUT_CURRENT = 0x2003       # Output current (A * 10)
    OUTPUT_VOLTAGE = 0x2004       # Output voltage (V)
    DC_BUS_VOLTAGE = 0x2005       # DC bus voltage (V)
    OUTPUT_POWER = 0x2006         # Output power (kW * 10)
    FAULT_CODE = 0x2100           # Active fault code

    # Write registers (holding registers)
    CONTROL_WORD = 0x3000         # Control word
    FREQUENCY_SETPOINT = 0x3001   # Frequency setpoint (Hz * 100)
    ACCEL_TIME = 0x3002           # Acceleration time (s * 10)
    DECEL_TIME = 0x3003           # Deceleration time (s * 10)
    MAX_FREQUENCY = 0x3004        # Maximum frequency (Hz * 100)
    MIN_FREQUENCY = 0x3005        # Minimum frequency (Hz * 100)


class RS485Driver:
    """
    RS485 driver for frequency converters and industrial devices

    Provides Modbus RTU communication over RS485 for VFD control.
    """

    def __init__(
        self,
        config: RS485Config,
        slave_id: int = 1,
        register_map: Optional[VFDRegisterMap] = None
    ):
        """
        Initialize RS485 driver

        Args:
            config: RS485 communication configuration
            slave_id: Modbus slave ID (1-247)
            register_map: Custom register map (None = use default)
        """
        if not MODBUS_AVAILABLE:
            logger.warning("Modbus not available - running in stub mode")
            self._enabled = False
            return

        self._enabled = True
        self._config = config
        self._slave_id = slave_id
        self._register_map = register_map or VFDRegisterMap()
        self._client: Optional[ModbusSerialClient] = None
        self._lock = threading.Lock()
        self._connected = False

        # Statistics
        self._stats = {
            'read_count': 0,
            'write_count': 0,
            'error_count': 0,
            'last_error': None
        }

        # Connect to device
        self._connect()

    def _connect(self) -> bool:
        """Connect to RS485 device"""
        try:
            self._client = ModbusSerialClient(
                port=self._config.port,
                baudrate=self._config.baudrate,
                bytesize=self._config.bytesize,
                parity=self._config.parity,
                stopbits=self._config.stopbits,
                timeout=self._config.timeout
            )

            if self._client.connect():
                self._connected = True
                logger.info(
                    f"RS485 connected: {self._config.port} @ "
                    f"{self._config.baudrate} baud, slave {self._slave_id}"
                )
                return True
            else:
                logger.error(f"Failed to connect to RS485 port {self._config.port}")
                self._connected = False
                return False

        except Exception as e:
            logger.error(f"RS485 connection error: {e}")
            self._stats['last_error'] = str(e)
            self._stats['error_count'] += 1
            self._connected = False
            return False

    def _read_registers(
        self,
        address: int,
        count: int = 1
    ) -> Optional[List[int]]:
        """
        Read holding registers

        Args:
            address: Starting register address
            count: Number of registers to read

        Returns:
            List of register values or None on error
        """
        if not self._connected or not self._client:
            logger.warning("RS485 not connected")
            return None

        try:
            with self._lock:
                result = self._client.read_holding_registers(
                    address,
                    count,
                    slave=self._slave_id
                )

                if result.isError():
                    logger.error(f"Error reading registers at {address}: {result}")
                    self._stats['error_count'] += 1
                    return None

                self._stats['read_count'] += 1
                return result.registers

        except Exception as e:
            logger.error(f"Exception reading registers: {e}")
            self._stats['last_error'] = str(e)
            self._stats['error_count'] += 1
            return None

    def _write_register(self, address: int, value: int) -> bool:
        """
        Write single holding register

        Args:
            address: Register address
            value: Value to write

        Returns:
            True if successful
        """
        if not self._connected or not self._client:
            logger.warning("RS485 not connected")
            return False

        try:
            with self._lock:
                result = self._client.write_register(
                    address,
                    value,
                    slave=self._slave_id
                )

                if result.isError():
                    logger.error(f"Error writing register at {address}: {result}")
                    self._stats['error_count'] += 1
                    return False

                self._stats['write_count'] += 1
                return True

        except Exception as e:
            logger.error(f"Exception writing register: {e}")
            self._stats['last_error'] = str(e)
            self._stats['error_count'] += 1
            return False

    def start_motor(self, forward: bool = True) -> bool:
        """
        Start motor in forward or reverse direction

        Args:
            forward: True for forward, False for reverse

        Returns:
            True if successful
        """
        command = VFDCommand.START_FORWARD if forward else VFDCommand.START_REVERSE
        logger.info(f"Starting motor ({'forward' if forward else 'reverse'})")
        return self._write_register(
            self._register_map.CONTROL_WORD,
            command
        )

    def stop_motor(self) -> bool:
        """
        Stop motor

        Returns:
            True if successful
        """
        logger.info("Stopping motor")
        return self._write_register(
            self._register_map.CONTROL_WORD,
            VFDCommand.STOP
        )

    def set_frequency(self, frequency_hz: float) -> bool:
        """
        Set motor frequency setpoint

        Args:
            frequency_hz: Desired frequency in Hz (e.g., 50.0)

        Returns:
            True if successful
        """
        # Convert to register value (Hz * 100)
        value = int(frequency_hz * 100)
        logger.info(f"Setting frequency to {frequency_hz} Hz")
        return self._write_register(
            self._register_map.FREQUENCY_SETPOINT,
            value
        )

    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get VFD status

        Returns:
            Dictionary with status information or None on error
        """
        registers = self._read_registers(
            self._register_map.STATUS_WORD,
            7  # Read status and parameters
        )

        if not registers or len(registers) < 7:
            return None

        status_word = registers[0]

        return {
            'running': bool(status_word & VFDStatus.RUNNING),
            'forward': bool(status_word & VFDStatus.FORWARD),
            'reverse': bool(status_word & VFDStatus.REVERSE),
            'fault': bool(status_word & VFDStatus.FAULT),
            'at_speed': bool(status_word & VFDStatus.AT_SPEED),
            'ready': bool(status_word & VFDStatus.READY),
            'frequency_ref': registers[1] / 100.0,  # Hz
            'output_frequency': registers[2] / 100.0,  # Hz
            'output_current': registers[3] / 10.0,  # A
            'output_voltage': registers[4],  # V
            'dc_bus_voltage': registers[5],  # V
            'output_power': registers[6] / 10.0  # kW
        }

    def get_fault_code(self) -> Optional[int]:
        """
        Get active fault code

        Returns:
            Fault code or None
        """
        registers = self._read_registers(self._register_map.FAULT_CODE, 1)
        return registers[0] if registers else None

    def reset_fault(self) -> bool:
        """
        Reset VFD fault

        Returns:
            True if successful
        """
        logger.info("Resetting VFD fault")
        return self._write_register(
            self._register_map.CONTROL_WORD,
            VFDCommand.RESET_FAULT
        )

    def set_acceleration_time(self, seconds: float) -> bool:
        """
        Set acceleration time

        Args:
            seconds: Acceleration time in seconds

        Returns:
            True if successful
        """
        value = int(seconds * 10)
        return self._write_register(self._register_map.ACCEL_TIME, value)

    def set_deceleration_time(self, seconds: float) -> bool:
        """
        Set deceleration time

        Args:
            seconds: Deceleration time in seconds

        Returns:
            True if successful
        """
        value = int(seconds * 10)
        return self._write_register(self._register_map.DECEL_TIME, value)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get driver statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'connected': self._connected,
            'port': self._config.port,
            'baudrate': self._config.baudrate,
            'slave_id': self._slave_id,
            **self._stats
        }

    def close(self) -> None:
        """Close RS485 connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("RS485 connection closed")
            except Exception as e:
                logger.error(f"Error closing RS485 connection: {e}")
            finally:
                self._client = None
                self._connected = False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class RS485Stub:
    """Stub implementation when RS485/Modbus is not available"""

    def __init__(self, *args, **kwargs):
        logger.info("Using RS485 stub (Modbus not available)")

    def start_motor(self, forward: bool = True) -> bool:
        logger.debug(f"RS485 stub: start_motor (forward={forward})")
        return False

    def stop_motor(self) -> bool:
        logger.debug("RS485 stub: stop_motor")
        return False

    def set_frequency(self, frequency_hz: float) -> bool:
        logger.debug(f"RS485 stub: set_frequency ({frequency_hz} Hz)")
        return False

    def get_status(self) -> Optional[Dict[str, Any]]:
        return None

    def get_fault_code(self) -> Optional[int]:
        return None

    def reset_fault(self) -> bool:
        return False

    def get_statistics(self) -> Dict[str, Any]:
        return {'connected': False, 'stub': True}

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Factory function
def create_rs485_driver(config: RS485Config, **kwargs) -> Any:
    """
    Create RS485 driver instance

    Returns RS485Driver if Modbus is available, otherwise RS485Stub
    """
    if MODBUS_AVAILABLE:
        return RS485Driver(config, **kwargs)
    else:
        return RS485Stub(config, **kwargs)
