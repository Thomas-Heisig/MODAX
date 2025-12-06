# ESP32 Field Layer

## Overview
The Field Layer is responsible for real-time sensor data acquisition from industrial equipment. This layer runs on ESP32 microcontrollers and implements safety-critical monitoring functions that operate independently of AI systems.

## Features
- **Real-time sensor reading** (10Hz for general data, 20Hz for safety)
- **Motor current monitoring** using ACS712 sensors
- **Vibration analysis** using MPU6050 accelerometer
- **Temperature monitoring** with thermistor sensors
- **Safety-critical monitoring** (Emergency stop, door sensors, overload detection)
- **MQTT data transmission** to control layer
- **Local safety responses** (hardware-level, AI-free)

## Hardware Requirements
- ESP32 Development Board
- MPU6050 Accelerometer/Gyroscope module
- ACS712 Current sensors (2x)
- NTC Thermistor temperature sensors
- Emergency stop button
- Door safety sensor

## Pin Configuration
- GPIO 34: Current Sensor 1 (ADC)
- GPIO 35: Current Sensor 2 (ADC)
- GPIO 32: Temperature Sensor 1 (ADC)
- GPIO 25: Emergency Stop Input (with pullup)
- GPIO 26: Door Sensor Input (with pullup)
- GPIO 21/22: I2C (SDA/SCL) for MPU6050

## Configuration
Edit the following in `src/main.cpp`:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;
```

## Building and Uploading
Using PlatformIO:
```bash
cd esp32-field-layer
pio run --target upload
pio device monitor
```

## MQTT Topics
- `modax/sensor/data` - Sensor readings (currents, vibration, temperature)
- `modax/sensor/safety` - Safety-critical status updates

## Safety Design
The safety system operates at the hardware level and is completely independent of AI processing. Safety checks run at 20Hz and can trigger immediate hardware responses through safety relays.

### Safety Conditions Monitored:
1. Emergency stop button state
2. Safety door closed state
3. Motor overload detection (>10A)
4. Temperature limits (<85°C)

All safety logic is deterministic and uses simple threshold checks without any AI/ML processing.
