"""
Unit tests for Network Scanner module
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from network_scanner import NetworkScanner, PortScanner, NetworkDevice


class TestNetworkDevice(unittest.TestCase):
    """Test NetworkDevice class"""
    
    def test_device_creation(self):
        """Test basic device creation"""
        device = NetworkDevice(ip="192.168.1.1", hostname="test-device")
        self.assertEqual(device.ip, "192.168.1.1")
        self.assertEqual(device.hostname, "test-device")
        self.assertEqual(device.open_ports, [])
        self.assertEqual(device.device_type, "Unknown")
    
    def test_device_to_dict(self):
        """Test device serialization to dictionary"""
        device = NetworkDevice(
            ip="192.168.1.1",
            hostname="test-device",
            open_ports=[80, 443]
        )
        device_dict = device.to_dict()
        
        self.assertEqual(device_dict["ip"], "192.168.1.1")
        self.assertEqual(device_dict["hostname"], "test-device")
        self.assertEqual(device_dict["open_ports"], [80, 443])
        self.assertIn("discovered_at", device_dict)


class TestNetworkScanner(unittest.TestCase):
    """Test NetworkScanner class"""
    
    def setUp(self):
        """Set up test scanner"""
        self.scanner = NetworkScanner(timeout=0.1)
    
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        self.assertEqual(self.scanner.timeout, 0.1)
        self.assertEqual(self.scanner.discovered_devices, [])
    
    def test_identify_device_type(self):
        """Test device type identification based on ports"""
        # Modbus device
        device_type = self.scanner._identify_device_type([502])
        self.assertEqual(device_type, "Modbus Device")
        
        # OPC UA device
        device_type = self.scanner._identify_device_type([44818])
        self.assertEqual(device_type, "OPC UA Device")
        
        # MODAX Control System
        device_type = self.scanner._identify_device_type([8000, 8001])
        self.assertEqual(device_type, "MODAX Control System")
        
        # Web server
        device_type = self.scanner._identify_device_type([80, 443])
        self.assertEqual(device_type, "Web Server")
        
        # SSH device
        device_type = self.scanner._identify_device_type([22])
        self.assertEqual(device_type, "SSH Device")
        
        # Unknown device
        device_type = self.scanner._identify_device_type([12345])
        self.assertEqual(device_type, "Unknown Device")
    
    @patch('socket.gethostbyaddr')
    async def test_resolve_hostname(self, mock_gethostbyaddr):
        """Test hostname resolution"""
        mock_gethostbyaddr.return_value = ("test-host", [], ["192.168.1.1"])
        
        hostname = await self.scanner.resolve_hostname("192.168.1.1")
        self.assertEqual(hostname, "test-host")
        mock_gethostbyaddr.assert_called_once_with("192.168.1.1")
    
    @patch('socket.gethostbyaddr')
    async def test_resolve_hostname_failure(self, mock_gethostbyaddr):
        """Test hostname resolution failure"""
        mock_gethostbyaddr.side_effect = Exception("DNS error")
        
        hostname = await self.scanner.resolve_hostname("192.168.1.1")
        self.assertIsNone(hostname)
    
    def test_get_discovered_devices(self):
        """Test getting discovered devices as dictionaries"""
        device1 = NetworkDevice(ip="192.168.1.1", hostname="device1")
        device2 = NetworkDevice(ip="192.168.1.2", hostname="device2")
        self.scanner.discovered_devices = [device1, device2]
        
        devices = self.scanner.get_discovered_devices()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["ip"], "192.168.1.1")
        self.assertEqual(devices[1]["ip"], "192.168.1.2")


class TestPortScanner(unittest.TestCase):
    """Test PortScanner class"""
    
    def setUp(self):
        """Set up test scanner"""
        self.scanner = PortScanner(timeout=0.1)
    
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        self.assertEqual(self.scanner.timeout, 0.1)
    
    @patch('socket.socket')
    async def test_scan_port_open(self, mock_socket):
        """Test scanning an open port"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0  # Port is open
        mock_socket.return_value = mock_sock
        
        is_open = await self.scanner.scan_port("192.168.1.1", 80)
        self.assertTrue(is_open)
    
    @patch('socket.socket')
    async def test_scan_port_closed(self, mock_socket):
        """Test scanning a closed port"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Port is closed
        mock_socket.return_value = mock_sock
        
        is_open = await self.scanner.scan_port("192.168.1.1", 80)
        self.assertFalse(is_open)
    
    def test_get_service_info(self):
        """Test getting service info for known ports"""
        # Test some well-known ports
        service = self.scanner.get_service_info(80)
        self.assertIsNotNone(service)
        
        service = self.scanner.get_service_info(443)
        self.assertIsNotNone(service)
        
        # Unknown port should return a string with port number
        service = self.scanner.get_service_info(99999)
        self.assertIn("99999", service)


def async_test(coro):
    """Decorator to run async tests"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


# Run async tests
for name in dir(TestNetworkScanner):
    if name.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestNetworkScanner, name)):
        setattr(TestNetworkScanner, name, async_test(getattr(TestNetworkScanner, name)))

for name in dir(TestPortScanner):
    if name.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestPortScanner, name)):
        setattr(TestPortScanner, name, async_test(getattr(TestPortScanner, name)))


if __name__ == '__main__':
    unittest.main()
