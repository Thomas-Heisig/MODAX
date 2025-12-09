# ESP32 Hardware-in-the-Loop (HIL) Tests

This directory contains automated Hardware-in-the-Loop tests for the MODAX ESP32 field layer.

## Overview

HIL tests validate the ESP32 firmware functionality through real MQTT communication, ensuring the field layer operates correctly under various conditions.

## Test Categories

### 1. Basic Communication Tests
- MQTT broker connection
- Sensor data message reception
- Safety status message reception
- Message structure validation

### 2. Sensor Data Flow Tests
- Publishing rate validation (~10Hz for sensors)
- Publishing rate validation (~20Hz for safety)
- Data format and type checking
- Timestamp monotonicity

### 3. Safety Monitoring Tests
- Normal safety state verification
- Safety message frequency validation
- Emergency response behavior

### 4. Robustness Tests
- Long-running stability (60 seconds)
- MQTT reconnection after disconnect
- Message burst handling
- Network fluctuation tolerance

### 5. Edge Cases
- Invalid command handling
- Multiple client subscriptions
- Message size validation

## Prerequisites

### Hardware Requirements
- ESP32 development board with firmware flashed
- USB connection to development machine
- WiFi network connectivity

### Software Requirements
- Python 3.8+
- MQTT broker (Mosquitto) running locally or on network
- pytest
- paho-mqtt

## Installation

```bash
# Install test dependencies
cd tests/hil
pip install -r requirements.txt

# Or install from root
pip install pytest paho-mqtt
```

## Configuration

### ESP32 Configuration
1. Update WiFi credentials in `esp32-field-layer/src/main.cpp`:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "192.168.1.100";  // Your MQTT broker IP
   ```

2. Flash firmware to ESP32:
   ```bash
   cd esp32-field-layer
   pio run --target upload
   pio device monitor  # Monitor serial output
   ```

### MQTT Broker Setup
Start Mosquitto broker:

```bash
# Linux/macOS
sudo systemctl start mosquitto

# Or use Docker
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto

# Windows (if installed as service)
net start mosquitto
```

Verify broker is running:
```bash
mosquitto_sub -h localhost -t '#' -v
```

## Running Tests

### Run All Tests
```bash
cd tests/hil
pytest test_esp32_hil.py -v
```

### Run Specific Test Suite
```bash
# Basic communication only
pytest test_esp32_hil.py::TestBasicCommunication -v

# Sensor data flow only
pytest test_esp32_hil.py::TestSensorDataFlow -v

# Safety monitoring only
pytest test_esp32_hil.py::TestSafetyMonitoring -v

# Robustness tests (includes long-running tests)
pytest test_esp32_hil.py::TestRobustness -v

# Edge cases only
pytest test_esp32_hil.py::TestEdgeCases -v
```

### Run Without Slow Tests
```bash
pytest test_esp32_hil.py -v -m "not slow"
```

### Run Only Slow Tests
```bash
pytest test_esp32_hil.py -v -m "slow"
```

### Run with Detailed Logging
```bash
pytest test_esp32_hil.py -v -s --log-cli-level=INFO
```

### Run with Coverage
```bash
pytest test_esp32_hil.py --cov=. --cov-report=html
```

## Test Markers

- `@pytest.mark.slow` - Tests that take longer than 10 seconds (e.g., 60-second stability test)

## Expected Test Output

### Successful Test Run
```
tests/hil/test_esp32_hil.py::TestBasicCommunication::test_mqtt_connection PASSED
tests/hil/test_esp32_hil.py::TestBasicCommunication::test_sensor_data_received PASSED
tests/hil/test_esp32_hil.py::TestBasicCommunication::test_safety_data_received PASSED
tests/hil/test_esp32_hil.py::TestSensorDataFlow::test_sensor_publishing_rate PASSED
tests/hil/test_esp32_hil.py::TestSensorDataFlow::test_safety_publishing_rate PASSED
tests/hil/test_esp32_hil.py::TestSensorDataFlow::test_sensor_data_format PASSED
tests/hil/test_esp32_hil.py::TestSensorDataFlow::test_message_timestamps PASSED
tests/hil/test_esp32_hil.py::TestSafetyMonitoring::test_normal_safety_state PASSED
tests/hil/test_esp32_hil.py::TestSafetyMonitoring::test_safety_message_frequency PASSED
tests/hil/test_esp32_hil.py::TestRobustness::test_reconnection_after_disconnect PASSED
tests/hil/test_esp32_hil.py::TestEdgeCases::test_invalid_command_handling PASSED
tests/hil/test_esp32_hil.py::TestEdgeCases::test_multiple_clients_subscription PASSED
tests/hil/test_esp32_hil.py::TestEdgeCases::test_message_size_reasonable PASSED

