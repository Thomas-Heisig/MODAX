# MQTT Sparkplug B Integration Guide

This document describes the implementation strategy for MQTT Sparkplug B protocol in the MODAX system for standardized IIoT communication.

**Last Updated:** 2025-12-09  
**Version:** 0.3.0  
**Status:** Implementation Guide

## Overview

Sparkplug B is a specification that provides MQTT clients and servers with a standard way to exchange data in a structured and scalable manner. It addresses many challenges in industrial IoT deployments.

### Why Sparkplug B for MODAX?

**Current MODAX MQTT:** Custom JSON messages over standard MQTT topics
**With Sparkplug B:** Standardized, optimized protocol for Industrial IoT

#### Benefits

1. **Interoperability:** Standard protocol understood by SCADA systems
2. **Efficiency:** Binary encoding with Protocol Buffers (smaller messages)
3. **State Management:** Birth/Death certificates for client state
4. **Auto-Discovery:** Automatic device and metric discovery
5. **Quality of Service:** Proper QoS handling and message ordering
6. **Timestamps:** High-resolution timestamps with microsecond precision
7. **Data Types:** Rich type system (integers, floats, strings, datasets)
8. **Aliasing:** Metric aliasing for bandwidth optimization

## Sparkplug B Concepts

### Topic Namespace

```
spBv1.0/GROUP_ID/MESSAGE_TYPE/EDGE_NODE_ID/[DEVICE_ID]
```

Example for MODAX:
```
spBv1.0/MODAX/NBIRTH/Field_Edge_001/ESP32_001
spBv1.0/MODAX/NDATA/Field_Edge_001/ESP32_001
spBv1.0/MODAX/DDATA/Field_Edge_001/ESP32_001
```

**Components:**
- `spBv1.0`: Sparkplug B version 1.0
- `GROUP_ID`: MODAX (organization/group identifier)
- `MESSAGE_TYPE`: NBIRTH, NDEATH, DBIRTH, DDEATH, NDATA, DDATA, NCMD, DCMD
- `EDGE_NODE_ID`: Field_Edge_001 (Control Layer edge node)
- `DEVICE_ID`: ESP32_001 (ESP32 field device)

### Message Types

| Type | Description | Publisher | Use Case |
|------|-------------|-----------|----------|
| NBIRTH | Node Birth | Edge Node | Node comes online |
| NDEATH | Node Death | Broker (Will) | Node goes offline |
| DBIRTH | Device Birth | Edge Node | Device connects |
| DDEATH | Device Death | Edge Node | Device disconnects |
| NDATA | Node Data | Edge Node | Node metrics update |
| DDATA | Device Data | Edge Node | Device metrics update |
| NCMD | Node Command | Control App | Command to node |
| DCMD | Device Command | Control App | Command to device |

## Architecture

```
┌─────────────────────────────────────────────────┐
│              SCADA / HMI Systems                │
│  (Subscribe to spBv1.0/MODAX/+/+/+)            │
└────────────────────┬────────────────────────────┘
                     │
                ┌────▼──────┐
                │   MQTT    │
                │  Broker   │
                └────┬──────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    ┌───▼────┐              ┌─────▼─────┐
    │ Control│              │ Control   │
    │ Layer  │              │ Layer     │
    │ (Edge  │              │ (Edge     │
    │ Node)  │              │ Node)     │
    └───┬────┘              └─────┬─────┘
        │                         │
    ┌───▼────┐              ┌─────▼─────┐
    │ ESP32  │              │ ESP32     │
    │ Device │              │ Device    │
    └────────┘              └───────────┘
```

## Implementation

### Step 1: Add Sparkplug B Libraries

#### Python Control Layer

Add to `requirements.txt`:
```
sparkplug-b>=1.0.0
protobuf>=4.25.8
```

Install:
```bash
pip install sparkplug-b
```

#### ESP32 Field Layer

Add to `platformio.ini`:
```ini
lib_deps =
    bblanchon/ArduinoJson@^6.21.0
    knolleary/PubSubClient@^2.8
    https://github.com/Cirrus-Link/sparkplug/tree/master/client_libraries/c
```

