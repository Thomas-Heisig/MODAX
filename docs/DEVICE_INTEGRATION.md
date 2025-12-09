# Extended Device Integration Guide

**Last Updated:** 2025-12-09  
**Status:** Implemented  
**Version:** 1.0

## Overview

MODAX Control Layer now supports a unified device interface for integrating various industrial devices beyond the ESP32 field layer. This enables connection to existing DIY CNC machines, 3D printers, PLCs, and Arduino-based controllers.

## Supported Devices

### 1. ESP32 Field Devices (MQTT)
- **Status**: Fully implemented
- **Communication**: MQTT
- **Use Case**: Custom sensor nodes, IoT devices

### 2. GRBL-based CNC Machines (Serial)
- **Status**: Newly implemented
- **Communication**: Serial/USB (G-Code)
- **Compatible With**:
  - GRBL v1.1+ controllers
  - Arduino CNC shields
  - DIY CNC routers and mills
  - Laser engravers
  - 3D printers with GRBL firmware
- **Features**:
  - Real-time status monitoring (10Hz)
  - G-Code command execution
  - Position tracking (machine and work coordinates)
  - Feed rate and spindle speed monitoring
  - Safety alarm detection
  - Soft reset and emergency stop

### 3. Arduino with Modbus TCP (Ethernet)
- **Status**: Newly implemented
- **Communication**: Modbus TCP over Ethernet
- **Compatible With**:
  - Arduino with Ethernet shield + Modbus library
  - Industrial PLCs with Modbus gateway
  - Modbus RTU-to-TCP converters
  - Custom Modbus devices
- **Features**:
  - Register read/write (holding, input, coils, discrete)
  - Continuous monitoring (10Hz)
  - Sensor data mapping
  - Safety status monitoring
  - Function codes 1-6, 15-16

## Architecture

### Device Interface Abstraction

All device drivers implement a common `DeviceInterface` abstract base class:

```python
from device_interface import DeviceInterface, DeviceInfo, DeviceCommand

class MyDevice(DeviceInterface):
    def connect(self, timeout: float) -> bool:
        # Implementation
        
    def disconnect(self) -> bool:
        # Implementation
        
    def _read_sensor_data_impl(self) -> Optional[SensorData]:
        # Implementation
        
    def _send_command_impl(self, command: DeviceCommand) -> DeviceResponse:
        # Implementation
```

### Benefits of Abstraction

- **Consistent API**: Same interface for all device types
- **Easy Integration**: Add new devices by implementing abstract methods
- **Unified Data Model**: Common sensor data and safety status structures
- **Callback System**: Event-driven architecture for real-time updates
- **State Management**: Standardized device state tracking

## Quick Start

### GRBL Device Example

```python
from grbl_device import GRBLDevice
from device_interface import DeviceCommand

# Create device
device = GRBLDevice(
    device_id="CNC_001",
    port="/dev/ttyUSB0",  # Linux: /dev/ttyUSB0, Windows: COM3
    baud_rate=115200
)

# Connect
if device.connect():
    print(f"Connected to {device}")
    
    # Execute G-Code
    cmd = DeviceCommand(
        command_type="gcode",
        command_data="G0 X10 Y20 Z5"  # Rapid move
    )
    response = device.send_command(cmd)
    print(f"Command result: {response.message}")
    
    # Read position
    sensor_data = device.read_sensor_data()
    if sensor_data:
        print(f"Position: X={sensor_data.values['pos_x']:.2f} "
              f"Y={sensor_data.values['pos_y']:.2f} "
              f"Z={sensor_data.values['pos_z']:.2f}")
    
    # Register callback for status changes
    def on_state_change(old_state, new_state):
        print(f"State changed: {old_state} -> {new_state}")
    
    device.register_callback('state_change', on_state_change)
    
    # Disconnect
    device.disconnect()
```

### Modbus TCP Device Example

```python
from modbus_device import ModbusTCPDevice, ModbusRegisterMap
from device_interface import DeviceCommand

# Configure register mapping
register_map = ModbusRegisterMap(
    current_1=0,  # Input register addresses
    current_2=1,
    temperature_1=5,
    emergency_stop=0,  # Discrete input addresses
    door_closed=1
)

# Create device
device = ModbusTCPDevice(
    device_id="PLC_001",
    host="192.168.1.100",
    port=502,
    unit_id=1,
    register_map=register_map
)

# Connect
if device.connect():
    print(f"Connected to {device}")
    
    # Read register
    cmd = DeviceCommand(
        command_type="read_register",
        command_data={
            "address": 100,
            "count": 5,
            "type": "holding"
        }
    )
    response = device.send_command(cmd)
    print(f"Register values: {response.data}")
    
    # Write register
    cmd = DeviceCommand(
        command_type="write_register",
        command_data={
            "address": 100,
            "value": 1500
        }
    )
    device.send_command(cmd)
    
    # Read sensor data
    sensor_data = device.read_sensor_data()
    if sensor_data:
        print(f"Current 1: {sensor_data.values['current_1']:.2f}A")
        print(f"Temperature: {sensor_data.values['temperature_1']:.1f}°C")
    
    # Disconnect
    device.disconnect()
```

## Integration with Control Layer

### Adding Device to Control Layer

```python
from control_layer import ControlLayer
from grbl_device import GRBLDevice

# Create control layer
control = ControlLayer(config)

# Create device
grbl = GRBLDevice("CNC_001", "/dev/ttyUSB0")
grbl.connect()

# Register callbacks to forward data to control layer
grbl.register_callback('sensor_data', 
    lambda data: control.aggregator.add_sensor_reading(data))
grbl.register_callback('safety_data',
    lambda data: control.aggregator.update_safety_status(data))

# Device is now integrated!
```

