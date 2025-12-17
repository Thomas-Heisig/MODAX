"""
Network Scanner Module for MODAX
Provides network discovery and device detection capabilities
"""
import socket
import ipaddress
from typing import List, Dict, Optional, Tuple
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NetworkDevice:
    """Represents a discovered network device"""
    
    def __init__(self, ip: str, hostname: Optional[str] = None,
                 mac: Optional[str] = None, open_ports: Optional[List[int]] = None):
        self.ip = ip
        self.hostname = hostname or ip
        self.mac = mac
        self.open_ports = open_ports or []
        self.discovered_at = datetime.now()
        self.device_type = "Unknown"
        self.vendor = None
        
    def to_dict(self) -> Dict:
        """Convert device to dictionary"""
        return {
            "ip": self.ip,
            "hostname": self.hostname,
            "mac": self.mac,
            "open_ports": self.open_ports,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "discovered_at": self.discovered_at.isoformat()
        }


class NetworkScanner:
    """Network scanner for device discovery"""
    
    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout
        self.discovered_devices: List[NetworkDevice] = []
        
    async def ping_host(self, ip: str) -> bool:
        """
        Check if a host is reachable using socket connection
        Returns True if host responds, False otherwise
        """
        try:
            # Try to connect to common ports
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, 80))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve IP to hostname"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return None
    
    async def scan_network_range(self, network: str) -> List[NetworkDevice]:
        """
        Scan a network range for active hosts
        network: CIDR notation (e.g., "192.168.1.0/24")
        """
        try:
            network_obj = ipaddress.ip_network(network, strict=False)
            logger.info(f"Scanning network {network} ({network_obj.num_addresses} addresses)")
            
            devices = []
            tasks = []
            
            # Create scan tasks for all hosts in range
            for ip in network_obj.hosts():
                tasks.append(self._scan_host(str(ip)))
            
            # Execute scans concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in results:
                if isinstance(result, NetworkDevice):
                    devices.append(result)
            
            self.discovered_devices = devices
            logger.info(f"Scan complete. Found {len(devices)} active devices")
            return devices
            
        except Exception as e:
            logger.error(f"Error scanning network {network}: {e}")
            return []
    
    async def _scan_host(self, ip: str) -> Optional[NetworkDevice]:
        """Scan a single host"""
        try:
            # Try common ports to detect if host is alive
            ports_to_check = [80, 443, 22, 23, 8000, 8001, 502, 44818]  # Include Modbus and OPC UA
            is_alive = False
            open_ports = []
            
            for port in ports_to_check:
                # Create a new socket for each port check
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    is_alive = True
                    open_ports.append(port)
            
            if not is_alive:
                return None
            
            # Resolve hostname
            hostname = await self.resolve_hostname(ip)
            
            # Create device object
            device = NetworkDevice(ip=ip, hostname=hostname, open_ports=open_ports)
            
            # Try to identify device type based on open ports
            device.device_type = self._identify_device_type(open_ports)
            
            logger.debug(f"Found device: {ip} ({hostname}) - Type: {device.device_type}")
            return device
            
        except Exception as e:
            logger.debug(f"Error scanning {ip}: {e}")
            return None
    
    def _identify_device_type(self, open_ports: List[int]) -> str:
        """Identify device type based on open ports"""
        if 502 in open_ports:
            return "Modbus Device"
        elif 44818 in open_ports or 4840 in open_ports:
            return "OPC UA Device"
        elif 8000 in open_ports and 8001 in open_ports:
            return "MODAX Control System"
        elif 8000 in open_ports:
            return "MODAX Control Layer"
        elif 8001 in open_ports:
            return "MODAX AI Layer"
        elif 80 in open_ports or 443 in open_ports:
            return "Web Server"
        elif 22 in open_ports:
            return "SSH Device"
        elif 23 in open_ports:
            return "Telnet Device"
        else:
            return "Unknown Device"
    
    async def scan_subnet(self, interface: Optional[str] = None) -> List[NetworkDevice]:
        """
        Scan the local subnet
        If interface is not specified, uses the default gateway's subnet
        """
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Calculate subnet
            network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
            logger.info(f"Scanning local subnet: {network}")
            
            return await self.scan_network_range(str(network))
            
        except Exception as e:
            logger.error(f"Error scanning subnet: {e}")
            return []
    
    def get_discovered_devices(self) -> List[Dict]:
        """Get list of discovered devices as dictionaries"""
        return [device.to_dict() for device in self.discovered_devices]
    
    async def quick_scan(self, hosts: List[str]) -> List[NetworkDevice]:
        """
        Quick scan of specific hosts
        hosts: List of IP addresses or hostnames
        """
        logger.info(f"Quick scanning {len(hosts)} hosts")
        tasks = [self._scan_host(host) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        devices = []
        for result in results:
            if isinstance(result, NetworkDevice):
                devices.append(result)
        
        logger.info(f"Quick scan complete. Found {len(devices)} active devices")
        return devices


class PortScanner:
    """Port scanner for service detection"""
    
    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout
        
    async def scan_port(self, host: str, port: int) -> bool:
        """Check if a specific port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def scan_ports(self, host: str, ports: List[int]) -> Dict[int, bool]:
        """
        Scan multiple ports on a host
        Returns dictionary of port -> is_open
        """
        logger.info(f"Scanning {len(ports)} ports on {host}")
        tasks = [self.scan_port(host, port) for port in ports]
        results = await asyncio.gather(*tasks)
        
        port_status = {port: is_open for port, is_open in zip(ports, results)}
        open_ports = [port for port, is_open in port_status.items() if is_open]
        logger.info(f"Found {len(open_ports)} open ports on {host}")
        
        return port_status
    
    async def scan_common_ports(self, host: str) -> Dict[int, Tuple[bool, str]]:
        """
        Scan common ports and identify services
        Returns dictionary of port -> (is_open, service_name)
        """
        common_ports = {
            20: "FTP Data",
            21: "FTP Control",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            502: "Modbus TCP",
            1883: "MQTT",
            3306: "MySQL",
            5432: "PostgreSQL",
            8000: "HTTP Alt (Control Layer)",
            8001: "HTTP Alt (AI Layer)",
            8080: "HTTP Proxy",
            8883: "MQTT TLS",
            4840: "OPC UA",
            44818: "OPC UA Discovery"
        }
        
        logger.info(f"Scanning common ports on {host}")
        port_list = list(common_ports.keys())
        tasks = [self.scan_port(host, port) for port in port_list]
        results = await asyncio.gather(*tasks)
        
        services = {}
        for port, is_open in zip(port_list, results):
            service_name = common_ports[port]
            services[port] = (is_open, service_name)
        
        open_count = sum(1 for is_open, _ in services.values() if is_open)
        logger.info(f"Found {open_count} open ports on {host}")
        
        return services
    
    async def scan_range(self, host: str, start_port: int, end_port: int) -> List[int]:
        """
        Scan a range of ports
        Returns list of open ports
        """
        ports = list(range(start_port, end_port + 1))
        logger.info(f"Scanning ports {start_port}-{end_port} on {host}")
        
        port_status = await self.scan_ports(host, ports)
        open_ports = [port for port, is_open in port_status.items() if is_open]
        
        logger.info(f"Found {len(open_ports)} open ports on {host}")
        return open_ports
    
    def get_service_info(self, port: int) -> str:
        """Get service information for a port number"""
        try:
            service = socket.getservbyport(port)
            return service
        except Exception:
            return f"Unknown (Port {port})"