### Step 2: Implement Sparkplug B in Control Layer

Create `sparkplug_handler.py`:

```python
"""Sparkplug B MQTT Handler for MODAX Control Layer"""
from sparkplug_b import *
import paho.mqtt.client as mqtt
from datetime import datetime
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class SparkplugHandler:
    """Handles Sparkplug B protocol for MODAX"""
    
    # Sparkplug B configuration
    GROUP_ID = "MODAX"
    EDGE_NODE_ID = "Control_Layer"
    
    def __init__(self, broker_host: str, broker_port: int = 1883):
        """Initialize Sparkplug B handler
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        
        # Sequence number for ordering
        self.seq = 0
        
        # Birth/Death certificate (will message)
        self.setup_will_message()
        
        # Device registry
        self.devices: Dict[str, bool] = {}  # device_id -> is_online
        
        # Metric aliases for bandwidth optimization
        self.metric_aliases: Dict[str, int] = {
            "motor_current_1": 1,
            "motor_current_2": 2,
            "vibration_x": 3,
            "vibration_y": 4,
            "vibration_z": 5,
            "temperature": 6,
            "emergency_stop": 7,
            "door_closed": 8,
            "overload": 9,
            "temp_ok": 10
        }
        
    def setup_will_message(self):
        """Setup MQTT will message for node death"""
        death_payload = self._create_node_death()
        death_topic = f"spBv1.0/{self.GROUP_ID}/NDEATH/{self.EDGE_NODE_ID}"
        
        self.client.will_set(
            death_topic,
            death_payload,
            qos=1,
            retain=False
        )
    
    def _create_node_birth(self) -> bytes:
        """Create Node Birth certificate
        
        Returns:
            Encoded Sparkplug B NBIRTH payload
        """
        payload = getNodeBirthPayload()
        
        # Add node metrics
        addMetric(payload, "Node Control Layer", None, MetricDataType.String, 
                 "MODAX Control Layer v0.3.0")
        addMetric(payload, "bdSeq", 0, MetricDataType.Int64, 0)  # Birth/Death sequence
        
        # Add node properties
        addMetric(payload, "Properties/API_Version", None, MetricDataType.String, "v1")
        addMetric(payload, "Properties/Max_Devices", None, MetricDataType.Int32, 100)
        
        payload.timestamp = int(datetime.utcnow().timestamp() * 1000)
        payload.seq = self._get_next_seq()
        
        return bytearray(payload.SerializeToString())
    
    def _create_node_death(self) -> bytes:
        """Create Node Death certificate
        
        Returns:
            Encoded Sparkplug B NDEATH payload
        """
        payload = getNodeDeathPayload()
        addMetric(payload, "bdSeq", None, MetricDataType.Int64, 0)
        
        payload.timestamp = int(datetime.utcnow().timestamp() * 1000)
        
        return bytearray(payload.SerializeToString())
    
    def _create_device_birth(self, device_id: str) -> bytes:
        """Create Device Birth certificate
        
        Args:
            device_id: Device identifier
            
        Returns:
            Encoded Sparkplug B DBIRTH payload
        """
        payload = getDeviceBirthPayload()
        
        # Add device metrics with aliases
        addMetric(payload, "motor_current_1", 1, MetricDataType.Float, 0.0)
        addMetric(payload, "motor_current_2", 2, MetricDataType.Float, 0.0)
        addMetric(payload, "vibration_x", 3, MetricDataType.Float, 0.0)
        addMetric(payload, "vibration_y", 4, MetricDataType.Float, 0.0)
        addMetric(payload, "vibration_z", 5, MetricDataType.Float, 0.0)
        addMetric(payload, "temperature", 6, MetricDataType.Float, 0.0)
        addMetric(payload, "emergency_stop", 7, MetricDataType.Boolean, False)
        addMetric(payload, "door_closed", 8, MetricDataType.Boolean, True)
        addMetric(payload, "overload", 9, MetricDataType.Boolean, False)
        addMetric(payload, "temp_ok", 10, MetricDataType.Boolean, True)
        
        # Add device properties
        addMetric(payload, "Properties/Device_Type", None, 
                 MetricDataType.String, "ESP32")
        addMetric(payload, "Properties/Firmware_Version", None, 
                 MetricDataType.String, "1.0.0")
        
        payload.timestamp = int(datetime.utcnow().timestamp() * 1000)
        payload.seq = self._get_next_seq()
        
        return bytearray(payload.SerializeToString())
    
    def _create_device_death(self, device_id: str) -> bytes:
        """Create Device Death certificate
        
        Args:
            device_id: Device identifier
            
        Returns:
            Encoded Sparkplug B DDEATH payload
        """
        payload = getDeviceDeathPayload()
        payload.timestamp = int(datetime.utcnow().timestamp() * 1000)
        payload.seq = self._get_next_seq()
        
        return bytearray(payload.SerializeToString())
    
    def _create_device_data(self, device_id: str, sensor_data: dict) -> bytes:
        """Create Device Data message with sensor readings
        
        Args:
            device_id: Device identifier
            sensor_data: Dictionary with sensor values
            
        Returns:
            Encoded Sparkplug B DDATA payload
        """
        payload = getDdataPayload()
        
        # Use aliases for bandwidth optimization (after DBIRTH)
        if "motor_currents" in sensor_data:
            addMetric(payload, None, 1, MetricDataType.Float, 
                     sensor_data["motor_currents"][0])
            addMetric(payload, None, 2, MetricDataType.Float, 
                     sensor_data["motor_currents"][1])
        
        if "vibration" in sensor_data:
            addMetric(payload, None, 3, MetricDataType.Float, 
                     sensor_data["vibration"][0])
            addMetric(payload, None, 4, MetricDataType.Float, 
                     sensor_data["vibration"][1])
            addMetric(payload, None, 5, MetricDataType.Float, 
                     sensor_data["vibration"][2])
        
        if "temperatures" in sensor_data:
            addMetric(payload, None, 6, MetricDataType.Float, 
                     sensor_data["temperatures"][0])
        
        # Safety status
        if "safety" in sensor_data:
            addMetric(payload, None, 7, MetricDataType.Boolean,
                     sensor_data["safety"]["emergency_stop"])
            addMetric(payload, None, 8, MetricDataType.Boolean,
                     sensor_data["safety"]["door_closed"])
            addMetric(payload, None, 9, MetricDataType.Boolean,
                     sensor_data["safety"]["overload_detected"])
            addMetric(payload, None, 10, MetricDataType.Boolean,
                     sensor_data["safety"]["temperature_ok"])
        
        payload.timestamp = int(datetime.utcnow().timestamp() * 1000)
        payload.seq = self._get_next_seq()
        
        return bytearray(payload.SerializeToString())
    
    def _get_next_seq(self) -> int:
        """Get next sequence number (0-255, wraps around)
        
        Returns:
            Next sequence number
        """
        seq = self.seq
        self.seq = (self.seq + 1) % 256
        return seq
    
    def connect(self):
        """Connect to MQTT broker and publish Node Birth"""
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()
        
        # Publish Node Birth
        topic = f"spBv1.0/{self.GROUP_ID}/NBIRTH/{self.EDGE_NODE_ID}"
        payload = self._create_node_birth()
        self.client.publish(topic, payload, qos=0, retain=False)
        
        logger.info(f"Published Node Birth: {topic}")
    
    def disconnect(self):
        """Disconnect from MQTT broker (will trigger Node Death)"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def register_device(self, device_id: str):
        """Register a new device and publish Device Birth
        
        Args:
            device_id: Device identifier
        """
        if device_id not in self.devices:
            self.devices[device_id] = True
            
            # Publish Device Birth
            topic = f"spBv1.0/{self.GROUP_ID}/DBIRTH/{self.EDGE_NODE_ID}/{device_id}"
            payload = self._create_device_birth(device_id)
            self.client.publish(topic, payload, qos=0, retain=False)
            
            logger.info(f"Registered device: {device_id}")
    
    def unregister_device(self, device_id: str):
        """Unregister a device and publish Device Death
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.devices:
            # Publish Device Death
            topic = f"spBv1.0/{self.GROUP_ID}/DDEATH/{self.EDGE_NODE_ID}/{device_id}"
            payload = self._create_device_death(device_id)
            self.client.publish(topic, payload, qos=0, retain=False)
            
            del self.devices[device_id]
            logger.info(f"Unregistered device: {device_id}")
    
    def publish_device_data(self, device_id: str, sensor_data: dict):
        """Publish device sensor data
        
        Args:
            device_id: Device identifier
            sensor_data: Dictionary with sensor readings
        """
        if device_id not in self.devices:
            self.register_device(device_id)
        
        # Publish Device Data
        topic = f"spBv1.0/{self.GROUP_ID}/DDATA/{self.EDGE_NODE_ID}/{device_id}"
        payload = self._create_device_data(device_id, sensor_data)
        self.client.publish(topic, payload, qos=0, retain=False)
    
    def handle_command(self, topic: str, payload: bytes):
        """Handle incoming command (NCMD or DCMD)
        
        Args:
            topic: MQTT topic
            payload: Command payload
        """
        # Parse Sparkplug B command
        inboundPayload = Payload()
        inboundPayload.ParseFromString(payload)
        
        # Extract metrics from command
        for metric in inboundPayload.metrics:
            metric_name = metric.name
            metric_value = metric.int_value  # or float_value, bool_value, etc.
            
            logger.info(f"Received command: {metric_name} = {metric_value}")
            # Process command...
```

