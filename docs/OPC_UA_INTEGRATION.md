# MODAX OPC UA Integration Guide

## Overview
OPC UA (Open Platform Communications Unified Architecture) is the industry standard for industrial communication. This document describes how to integrate MODAX with OPC UA servers and clients for interoperability with other industrial systems.

## OPC UA Architecture in MODAX

```
┌─────────────────────────────────────────────────────────────┐
│ External Systems                                             │
│ - SCADA (WinCC, Ignition)                                   │
│ - MES Systems                                               │
│ - PLCs with OPC UA                                          │
└────────────────┬────────────────────────────────────────────┘
                 │ OPC UA Client connections
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ MODAX OPC UA Server                                         │
│ - Exposes MODAX data via OPC UA                             │
│ - Namespace: urn:modax:server                               │
│ - Security: Sign & Encrypt (SecurityPolicy: Basic256Sha256) │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ MODAX Control Layer                                         │
│ - OPC UA Server component                                   │
│ - OPC UA Client component (optional)                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ MODAX Data Sources                                          │
│ - ESP32 devices (via MQTT)                                  │
│ - TimescaleDB (historical data)                             │
│ - AI Layer (predictions)                                    │
└─────────────────────────────────────────────────────────────┘
```

## OPC UA Server Implementation

### Python Library Selection
We recommend **asyncua** (formerly FreeOpcUa) for Python OPC UA implementation.

```bash
pip install asyncua
```

### OPC UA Server Component

