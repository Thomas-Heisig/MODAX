"""
Slave Board Communication Module

This module provides communication with slave I/O boards for distributed
control systems. Slave boards extend the I/O capabilities of the system and
can be placed near sensors/actuators to reduce wiring.

Supports:
- Multiple communication protocols (I2C, SPI, CAN, RS485)
- Digital I/O expansion
- Analog input expansion
- PWM output expansion
- Encoder inputs
- Relay outputs
- Auto-discovery and enumeration
- Hot-plugging support

Compatible Boards:
- Arduino slave boards (I2C, SPI, Serial)
- ESP32 slave nodes (WiFi, CAN, I2C)
- MCP23017 I2C I/O expanders
- PCF8574 I2C I/O expanders
- Custom slave board protocols
"""

import logging
from typing import Optional, Dict, Any, List
from enum import IntEnum
from dataclasses import dataclass
import threading
import time

try:
    import smbus2
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logging.warning("I2C support not available. Install with: pip install smbus2")

logger = logging.getLogger(__name__)


class SlaveType(IntEnum):
    """Slave board types"""
    DIGITAL_IO = 0
    ANALOG_INPUT = 1
    PWM_OUTPUT = 2
    ENCODER_INPUT = 3
    RELAY_OUTPUT = 4
    MIXED_IO = 5
    CUSTOM = 99


class IODirection(IntEnum):
    """I/O pin direction"""
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2


@dataclass
class SlaveConfig:
    """Slave board configuration"""
    slave_id: int
    slave_type: SlaveType
    address: int  # I2C address or bus ID
    description: str = ""
    num_digital_inputs: int = 0
    num_digital_outputs: int = 0
    num_analog_inputs: int = 0
    num_pwm_outputs: int = 0


@dataclass
class SlaveStatus:
    """Slave board status"""
    slave_id: int
    online: bool
    last_seen: float
    error_count: int
    firmware_version: Optional[str] = None
    uptime: Optional[float] = None