### Step 3: Integrate with Control Layer

Update `control_layer.py`:

```python
from sparkplug_handler import SparkplugHandler

class ControlLayer:
    def __init__(self, config):
        # ... existing initialization ...
        
        # Initialize Sparkplug B if enabled
        if config.control.sparkplug_enabled:
            self.sparkplug = SparkplugHandler(
                config.mqtt.broker_host,
                config.mqtt.broker_port
            )
            self.sparkplug.connect()
        else:
            self.sparkplug = None
    
    def on_sensor_reading(self, reading: SensorReading):
        """Handle incoming sensor reading"""
        # ... existing logic ...
        
        # Publish to Sparkplug B if enabled
        if self.sparkplug:
            sensor_data = {
                "motor_currents": reading.motor_currents,
                "vibration": reading.vibration,
                "temperatures": reading.temperatures
            }
            self.sparkplug.publish_device_data(
                reading.device_id,
                sensor_data
            )
```

### Step 4: Configuration

Add to `config.py`:

```python
@dataclass
class MQTTConfig:
    # ... existing config ...
    sparkplug_enabled: bool = field(
        default_factory=lambda: os.getenv("SPARKPLUG_ENABLED", "false").lower() == "true"
    )
    sparkplug_group_id: str = field(
        default_factory=lambda: os.getenv("SPARKPLUG_GROUP_ID", "MODAX")
    )
    sparkplug_edge_node_id: str = field(
        default_factory=lambda: os.getenv("SPARKPLUG_EDGE_NODE_ID", "Control_Layer")
    )
```