#### opcua_server.py
```python
# python-control-layer/opcua_server.py
import asyncio
import logging
from asyncua import Server, ua
from asyncua.common.node import Node
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MODAXOpcUaServer:
    """OPC UA Server for MODAX System"""
    
    def __init__(self, endpoint: str = "opc.tcp://0.0.0.0:4840", name: str = "MODAX OPC UA Server"):
        self.endpoint = endpoint
        self.name = name
        self.server: Optional[Server] = None
        self.namespace_idx = None
        self.device_nodes: Dict[str, Node] = {}
        
    async def init(self):
        """Initialize OPC UA server"""
        self.server = Server()
        await self.server.init()
        
        # Set server properties
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(self.name)
        
        # Set security policies
        await self.setup_security()
        
        # Set up namespace
        self.namespace_idx = await self.server.register_namespace("urn:modax:server")
        
        # Create root objects
        await self.setup_object_model()
        
        logger.info(f"OPC UA Server initialized at {self.endpoint}")
    
    async def setup_security(self):
        """Configure OPC UA security"""
        # Load server certificate and key
        await self.server.load_certificate("certs/server_cert.der")
        await self.server.load_private_key("certs/server_key.pem")
        
        # Set security policies
        self.server.set_security_policy([
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
        ])
        
        # Set user authentication
        # Option 1: Anonymous
        self.server.set_security_IDs(["Anonymous"])
        
        # Option 2: Username/Password (recommended)
        # self.server.set_security_IDs(["Username"])
        # def user_manager(isession, username, password):
        #     if username == "admin" and password == "secure_password":
        #         return True
        #     return False
        # self.server.user_manager.set_user_manager(user_manager)
    
    async def setup_object_model(self):
        """Create OPC UA object model"""
        objects = self.server.get_objects_node()
        
        # Create MODAX root folder
        modax_root = await objects.add_folder(self.namespace_idx, "MODAX")
        
        # Create Devices folder
        devices_folder = await modax_root.add_folder(self.namespace_idx, "Devices")
        
        # Create System folder
        system_folder = await modax_root.add_folder(self.namespace_idx, "System")
        
        # System status variables
        await system_folder.add_variable(self.namespace_idx, "Status", "Running")
        await system_folder.add_variable(self.namespace_idx, "ConnectedDevices", 0)
        await system_folder.add_variable(self.namespace_idx, "Timestamp", datetime.utcnow())
        
        # Store references
        self.devices_folder = devices_folder
        self.system_folder = system_folder
    
    async def add_device(self, device_id: str):
        """Add a device to OPC UA namespace"""
        if device_id in self.device_nodes:
            logger.warning(f"Device {device_id} already exists in OPC UA namespace")
            return
        
        # Create device folder
        device_node = await self.devices_folder.add_folder(self.namespace_idx, device_id)
        
        # Create device variables
        variables = {
            "DeviceID": await device_node.add_variable(self.namespace_idx, "DeviceID", device_id),
            "Status": await device_node.add_variable(self.namespace_idx, "Status", "Unknown"),
            "Current_A": await device_node.add_variable(self.namespace_idx, "Current_A", 0.0),
            "Current_B": await device_node.add_variable(self.namespace_idx, "Current_B", 0.0),
            "Current_C": await device_node.add_variable(self.namespace_idx, "Current_C", 0.0),
            "Vibration": await device_node.add_variable(self.namespace_idx, "Vibration", 0.0),
            "Temperature": await device_node.add_variable(self.namespace_idx, "Temperature", 0.0),
            "RPM": await device_node.add_variable(self.namespace_idx, "RPM", 0),
            "PowerKW": await device_node.add_variable(self.namespace_idx, "PowerKW", 0.0),
            "IsSafe": await device_node.add_variable(self.namespace_idx, "IsSafe", True),
            "LastUpdate": await device_node.add_variable(self.namespace_idx, "LastUpdate", datetime.utcnow()),
        }
        
        # Make variables writable (for control commands)
        # await variables["Status"].set_writable()
        
        # AI Analysis folder
        ai_folder = await device_node.add_folder(self.namespace_idx, "AI_Analysis")
        ai_variables = {
            "IsAnomaly": await ai_folder.add_variable(self.namespace_idx, "IsAnomaly", False),
            "AnomalyScore": await ai_folder.add_variable(self.namespace_idx, "AnomalyScore", 0.0),
            "WearPercentage": await ai_folder.add_variable(self.namespace_idx, "WearPercentage", 0.0),
            "RemainingHours": await ai_folder.add_variable(self.namespace_idx, "RemainingHours", 0),
            "Confidence": await ai_folder.add_variable(self.namespace_idx, "Confidence", 0.0),
        }
        
        variables.update(ai_variables)
        
        self.device_nodes[device_id] = {
            "node": device_node,
            "variables": variables
        }
        
        logger.info(f"Added device {device_id} to OPC UA namespace")
    
    async def update_device_data(self, device_id: str, data: Dict):
        """Update device data in OPC UA namespace"""
        if device_id not in self.device_nodes:
            await self.add_device(device_id)
        
        variables = self.device_nodes[device_id]["variables"]
        
        # Update sensor data
        if "current_a" in data:
            await variables["Current_A"].write_value(float(data["current_a"]))
        if "current_b" in data:
            await variables["Current_B"].write_value(float(data["current_b"]))
        if "current_c" in data:
            await variables["Current_C"].write_value(float(data["current_c"]))
        if "vibration" in data:
            await variables["Vibration"].write_value(float(data["vibration"]))
        if "temperature" in data:
            await variables["Temperature"].write_value(float(data["temperature"]))
        if "rpm" in data:
            await variables["RPM"].write_value(int(data["rpm"]))
        if "power_kw" in data:
            await variables["PowerKW"].write_value(float(data["power_kw"]))
        if "is_safe" in data:
            await variables["IsSafe"].write_value(bool(data["is_safe"]))
        
        # Update timestamp
        await variables["LastUpdate"].write_value(datetime.utcnow())
    
    async def update_ai_analysis(self, device_id: str, analysis: Dict):
        """Update AI analysis data in OPC UA namespace"""
        if device_id not in self.device_nodes:
            return
        
        variables = self.device_nodes[device_id]["variables"]
        
        if "is_anomaly" in analysis:
            await variables["IsAnomaly"].write_value(bool(analysis["is_anomaly"]))
        if "anomaly_score" in analysis:
            await variables["AnomalyScore"].write_value(float(analysis["anomaly_score"]))
        if "wear_percentage" in analysis:
            await variables["WearPercentage"].write_value(float(analysis["wear_percentage"]))
        if "remaining_hours" in analysis:
            await variables["RemainingHours"].write_value(int(analysis["remaining_hours"]))
        if "confidence" in analysis:
            await variables["Confidence"].write_value(float(analysis["confidence"]))
    
    async def start(self):
        """Start OPC UA server"""
        await self.server.start()
        logger.info(f"OPC UA Server started at {self.endpoint}")
    
    async def stop(self):
        """Stop OPC UA server"""
        await self.server.stop()
        logger.info("OPC UA Server stopped")

# Global OPC UA server instance
opcua_server = MODAXOpcUaServer()

async def init_opcua_server():
    """Initialize and start OPC UA server"""
    await opcua_server.init()
    await opcua_server.start()

async def stop_opcua_server():
    """Stop OPC UA server"""
    await opcua_server.stop()
```

