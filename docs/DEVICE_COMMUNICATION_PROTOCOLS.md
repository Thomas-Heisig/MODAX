# MODAX Device Communication Protocols

## Overview

This document describes the communication protocols supported by MODAX for integration with industrial devices, frequency converters, pendant controls, and distributed I/O systems.

**Version:** 0.4.0  
**Last Updated:** 2025-12-17

---

## Supported Protocols

### 1. RS485/Modbus RTU

RS485 is a robust serial communication standard widely used in industrial automation. MODAX supports Modbus RTU protocol over RS485 for communication with frequency converters (VFDs), PLCs, and other industrial devices.

#### Features
- **Modbus RTU Protocol**: Industry-standard protocol
- **Multi-Drop Networks**: Up to 32 devices on one bus
- **Long Distance**: Up to 1200 meters
- **Noise Immunity**: Differential signaling
- **Speed Range**: 1200-115200 baud (typically 9600 or 19200)

#### Supported Devices
- **Frequency Converters/VFDs**:
  - ABB ACS/ACH series
  - Siemens SINAMICS series
  - Schneider Altivar series
  - Danfoss VLT series
  - Delta VFD series
  
- **PLCs**: Via Modbus gateway
- **Custom Devices**: Any Modbus RTU compatible device

#### Configuration

```python
from rs485_driver import RS485Config, create_rs485_driver

# Configure RS485 port
config = RS485Config(
    port='/dev/ttyUSB0',     # Serial port
    baudrate=9600,           # Communication speed
    bytesize=8,              # Data bits
    parity='N',              # No parity
    stopbits=1,              # Stop bits
    timeout=1.0              # Response timeout
)

# Create driver for VFD at slave ID 1
vfd = create_rs485_driver(config, slave_id=1)

# Control operations
vfd.start_motor(forward=True)
vfd.set_frequency(50.0)  # 50 Hz
status = vfd.get_status()
```

#### Register Mapping

Standard VFD register addresses (consult your device manual):

| Register | Address | Description | R/W |
|----------|---------|-------------|-----|
| Status Word | 0x2000 | Device status | R |
| Output Frequency | 0x2002 | Actual frequency (Hz * 100) | R |
| Output Current | 0x2003 | Output current (A * 10) | R |
| Control Word | 0x3000 | Control commands | W |
| Frequency Setpoint | 0x3001 | Target frequency (Hz * 100) | W |
| Acceleration Time | 0x3002 | Ramp-up time (s * 10) | W |

### 2. MIDI Control

MIDI (Musical Instrument Digital Interface) provides low-latency audio feedback for CNC machine events. While unconventional, MIDI is ideal for operator notifications.

#### Features
- **Low Latency**: Sub-millisecond response
- **Standard Protocol**: Universal MIDI support
- **Rich Feedback**: Musical tones for different events
- **Easy Integration**: USB MIDI devices or virtual MIDI

#### Event Mapping

| Event | MIDI Note | Description |
|-------|-----------|-------------|
| Machine Start | C3 (48) | Low tone |
| Machine Stop | D3 (50) | Low tone |
| Tool Change | C4 (60) | Mid tone |
| Program Start | C5 (72) | Ascending chord |
| Program End | C5 (74) | Descending chord |
| Error | C6 (84) | Rapid beeps |
| Emergency Stop | F#6 (90) | Sustained alarm |

#### Usage

```python
from midi_controller import create_midi_controller

# Create MIDI controller
midi = create_midi_controller(
    port_name=None,  # Auto-detect
    channel=0,
    velocity=100
)

# Play event sounds
midi.machine_start()
midi.tool_change()
midi.program_end()
midi.error_alert()

# Get statistics
stats = midi.get_statistics()
```

### 3. Pendant Control Devices

Pendant devices provide manual control for CNC machines through handwheels (MPG) and buttons.

#### Features
- **USB HID Support**: Standard USB pendants
- **Manual Jog Control**: X, Y, Z axes
- **Feed Override**: Real-time speed adjustment
- **Spindle Override**: Speed control
- **Emergency Stop**: Hardware button
- **Wireless Support**: Bluetooth/WiFi pendants

#### Compatible Devices
- Generic USB MPG/handwheel pendants
- XHC WHB series wireless pendants
- MACH3/LinuxCNC compatible pendants
- Custom Arduino/ESP32 pendants

#### Usage