## Testing

### Unit Tests

Create `test_sparkplug_handler.py`:

```python
import unittest
from sparkplug_handler import SparkplugHandler
from sparkplug_b import *

class TestSparkplugHandler(unittest.TestCase):
    
    def setUp(self):
        self.handler = SparkplugHandler("localhost", 1883)
    
    def test_node_birth_creation(self):
        """Test Node Birth certificate creation"""
        payload_bytes = self.handler._create_node_birth()
        
        # Decode and verify
        payload = Payload()
        payload.ParseFromString(bytes(payload_bytes))
        
        self.assertGreater(payload.timestamp, 0)
        self.assertGreater(len(payload.metrics), 0)
    
    def test_device_birth_creation(self):
        """Test Device Birth certificate creation"""
        device_id = "ESP32_001"
        payload_bytes = self.handler._create_device_birth(device_id)
        
        # Decode and verify
        payload = Payload()
        payload.ParseFromString(bytes(payload_bytes))
        
        # Check for required metrics
        metric_names = [m.name for m in payload.metrics]
        self.assertIn("motor_current_1", metric_names)
        self.assertIn("vibration_x", metric_names)
    
    def test_sequence_numbering(self):
        """Test sequence number wrapping"""
        # Sequence should wrap at 256
        for i in range(300):
            seq = self.handler._get_next_seq()
            self.assertLess(seq, 256)
```