### Integration with Control Layer

#### main.py (Modified)
```python
# python-control-layer/main.py
import asyncio
from control_layer import ControlLayer
from opcua_server import init_opcua_server, stop_opcua_server, opcua_server
import signal

async def main():
    """Main entry point"""
    
    # Initialize OPC UA server
    await init_opcua_server()
    
    # Initialize Control Layer
    control = ControlLayer()
    control.start()
    
    # Register callback to update OPC UA when new data arrives
    def on_sensor_data(device_id, data):
        asyncio.create_task(opcua_server.update_device_data(device_id, data))
    
    def on_ai_analysis(device_id, analysis):
        asyncio.create_task(opcua_server.update_ai_analysis(device_id, analysis))
    
    control.register_sensor_callback(on_sensor_data)
    control.register_ai_callback(on_ai_analysis)
    
    # Handle shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(control)))
    
    # Keep running
    await asyncio.Event().wait()

async def shutdown(control):
    """Graceful shutdown"""
    logger.info("Shutting down...")
    control.stop()
    await stop_opcua_server()
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## OPC UA Client Implementation

### Connecting to External OPC UA Servers

#### opcua_client.py
```python
# python-control-layer/opcua_client.py
import asyncio
import logging
from asyncua import Client
from asyncua import ua
from typing import Dict, List, Callable

logger = logging.getLogger(__name__)