======================== 13 passed in 25.3s ========================
```

## Troubleshooting

### Issue: "Failed to connect to MQTT broker"
**Solution:** 
- Verify mosquitto is running: `systemctl status mosquitto`
- Check firewall settings allow port 1883
- Verify broker address in test configuration

### Issue: "No sensor messages captured"
**Solution:**
- Check ESP32 is powered and running (check serial monitor)
- Verify ESP32 WiFi connection (LED indicators, serial output)
- Confirm MQTT broker IP in ESP32 firmware matches test configuration
- Check MQTT topics match between firmware and tests

### Issue: "Expected X messages, got Y"
**Solution:**
- ESP32 may be experiencing network latency
- Tests use tolerance ranges - small deviations are acceptable
- Check WiFi signal strength
- Verify MQTT broker is not overloaded

### Issue: Long-running tests timeout
**Solution:**
- Ensure stable WiFi connection during test
- Check ESP32 power supply is stable
- Increase timeout values if needed for your environment

## Test Jig Schematic (Future Enhancement)

For more controlled testing, a test jig can simulate sensor inputs:

### Components Needed
- ESP32 development board
- PWM generator for motor speed simulation
- Voltage dividers for current sensor simulation
- MPU6050 vibration sensor (or simulator)
- Temperature sensor (or voltage source)
- Push buttons for safety inputs (E-Stop, door sensor)

### Connections
```
PWM Generator → GPIO for motor control
Voltage Source → CURRENT_SENSOR_PIN_1 (GPIO 34)
Voltage Source → CURRENT_SENSOR_PIN_2 (GPIO 35)
Voltage Source → TEMP_SENSOR_PIN_1 (GPIO 32)
Push Button → EMERGENCY_STOP_PIN (GPIO 25)
Push Button → DOOR_SENSOR_PIN (GPIO 26)
MPU6050 → I2C (SDA/SCL)
```

### Simulation Script
Future versions will include `simulate_sensors.py` to programmatically control the test jig via GPIO expander or Arduino.

## Continuous Integration

These tests can be integrated into CI/CD pipeline with a dedicated test rig:

```yaml
# .github/workflows/esp32-hil.yml
name: ESP32 HIL Tests

on: [push, pull_request]

jobs:
  esp32-hil:
    runs-on: self-hosted  # Requires runner with ESP32 hardware
    steps:
      - uses: actions/checkout@v2
      - name: Start MQTT Broker
        run: docker run -d -p 1883:1883 eclipse-mosquitto
      - name: Flash ESP32
        run: |
          cd esp32-field-layer
          pio run --target upload
      - name: Run HIL Tests
        run: |
          cd tests/hil
          pytest test_esp32_hil.py -v
```

## Performance Benchmarks

Expected performance metrics:
- Sensor data rate: 8-12 Hz (target: 10 Hz)
- Safety data rate: 16-24 Hz (target: 20 Hz)
- Message latency: < 100ms
- Reconnection time: < 10s
- Message loss rate: < 1%

## Future Enhancements

1. **Automated Sensor Simulation**
   - GPIO control for test jig
   - Programmatic sensor value injection
   - Automated safety state transitions

2. **Power Loss Simulation**
   - Controlled power cycling
   - Recovery time measurement
   - Data integrity verification

3. **Network Fluctuation Tests**
   - Simulated packet loss
   - Variable latency injection
   - Bandwidth throttling

4. **Stress Testing**
   - Maximum message rate testing
   - Memory leak detection
   - CPU usage monitoring

5. **Multi-Device Testing**
   - Multiple ESP32 devices simultaneously
   - Device discovery and coordination
   - Collision detection and avoidance

## References

- [MODAX Architecture Documentation](../../docs/ARCHITECTURE.md)
- [ESP32 Field Layer README](../../esp32-field-layer/README.md)
- [MQTT Protocol Specification](https://mqtt.org/mqtt-specification/)
- [pytest Documentation](https://docs.pytest.org/)
- [paho-mqtt Documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)

## Support

For issues or questions about HIL tests:
1. Check the troubleshooting section above
2. Review ESP32 serial output for errors
3. Verify MQTT broker logs
4. Open an issue on GitHub with test logs and hardware details