### Integration Testing with MQTT Broker

```bash
# Start MQTT broker
docker run -p 1883:1883 eclipse-mosquitto

# Subscribe to Sparkplug topics
mosquitto_sub -h localhost -t 'spBv1.0/MODAX/#' -v

# Run tests
python -m unittest test_sparkplug_handler
```

## SCADA Integration

### Ignition by Inductive Automation

Ignition has native Sparkplug B support:

1. Install Ignition
2. Install MQTT Engine module
3. Configure MQTT broker connection
4. Subscribe to `spBv1.0/MODAX/#`
5. Metrics automatically appear in tag browser

### Other SCADA Systems

For SCADA systems without native Sparkplug B:

1. Use Sparkplug B to MQTT bridge
2. Convert Sparkplug B to OPC UA
3. Use Node-RED with Sparkplug B nodes

## Migration Strategy

### Phase 1: Dual Mode (Recommended)
Run both standard MQTT and Sparkplug B in parallel:

```python
# config.py
STANDARD_MQTT_ENABLED = True
SPARKPLUG_ENABLED = True

# control_layer.py
if STANDARD_MQTT_ENABLED:
    self.mqtt_handler.publish(...)

if SPARKPLUG_ENABLED:
    self.sparkplug.publish_device_data(...)
```

### Phase 2: Gradual Migration
1. Deploy Sparkplug B to dev environment
2. Validate with SCADA system
3. Deploy to staging
4. Deploy to production
5. Monitor both protocols
6. Disable standard MQTT when confident

### Phase 3: Sparkplug B Only
```python
STANDARD_MQTT_ENABLED = False
SPARKPLUG_ENABLED = True
```

## Performance Considerations

### Message Size Comparison

**Standard MQTT (JSON):**
```json
{
  "device_id": "ESP32_001",
  "timestamp": 1702134567890,
  "motor_currents": [1.5, 2.1],
  "vibration": [0.1, 0.15, 0.12],
  "temperatures": [25.3]
}
```
**Size:** ~150 bytes

**Sparkplug B (Protobuf with Aliases):**
Binary payload with metric aliases
**Size:** ~50-60 bytes (60-70% reduction)

### Bandwidth Calculation

**10 devices @ 10Hz:**
- Standard MQTT: 15 KB/s
- Sparkplug B: 5-6 KB/s (60% reduction)

## Best Practices

1. **Always Send Birth Certificates**
   - Ensures SCADA knows available metrics
   - Establishes metric aliases

2. **Use Will Messages**
   - Automatic death certificates
   - SCADA knows when connection lost

3. **Maintain Sequence Numbers**
   - Enables message ordering
   - Detects missed messages

4. **Use Metric Aliases**
   - Reduces bandwidth after DBIRTH
   - Name sent once, alias used thereafter

5. **Set Appropriate QoS**
   - QoS 0 for high-frequency data
   - QoS 1 for commands and births/deaths

## Related Documentation

- [MQTT Optimization](MQTT_OPTIMIZATION.md)
- [OPC UA Integration](OPC_UA_INTEGRATION.md)
- [External Integrations](EXTERNAL_INTEGRATIONS.md)
- [MQTT Handler](../python-control-layer/mqtt_handler.py)

## Resources

- [Sparkplug B Specification](https://sparkplug.eclipse.org/)
- [Eclipse Tahu (Reference Implementation)](https://github.com/eclipse/tahu)
- [Ignition MQTT Modules](https://inductiveautomation.com/mqtt)
- [Python Sparkplug B Library](https://pypi.org/project/sparkplug-b/)