```python
from pendant_device import (
    create_pendant_device,
    PendantButton,
    PendantAxis,
    JogMode
)

# Create pendant device
pendant = create_pendant_device(
    vendor_id=0x1234,  # USB VID
    product_id=0x5678  # USB PID
)

# Register event handlers
def on_emergency_stop(event):
    print("EMERGENCY STOP!")
    # Trigger safety shutdown

pendant.register_button_handler(
    PendantButton.EMERGENCY_STOP,
    on_emergency_stop
)

def on_mpg_move(event):
    axis = event.data['axis']
    delta = event.data['delta']
    print(f"MPG: Axis {axis}, Delta {delta}")
    # Move machine

pendant.register_mpg_handler(on_mpg_move)

# Get current state
state = pendant.get_state()
print(f"Active axis: {state.axis}")
print(f"Feed override: {state.feed_override}%")
```

### 4. Slave Board I/O Expansion

Distributed I/O boards extend system capabilities with additional digital/analog I/O near sensors and actuators.

#### Features
- **I2C Protocol**: Standard 2-wire interface
- **Hot-Plugging**: Dynamic device discovery
- **Multiple Boards**: Up to 112 I2C addresses
- **Auto-Discovery**: Automatic enumeration
- **Mixed I/O**: Digital, analog, PWM, encoders

#### Compatible Boards
- Arduino slave boards (I2C)
- ESP32 slave nodes
- MCP23017 I2C I/O expanders (16 digital I/O)
- PCF8574 I2C I/O expanders (8 digital I/O)
- Custom slave boards

#### Usage

```python
from slave_board import (
    create_slave_board_manager,
    SlaveConfig,
    SlaveType
)

# Create slave board manager
slaves = create_slave_board_manager(
    bus=1,  # I2C bus number
    auto_discover=True
)

# Add slave board
config = SlaveConfig(
    slave_id=1,
    slave_type=SlaveType.MIXED_IO,
    address=0x20,  # I2C address
    description="Main I/O Board",
    num_digital_inputs=8,
    num_digital_outputs=8,
    num_analog_inputs=4
)
slaves.add_slave(config)

# Read digital input
door_closed = slaves.read_digital_input(
    slave_id=1,
    pin=0
)

# Write digital output
slaves.write_digital_output(
    slave_id=1,
    pin=7,
    value=True  # Turn on relay
)

# Read analog input
temperature = slaves.read_analog_input(
    slave_id=1,
    channel=0
)

# Write PWM output
slaves.write_pwm_output(
    slave_id=1,
    channel=0,
    duty_cycle=0.75  # 75% duty cycle
)

# Get all slaves
all_slaves = slaves.get_all_slaves()
```

### 5. Live Wire Communication (ESP32/Arduino)

Direct serial communication with ESP32/Arduino field devices for real-time sensor data.

#### Features
- **MQTT Protocol**: Publish/Subscribe messaging
- **Real-Time**: 10Hz sensor data, 20Hz safety
- **Reliable**: QoS levels, retained messages
- **Scalable**: Multiple field devices
- **TLS Support**: Encrypted communication

#### Topics

| Topic | Direction | Rate | Description |
|-------|-----------|------|-------------|
| `modax/sensor/data` | ESP32 → Control | 10 Hz | Sensor readings |
| `modax/sensor/safety` | ESP32 → Control | 20 Hz | Safety status |
| `modax/control/command` | Control → ESP32 | On-demand | Control commands |

#### ESP32 Configuration

```cpp
// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;

// Topics
const char* mqtt_topic_data = "modax/sensor/data";
const char* mqtt_topic_safety = "modax/sensor/safety";
const char* mqtt_topic_command = "modax/control/command";

// Device ID
const char* device_id = "ESP32_FIELD_001";
```

---

## Integration Patterns

### Pattern 1: VFD Control

```python
# Initialize VFD
config = RS485Config(port='/dev/ttyUSB0', baudrate=9600)
vfd = create_rs485_driver(config, slave_id=1)

# Start spindle
vfd.set_frequency(100.0)  # 100 Hz (60000 RPM @ 2-pole motor)
vfd.start_motor(forward=True)

# Monitor status
status = vfd.get_status()
if status['running'] and status['at_speed']:
    print("Spindle ready")
    
# Stop spindle
vfd.stop_motor()
```

### Pattern 2: Pendant-Controlled Jogging

```python
# Initialize pendant
pendant = create_pendant_device()

def on_mpg_move(event):
    axis = event.data['axis']
    delta = event.data['delta']
    
    # Calculate jog distance
    state = pendant.get_state()
    distance = delta * state.jog_step
    
    # Send jog command to CNC
    cnc.jog(axis=axis, distance=distance)

pendant.register_mpg_handler(on_mpg_move)
```