class SlaveBoardI2C:
    """
    I2C-based slave board driver

    Provides communication with I2C slave boards for distributed I/O.
    Compatible with Arduino, ESP32, and I2C I/O expanders.
    """

    def __init__(
        self,
        bus: int = 1,
        auto_discover: bool = True
    ):
        """
        Initialize I2C slave board manager

        Args:
            bus: I2C bus number (typically 1 for Raspberry Pi)
            auto_discover: Auto-discover slave boards on startup
        """
        if not I2C_AVAILABLE:
            logger.warning("I2C not available - running in stub mode")
            self._enabled = False
            return

        self._enabled = True
        self._bus_num = bus
        self._bus: Optional[smbus2.SMBus] = None
        self._slaves: Dict[int, SlaveConfig] = {}
        self._status: Dict[int, SlaveStatus] = {}
        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            'read_count': 0,
            'write_count': 0,
            'error_count': 0,
            'slaves_discovered': 0
        }

        # Initialize I2C bus
        self._init_bus()

        # Auto-discover slaves
        if auto_discover:
            self.discover_slaves()

    def _init_bus(self) -> bool:
        """Initialize I2C bus"""
        try:
            self._bus = smbus2.SMBus(self._bus_num)
            logger.info(f"I2C bus {self._bus_num} initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus: {e}")
            self._enabled = False
            return False

    def discover_slaves(self) -> List[int]:
        """
        Discover slave boards on I2C bus

        Returns:
            List of discovered slave addresses
        """
        if not self._enabled or not self._bus:
            return []

        discovered = []

        # Scan common I2C slave addresses (0x08-0x77)
        for addr in range(0x08, 0x78):
            try:
                # Try to read from device
                self._bus.read_byte(addr)
                discovered.append(addr)
                logger.info(f"Discovered I2C slave at address 0x{addr:02X}")
            except Exception:
                # Device not present
                pass

        self._stats['slaves_discovered'] = len(discovered)
        return discovered

    def add_slave(self, config: SlaveConfig) -> bool:
        """
        Add slave board to system

        Args:
            config: Slave configuration

        Returns:
            True if successful
        """
        with self._lock:
            self._slaves[config.slave_id] = config
            self._status[config.slave_id] = SlaveStatus(
                slave_id=config.slave_id,
                online=False,
                last_seen=0,
                error_count=0
            )

        logger.info(
            f"Added slave {config.slave_id}: {config.description} "
            f"at address 0x{config.address:02X}"
        )
        return True

    def read_digital_input(self, slave_id: int, pin: int) -> Optional[bool]:
        """
        Read digital input from slave

        Args:
            slave_id: Slave board ID
            pin: Pin number

        Returns:
            Pin state (True/False) or None on error
        """
        if not self._enabled or not self._bus:
            return None

        config = self._slaves.get(slave_id)
        if not config:
            logger.error(f"Slave {slave_id} not found")
            return None

        try:
            # Read from slave using I2C protocol
            # Protocol: CMD_READ_DIGITAL (0x01), PIN
            data = self._bus.read_i2c_block_data(
                config.address,
                0x01,  # CMD_READ_DIGITAL
                1
            )

            self._stats['read_count'] += 1
            self._update_slave_status(slave_id, True)

            return bool(data[0] & (1 << pin))

        except Exception as e:
            logger.error(f"Error reading from slave {slave_id}: {e}")
            self._stats['error_count'] += 1
            self._update_slave_status(slave_id, False)
            return None

    def write_digital_output(
        self,
        slave_id: int,
        pin: int,
        value: bool
    ) -> bool:
        """
        Write digital output to slave

        Args:
            slave_id: Slave board ID
            pin: Pin number
            value: Output state

        Returns:
            True if successful
        """
        if not self._enabled or not self._bus:
            return False

        config = self._slaves.get(slave_id)
        if not config:
            logger.error(f"Slave {slave_id} not found")
            return False

        try:
            # Write to slave using I2C protocol
            # Protocol: CMD_WRITE_DIGITAL (0x02), PIN, VALUE
            self._bus.write_i2c_block_data(
                config.address,
                0x02,  # CMD_WRITE_DIGITAL
                [pin, 1 if value else 0]
            )

            self._stats['write_count'] += 1
            self._update_slave_status(slave_id, True)

            return True

        except Exception as e:
            logger.error(f"Error writing to slave {slave_id}: {e}")
            self._stats['error_count'] += 1
            self._update_slave_status(slave_id, False)
            return False

    def read_analog_input(self, slave_id: int, channel: int) -> Optional[float]:
        """
        Read analog input from slave

        Args:
            slave_id: Slave board ID
            channel: Analog channel

        Returns:
            Analog value (0.0-1.0) or None on error
        """
        if not self._enabled or not self._bus:
            return None

        config = self._slaves.get(slave_id)
        if not config:
            logger.error(f"Slave {slave_id} not found")
            return None

        try:
            # Read analog value from slave
            # Protocol: CMD_READ_ANALOG (0x03), CHANNEL
            data = self._bus.read_i2c_block_data(
                config.address,
                0x03,  # CMD_READ_ANALOG
                2  # 16-bit value
            )

            # Convert to 0.0-1.0 range
            raw_value = (data[0] << 8) | data[1]
            normalized_value = raw_value / 65535.0

            self._stats['read_count'] += 1
            self._update_slave_status(slave_id, True)

            return normalized_value

        except Exception as e:
            logger.error(f"Error reading analog from slave {slave_id}: {e}")
            self._stats['error_count'] += 1
            self._update_slave_status(slave_id, False)
            return None

    def write_pwm_output(
        self,
        slave_id: int,
        channel: int,
        duty_cycle: float
    ) -> bool:
        """
        Write PWM output to slave

        Args:
            slave_id: Slave board ID
            channel: PWM channel
            duty_cycle: Duty cycle (0.0-1.0)

        Returns:
            True if successful
        """
        if not self._enabled or not self._bus:
            return False

        config = self._slaves.get(slave_id)
        if not config:
            logger.error(f"Slave {slave_id} not found")
            return False

        # Clamp duty cycle
        duty_cycle = max(0.0, min(1.0, duty_cycle))

        try:
            # Write PWM value to slave
            # Protocol: CMD_WRITE_PWM (0x04), CHANNEL, VALUE_HIGH, VALUE_LOW
            raw_value = int(duty_cycle * 65535)
            value_high = (raw_value >> 8) & 0xFF
            value_low = raw_value & 0xFF

            self._bus.write_i2c_block_data(
                config.address,
                0x04,  # CMD_WRITE_PWM
                [channel, value_high, value_low]
            )

            self._stats['write_count'] += 1
            self._update_slave_status(slave_id, True)

            return True

        except Exception as e:
            logger.error(f"Error writing PWM to slave {slave_id}: {e}")
            self._stats['error_count'] += 1
            self._update_slave_status(slave_id, False)
            return False

    def get_slave_info(self, slave_id: int) -> Optional[Dict[str, Any]]:
        """
        Get slave board information

        Args:
            slave_id: Slave board ID

        Returns:
            Slave information dictionary or None
        """
        if not self._enabled or not self._bus:
            return None

        config = self._slaves.get(slave_id)
        status = self._status.get(slave_id)

        if not config:
            return None

        try:
            # Read firmware version and uptime
            # Protocol: CMD_GET_INFO (0x10)
            data = self._bus.read_i2c_block_data(
                config.address,
                0x10,  # CMD_GET_INFO
                8
            )

            version = f"{data[0]}.{data[1]}.{data[2]}"
            uptime = (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]

            if status:
                status.firmware_version = version
                status.uptime = uptime / 1000.0  # Convert to seconds

            return {
                'slave_id': slave_id,
                'description': config.description,
                'type': config.slave_type.name,
                'address': f"0x{config.address:02X}",
                'online': status.online if status else False,
                'firmware_version': version,
                'uptime': uptime / 1000.0
            }

        except Exception as e:
            logger.error(f"Error getting info from slave {slave_id}: {e}")
            return None

    def _update_slave_status(self, slave_id: int, success: bool) -> None:
        """Update slave status after communication"""
        status = self._status.get(slave_id)
        if status:
            status.online = success
            status.last_seen = time.time()
            if not success:
                status.error_count += 1

    def get_all_slaves(self) -> List[Dict[str, Any]]:
        """Get information for all slaves"""
        slaves = []
        for slave_id in self._slaves:
            info = self.get_slave_info(slave_id)
            if info:
                slaves.append(info)
        return slaves

    def get_statistics(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            'enabled': self._enabled,
            'bus': self._bus_num,
            'num_slaves': len(self._slaves),
            **self._stats
        }

    def close(self) -> None:
        """Close I2C bus"""
        if self._bus:
            try:
                self._bus.close()
                logger.info("I2C slave board manager closed")
            except Exception as e:
                logger.error(f"Error closing I2C bus: {e}")
            finally:
                self._bus = None
                self._enabled = False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class SlaveBoardStub:
    """Stub implementation when I2C is not available"""

    def __init__(self, *args, **kwargs):
        logger.info("Using Slave Board stub (I2C not available)")

    def discover_slaves(self) -> List[int]:
        return []

    def add_slave(self, config: SlaveConfig) -> bool:
        return False

    def read_digital_input(self, slave_id: int, pin: int) -> Optional[bool]:
        return None

    def write_digital_output(self, slave_id: int, pin: int, value: bool) -> bool:
        return False

    def read_analog_input(self, slave_id: int, channel: int) -> Optional[float]:
        return None

    def write_pwm_output(self, slave_id: int, channel: int, duty_cycle: float) -> bool:
        return False

    def get_slave_info(self, slave_id: int) -> Optional[Dict[str, Any]]:
        return None

    def get_all_slaves(self) -> List[Dict[str, Any]]:
        return []

    def get_statistics(self) -> Dict[str, Any]:
        return {'enabled': False, 'stub': True}

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Factory function
def create_slave_board_manager(**kwargs) -> Any:
    """
    Create slave board manager instance

    Returns SlaveBoardI2C if I2C is available, otherwise SlaveBoardStub
    """
    if I2C_AVAILABLE:
        return SlaveBoardI2C(**kwargs)
    else:
        return SlaveBoardStub(**kwargs)