## Configuration

### GRBL Device Configuration

```yaml
devices:
  - type: grbl
    id: CNC_001
    port: /dev/ttyUSB0
    baud_rate: 115200
    enabled: true
```

### Modbus TCP Configuration

```yaml
devices:
  - type: modbus_tcp
    id: PLC_001
    host: 192.168.1.100
    port: 502
    unit_id: 1
    register_map:
      current_1: 0
      current_2: 1
      temperature_1: 5
    enabled: true
```

## Hardware Setup

### GRBL CNC Connection

1. **USB Connection**:
   - Connect Arduino/GRBL controller via USB
   - Identify port: `ls /dev/ttyUSB*` (Linux) or Device Manager (Windows)
   - Set permissions: `sudo usermod -a -G dialout $USER` (Linux)

2. **Software Setup**:
   - Flash GRBL firmware to Arduino (if not pre-installed)
   - Configure $ settings for your machine
   - Test with serial terminal (screen, minicom, or Universal Gcode Sender)

3. **Troubleshooting**:
   - Verify baud rate matches GRBL configuration
   - Check USB cable quality (data, not charge-only)
   - Disable Modem Manager on Linux if interfering with serial

### Arduino Modbus TCP Setup

1. **Hardware**:
   - Arduino board (Mega recommended for more memory)
   - Ethernet shield (W5100/W5500)
   - Sensors connected to analog/digital pins

2. **Software** (Arduino sketch):
```cpp
#include <SPI.h>
#include <Ethernet.h>
#include <Modbus.h>
#include <ModbusIP.h>

ModbusIP mb;

void setup() {
    // Configure Ethernet
    byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
    IPAddress ip(192, 168, 1, 100);
    Ethernet.begin(mac, ip);
    
    // Configure Modbus
    mb.server();
    
    // Add registers
    mb.addIreg(0);  // Current 1
    mb.addIreg(1);  // Current 2
    mb.addCoil(0);  // Emergency stop
}

void loop() {
    mb.task();
    
    // Update sensor values
    int current1 = analogRead(A0) * 5.0 / 1023.0 * 100;  // Scale to centamps
    int current2 = analogRead(A1) * 5.0 / 1023.0 * 100;
    mb.Ireg(0, current1);
    mb.Ireg(1, current2);
    
    // Update safety status
    mb.Coil(0, digitalRead(2));  // Emergency stop button
}
```

3. **Network Setup**:
   - Assign static IP to Arduino
   - Ensure network connectivity (ping test)
   - Configure firewall to allow Modbus TCP (port 502)

## API Endpoints

### Device Management (Future)

```http
GET /api/v1/devices
Response: List of all registered devices

GET /api/v1/devices/{device_id}
Response: Device info and current status

POST /api/v1/devices/{device_id}/command
Request: {"command_type": "gcode", "command_data": "G0 X10"}
Response: Command execution result
```

## Testing

### Unit Tests

```bash
cd python-control-layer
python -m pytest test_device_integration.py -v
```

### Manual Testing

1. **GRBL Device**:
```bash
# Terminal 1: Start MODAX control layer
python main.py

# Terminal 2: Send test commands
curl -X POST http://localhost:8000/api/v1/devices/CNC_001/command \
  -H "Content-Type: application/json" \
  -d '{"command_type": "gcode", "command_data": "?"}'
```

2. **Modbus Device**:
```bash
# Test with modpoll tool
modpoll -m tcp -a 1 -t 3 -r 0 -c 6 192.168.1.100
```

## Troubleshooting

### GRBL Issues

**Problem**: Device not connecting
- **Solution**: Check serial port permissions, verify baud rate, try different USB port

**Problem**: ALARM state on startup
- **Solution**: Send `$X` to clear alarm, or run homing cycle (`$H`)

**Problem**: Commands not executing
- **Solution**: Check GRBL buffer status, reduce feed rate, verify G-Code syntax

### Modbus Issues

**Problem**: Connection timeout
- **Solution**: Verify IP/port, check firewall, test with modpoll

**Problem**: Wrong register values
- **Solution**: Verify register mapping, check scaling factors, confirm unit ID

**Problem**: Register write fails
- **Solution**: Check register is writable (holding register), verify value range

## Future Enhancements

1. **Additional Device Types**:
   - Modbus RTU (Serial)
   - OPC UA clients
   - EtherCAT masters
   - PROFINET devices
   - MTConnect adapters

2. **Advanced Features**:
   - Device discovery (Modbus scan, UPnP)
   - Configuration wizards
   - Device templates
   - Multi-device synchronization
   - Hot-plug support

3. **Control Layer Integration**:
   - Automatic device registration from config
   - Device health monitoring
   - Failover and redundancy
   - Load balancing across devices

## References

- [GRBL Documentation](https://github.com/gnea/grbl)
- [Modbus Protocol Specification](https://www.modbus.org/)
- [pymodbus Documentation](https://pymodbus.readthedocs.io/)
- [MODAX Architecture](ARCHITECTURE.md)

## Support

For device integration issues:
1. Check device is powered and connected
2. Verify communication parameters (port, baud, IP)
3. Test with native tools (serial terminal, modpoll)
4. Review logs for detailed error messages
5. Open GitHub issue with device specs and logs