### Pattern 3: Distributed Safety System

```python
# Initialize slave boards
slaves = create_slave_board_manager(bus=1)

# Safety loop
while running:
    # Read door switches
    door1 = slaves.read_digital_input(1, pin=0)
    door2 = slaves.read_digital_input(1, pin=1)
    
    # Read emergency stop
    estop = slaves.read_digital_input(1, pin=2)
    
    # Check safety
    if not estop and door1 and door2:
        # Safe to run
        slaves.write_digital_output(1, pin=7, value=True)  # Enable relay
    else:
        # Safety fault
        slaves.write_digital_output(1, pin=7, value=False)  # Disable relay
        midi.error_alert()  # Alert operator
```

---

## Wiring Guidelines

### RS485 Wiring

```
Device 1       Device 2       Device N
   A ----------- A ----------- A
   B ----------- B ----------- B
  GND --------- GND --------- GND

Termination:    120Ω resistor between A-B at each end
Cable:          Twisted pair, shielded
Max Length:     1200m
```

### I2C Wiring

```
Master         Slave 1        Slave 2
  SDA ---------- SDA ---------- SDA
  SCL ---------- SCL ---------- SCL
  GND ---------- GND ---------- GND
  
Pull-up:        4.7kΩ on SDA and SCL to VCC
Max Length:     ~3m (use I2C extenders for longer)
```

---

## Troubleshooting

### RS485 Issues

**Problem**: No communication  
**Solution**: 
- Check wiring (A-A, B-B)
- Verify baud rate matches device
- Add termination resistors
- Check slave ID configuration

**Problem**: Intermittent errors  
**Solution**:
- Add shielding to cable
- Reduce baud rate
- Check ground connections
- Reduce cable length

### MIDI Issues

**Problem**: No MIDI output  
**Solution**:
- Install dependencies: `pip install mido python-rtmidi`
- Check MIDI device connection
- List available ports: `mido.get_output_names()`

### Pendant Issues

**Problem**: Pendant not detected  
**Solution**:
- Install HID support: `pip install hidapi`
- Check USB connection
- Verify permissions (Linux: add user to dialout group)
- Check VID/PID in device info

### I2C Issues

**Problem**: Slave not responding  
**Solution**:
- Check SDA/SCL connections
- Verify pull-up resistors (4.7kΩ)
- Scan bus: `i2cdetect -y 1`
- Check slave address conflicts

---

## Security Considerations

### RS485 Security
- Use isolated RS485 adapters
- Implement message authentication
- Monitor for unauthorized commands
- Use separate networks for safety-critical devices

### Network Segmentation
- Place industrial protocols on OT network
- Use firewall between IT and OT networks
- Implement VLANs for device isolation
- See [NETWORK_ARCHITECTURE.md](NETWORK_ARCHITECTURE.md)

---

## Performance

### Typical Latencies

| Protocol | Latency | Throughput |
|----------|---------|------------|
| RS485 (9600 baud) | 10-50ms | ~1 KB/s |
| RS485 (115200 baud) | 2-10ms | ~11 KB/s |
| MIDI | <1ms | ~3 KB/s |
| I2C (100 kHz) | 1-5ms | ~12 KB/s |
| I2C (400 kHz) | <1ms | ~50 KB/s |
| MQTT | 10-100ms | Variable |

---

## Best Practices

1. **Error Handling**: Always implement retry logic and timeouts
2. **Monitoring**: Log communication statistics and errors
3. **Redundancy**: Use multiple communication paths for critical systems
4. **Testing**: Test under realistic conditions with noise and load
5. **Documentation**: Document register mappings and device configurations
6. **Safety**: Keep safety systems independent of complex protocols
7. **Maintenance**: Regular cable inspection and connection testing

---

## Related Documentation

- [DEVICE_INTEGRATION.md](DEVICE_INTEGRATION.md) - General device integration
- [NETWORK_ARCHITECTURE.md](NETWORK_ARCHITECTURE.md) - Network design
- [SECURITY.md](SECURITY.md) - Security considerations
- [API.md](API.md) - Control layer API
- [CNC_FEATURES.md](CNC_FEATURES.md) - CNC functionality

---

## References

- **Modbus**: https://modbus.org/
- **RS485**: EIA-485 Standard
- **MIDI**: MIDI Specification 1.0
- **I2C**: Philips I2C Specification
- **USB HID**: USB HID Usage Tables

---

**Note**: All protocols support graceful degradation. If a protocol library is not installed, the system will use stub implementations and continue operating with reduced functionality.