class MODAXOpcUaClient:
    """OPC UA Client for connecting to external servers"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client: Client = None
        self.subscriptions: Dict[str, any] = {}
        
    async def connect(self):
        """Connect to OPC UA server"""
        self.client = Client(url=self.server_url)
        
        # Set security
        self.client.set_security_string("Basic256Sha256,Sign,certs/client_cert.der,certs/client_key.pem")
        
        # Connect
        await self.client.connect()
        logger.info(f"Connected to OPC UA server: {self.server_url}")
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from OPC UA server")
    
    async def read_node(self, node_id: str):
        """Read a single node value"""
        node = self.client.get_node(node_id)
        value = await node.read_value()
        return value
    
    async def write_node(self, node_id: str, value):
        """Write to a node"""
        node = self.client.get_node(node_id)
        await node.write_value(value)
        logger.info(f"Wrote {value} to node {node_id}")
    
    async def subscribe_to_nodes(self, node_ids: List[str], callback: Callable):
        """Subscribe to data changes on nodes"""
        
        class SubHandler:
            def datachange_notification(self, node, val, data):
                asyncio.create_task(callback(node, val, data))
        
        handler = SubHandler()
        subscription = await self.client.create_subscription(500, handler)
        
        for node_id in node_ids:
            node = self.client.get_node(node_id)
            await subscription.subscribe_data_change(node)
            logger.info(f"Subscribed to node: {node_id}")
        
        self.subscriptions[subscription] = node_ids
    
    async def browse_nodes(self, parent_node_id: str = "i=85"):
        """Browse nodes starting from parent"""
        node = self.client.get_node(parent_node_id)
        children = await node.get_children()
        
        nodes_info = []
        for child in children:
            node_id = child.nodeid.to_string()
            display_name = await child.read_display_name()
            node_class = await child.read_node_class()
            
            nodes_info.append({
                "node_id": node_id,
                "display_name": display_name.Text,
                "node_class": node_class
            })
        
        return nodes_info

# Example usage
async def example_opcua_client():
    """Example of using OPC UA client"""
    
    client = MODAXOpcUaClient("opc.tcp://plc.local:4840")
    
    try:
        await client.connect()
        
        # Browse nodes
        nodes = await client.browse_nodes()
        for node in nodes:
            print(f"Node: {node['display_name']} ({node['node_id']})")
        
        # Read a specific node
        value = await client.read_node("ns=2;i=1001")
        print(f"Node value: {value}")
        
        # Subscribe to data changes
        async def on_data_change(node, val, data):
            print(f"Data change: {node} = {val}")
        
        await client.subscribe_to_nodes(["ns=2;i=1001", "ns=2;i=1002"], on_data_change)
        
        # Keep running
        await asyncio.sleep(60)
        
    finally:
        await client.disconnect()
```

## OPC UA Information Model

### MODAX Namespace Structure
```
Root (ns=0;i=85)
└─ Objects (ns=0;i=85)
   └─ MODAX (ns=2;s=MODAX)
      ├─ System (ns=2;s=System)
      │  ├─ Status (ns=2;s=System.Status)
      │  ├─ ConnectedDevices (ns=2;s=System.ConnectedDevices)
      │  └─ Timestamp (ns=2;s=System.Timestamp)
      └─ Devices (ns=2;s=Devices)
         ├─ esp32_001 (ns=2;s=Devices.esp32_001)
         │  ├─ DeviceID (ns=2;s=Devices.esp32_001.DeviceID)
         │  ├─ Status (ns=2;s=Devices.esp32_001.Status)
         │  ├─ Current_A (ns=2;s=Devices.esp32_001.Current_A)
         │  ├─ Current_B (ns=2;s=Devices.esp32_001.Current_B)
         │  ├─ Current_C (ns=2;s=Devices.esp32_001.Current_C)
         │  ├─ Vibration (ns=2;s=Devices.esp32_001.Vibration)
         │  ├─ Temperature (ns=2;s=Devices.esp32_001.Temperature)
         │  ├─ RPM (ns=2;s=Devices.esp32_001.RPM)
         │  ├─ PowerKW (ns=2;s=Devices.esp32_001.PowerKW)
         │  ├─ IsSafe (ns=2;s=Devices.esp32_001.IsSafe)
         │  ├─ LastUpdate (ns=2;s=Devices.esp32_001.LastUpdate)
         │  └─ AI_Analysis (ns=2;s=Devices.esp32_001.AI_Analysis)
         │     ├─ IsAnomaly (ns=2;s=Devices.esp32_001.AI_Analysis.IsAnomaly)
         │     ├─ AnomalyScore (ns=2;s=Devices.esp32_001.AI_Analysis.AnomalyScore)
         │     ├─ WearPercentage (ns=2;s=Devices.esp32_001.AI_Analysis.WearPercentage)
         │     ├─ RemainingHours (ns=2;s=Devices.esp32_001.AI_Analysis.RemainingHours)
         │     └─ Confidence (ns=2;s=Devices.esp32_001.AI_Analysis.Confidence)
         └─ esp32_002 (...)
```

## Security Configuration

### Certificate Generation
```bash
# Generate server certificate
openssl req -x509 -newkey rsa:2048 \
    -keyout server_key.pem \
    -out server_cert.pem \
    -days 365 -nodes \
    -subj "/C=DE/ST=State/L=City/O=MODAX/CN=modax-server"

# Convert to DER format
openssl x509 -in server_cert.pem -outform der -out server_cert.der

# Generate client certificate
openssl req -x509 -newkey rsa:2048 \
    -keyout client_key.pem \
    -out client_cert.pem \
    -days 365 -nodes \
    -subj "/C=DE/ST=State/L=City/O=MODAX/CN=modax-client"

# Convert to DER format
openssl x509 -in client_cert.pem -outform der -out client_cert.der
```

### Security Policies
- **None**: No security (development only)
- **Basic256Sha256_Sign**: Message signing only
- **Basic256Sha256_SignAndEncrypt**: Message signing and encryption (recommended)

## Integration with SCADA Systems

### WinCC OPC UA Client Configuration
1. Add new connection in WinCC
2. Server URL: `opc.tcp://modax-control:4840`
3. Security Policy: Basic256Sha256_SignAndEncrypt
4. Authentication: Username/Password
5. Browse for MODAX namespace
6. Map tags to WinCC variables

### Ignition OPC UA Client Configuration
```python
# Ignition script to read from MODAX
from com.inductiveautomation.ignition.common import BasicDataset

# Read MODAX device data
device_status = system.opc.readValue("MODAX_Server", "ns=2;s=Devices.esp32_001.Status")
current_a = system.opc.readValue("MODAX_Server", "ns=2;s=Devices.esp32_001.Current_A")
temperature = system.opc.readValue("MODAX_Server", "ns=2;s=Devices.esp32_001.Temperature")

# Display in table
data = [
    ["Status", device_status.value],
    ["Current A", current_a.value],
    ["Temperature", temperature.value]
]

event.source.parent.getComponent('Table').data = system.dataset.toDataSet(["Parameter", "Value"], data)
```

## Performance Considerations

### Subscription vs Polling
- **Subscription (Recommended)**: Push data changes to clients
  - Lower network traffic
  - Real-time updates
  - More efficient
- **Polling**: Client periodically requests data
  - Higher network traffic
  - Potential delays
  - Simpler implementation

### Sampling Interval
```python
# Fast sampling for critical data (100ms)
await subscription.subscribe_data_change(critical_node, sampling_interval=100)

# Normal sampling for regular data (1s)
await subscription.subscribe_data_change(normal_node, sampling_interval=1000)

# Slow sampling for historical data (10s)
await subscription.subscribe_data_change(historical_node, sampling_interval=10000)
```

### Data Buffering
```python
# Enable buffering for unreliable networks
subscription_parameters = ua.CreateSubscriptionParameters()
subscription_parameters.RequestedPublishingInterval = 1000
subscription_parameters.RequestedLifetimeCount = 3000
subscription_parameters.RequestedMaxKeepAliveCount = 10000
subscription_parameters.MaxNotificationsPerPublish = 0
subscription_parameters.PublishingEnabled = True
subscription_parameters.Priority = 0
```

## Testing OPC UA

### UaExpert (OPC UA Client)
1. Download UaExpert from Unified Automation
2. Add server: `opc.tcp://localhost:4840`
3. Connect with appropriate security
4. Browse namespace
5. Create subscriptions
6. Monitor data changes

### Python Test Client
```python
# test_opcua.py
import asyncio
from asyncua import Client

async def test_modax_opcua():
    """Test MODAX OPC UA server"""
    
    client = Client("opc.tcp://localhost:4840")
    
    try:
        await client.connect()
        print("Connected to MODAX OPC UA Server")
        
        # Get root node
        root = client.get_root_node()
        print(f"Root: {root}")
        
        # Browse MODAX namespace
        objects = client.get_objects_node()
        modax = await objects.get_child(["2:MODAX"])
        
        # Read system status
        system = await modax.get_child(["2:System"])
        status = await system.get_child(["2:Status"])
        status_value = await status.read_value()
        print(f"System Status: {status_value}")
        
        # Read device data
        devices = await modax.get_child(["2:Devices"])
        children = await devices.get_children()
        
        for device in children:
            name = await device.read_display_name()
            print(f"\nDevice: {name.Text}")
            
            # Read temperature
            temp_node = await device.get_child(["2:Temperature"])
            temp = await temp_node.read_value()
            print(f"  Temperature: {temp}°C")
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_modax_opcua())
```

## Troubleshooting

### Common Issues

#### Certificate Errors
```
Error: BadSecurityChecksFailed
Solution: Verify certificate paths and permissions
```

#### Connection Timeout
```
Error: BadTimeout
Solution: Check firewall rules, ensure port 4840 is open
```

#### Authentication Failures
```
Error: BadUserAccessDenied
Solution: Verify username/password or certificate trust
```

### Logging
```python
# Enable detailed OPC UA logging
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("asyncua").setLevel(logging.DEBUG)
```

## References
- [OPC Foundation](https://opcfoundation.org/)
- [asyncua Documentation](https://github.com/FreeOpcUa/opcua-asyncio)
- [OPC UA Specification](https://reference.opcfoundation.org/)
- [OPC UA Security Best Practices](https://opcfoundation.org/about/opc-technologies/opc-ua/security/)

---
**Last Updated:** 2024-12-06  
**Maintained By:** MODAX Integration Team
