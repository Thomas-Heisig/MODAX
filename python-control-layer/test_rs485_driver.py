"""Unit tests for RS485 Driver"""
import unittest
from rs485_driver import (
    RS485Config, VFDCommand, VFDStatus,
    VFDRegisterMap, RS485Stub, create_rs485_driver
)


class TestRS485Config(unittest.TestCase):
    """Test RS485 configuration"""

    def test_config_creation(self):
        """Test creating RS485 configuration"""
        config = RS485Config(
            port='/dev/ttyUSB0',
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1.0
        )

        self.assertEqual(config.port, '/dev/ttyUSB0')
        self.assertEqual(config.baudrate, 9600)
        self.assertEqual(config.bytesize, 8)
        self.assertEqual(config.parity, 'N')
        self.assertEqual(config.stopbits, 1)
        self.assertEqual(config.timeout, 1.0)

    def test_config_defaults(self):
        """Test default configuration values"""
        config = RS485Config()

        self.assertEqual(config.port, '/dev/ttyUSB0')
        self.assertEqual(config.baudrate, 9600)


class TestVFDEnums(unittest.TestCase):
    """Test VFD enumerations"""

    def test_vfd_command_enum(self):
        """Test VFD command enum values"""
        self.assertEqual(VFDCommand.STOP, 0)
        self.assertEqual(VFDCommand.START_FORWARD, 1)
        self.assertEqual(VFDCommand.START_REVERSE, 2)

    def test_vfd_status_enum(self):
        """Test VFD status enum values"""
        self.assertEqual(VFDStatus.RUNNING, 0x01)
        self.assertEqual(VFDStatus.FORWARD, 0x02)
        self.assertEqual(VFDStatus.FAULT, 0x08)


class TestRS485Stub(unittest.TestCase):
    """Test RS485 stub implementation (no hardware required)"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = RS485Config(
            port='/dev/ttyUSB0',
            baudrate=9600
        )

    def test_stub_start_motor(self):
        """Test stub start motor (always returns False)"""
        stub = RS485Stub(self.config)
        self.assertFalse(stub.start_motor())
        self.assertFalse(stub.start_motor(forward=False))

    def test_stub_stop_motor(self):
        """Test stub stop motor"""
        stub = RS485Stub(self.config)
        self.assertFalse(stub.stop_motor())

    def test_stub_set_frequency(self):
        """Test stub set frequency"""
        stub = RS485Stub(self.config)
        self.assertFalse(stub.set_frequency(50.0))
        self.assertFalse(stub.set_frequency(100.0))

    def test_stub_get_status(self):
        """Test stub get status (returns None)"""
        stub = RS485Stub(self.config)
        self.assertIsNone(stub.get_status())

    def test_stub_get_fault_code(self):
        """Test stub get fault code"""
        stub = RS485Stub(self.config)
        self.assertIsNone(stub.get_fault_code())

    def test_stub_reset_fault(self):
        """Test stub reset fault"""
        stub = RS485Stub(self.config)
        self.assertFalse(stub.reset_fault())

    def test_stub_statistics(self):
        """Test stub get statistics"""
        stub = RS485Stub(self.config)
        stats = stub.get_statistics()

        self.assertFalse(stats['connected'])
        self.assertTrue(stats['stub'])

    def test_stub_context_manager(self):
        """Test stub context manager"""
        with RS485Stub(self.config) as stub:
            stub.start_motor()
        # Should not raise any exceptions


if __name__ == '__main__':
    unittest.main()
