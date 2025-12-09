# MODAX Troubleshooting Guide

**Last Updated:** 2025-12-09  
**Version:** 0.3.0

This comprehensive guide helps diagnose and resolve common issues in the MODAX system.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Connection Issues](#connection-issues)
- [MQTT Problems](#mqtt-problems)
- [API Issues](#api-issues)
- [HMI Problems](#hmi-problems)
- [ESP32 Field Layer Issues](#esp32-field-layer-issues)
- [Performance Issues](#performance-issues)
- [Data Issues](#data-issues)
- [Security Issues](#security-issues)
- [Docker/Deployment Issues](#dockerdeployment-issues)
- [Getting Help](#getting-help)

## Quick Diagnostics

### System Health Check

Run these commands to check system status:

```bash
# Check if services are running
docker ps  # If using Docker

# Check Python services
curl http://localhost:8000/health  # Control Layer
curl http://localhost:8001/health  # AI Layer

# Check MQTT broker
mosquitto_sub -h localhost -t '#' -v  # Listen to all topics

# Check logs
tail -f python-control-layer/logs/*.log
tail -f python-ai-layer/logs/*.log
```

### Common Error Patterns

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `Connection refused` | Service not running | Start the service |
| `Timeout` | Network issue or slow response | Check network, increase timeout |
| `401 Unauthorized` | Missing/invalid credentials | Check API keys |
| `500 Internal Server Error` | Backend crash | Check service logs |
| `MQTT connection failed` | Broker not running | Start MQTT broker |

## Connection Issues

### HMI Cannot Connect to Control Layer

**Symptoms:**
- HMI shows "Connection Error"
- Status shows "Disconnected" in red
- No data displayed

**Diagnosis:**
```bash
# Test if Control Layer is accessible
curl http://localhost:8000/health

# Check if service is running
ps aux | grep "python.*main.py"

# Check firewall
sudo ufw status  # Linux
netsh advfirewall show allprofiles  # Windows
```

**Solutions:**

1. **Service Not Running:**
   ```bash
   cd python-control-layer
   python main.py
   ```

2. **Wrong URL/Port:**
   - Check HMI configuration: `CONTROL_LAYER_URL`
   - Default: `http://localhost:8000`
   - Ensure port 8000 is not in use: `lsof -i :8000`

3. **Firewall Blocking:**
   ```bash
   # Allow port 8000
   sudo ufw allow 8000/tcp
   ```

4. **Network Issue:**
   ```bash
   # Test connectivity
   ping localhost
   telnet localhost 8000
   ```

### Control Layer Cannot Reach AI Layer

**Symptoms:**
- Control Layer logs show "AI Layer timeout"
- Analysis features not working

**Diagnosis:**
```bash
# Check AI Layer status
curl http://localhost:8001/health

# Check environment variable
echo $AI_LAYER_URL
echo $AI_LAYER_TIMEOUT
```

**Solutions:**

1. **Start AI Layer:**
   ```bash
   cd python-ai-layer
   python main.py
   ```

2. **Configure Timeout:**
   ```bash
   export AI_LAYER_TIMEOUT=10  # Increase to 10 seconds
   ```

3. **Check URL Configuration:**
   ```bash
   # In python-control-layer/config/.env
   AI_LAYER_URL=http://localhost:8001/analyze
   ```

## MQTT Problems

### MQTT Broker Not Accessible

**Symptoms:**
- "MQTT connection failed" in logs
- No sensor data received
- ESP32 cannot publish data

**Diagnosis:**
```bash
# Check if broker is running
ps aux | grep mosquitto

# Test connection
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test

# Check broker logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

**Solutions:**

1. **Start Broker:**
   ```bash
   # Linux
   sudo systemctl start mosquitto
   
   # Docker
   docker run -d -p 1883:1883 eclipse-mosquitto
   ```

2. **Check Configuration:**
   ```bash
   # Edit /etc/mosquitto/mosquitto.conf
   listener 1883
   allow_anonymous true  # For development only!
   ```

3. **Firewall:**
   ```bash
   sudo ufw allow 1883/tcp
   ```

### MQTT Authentication Fails

**Symptoms:**
- "Connection refused: not authorized" in logs
- ESP32/Python clients cannot connect

**Solutions:**

1. **Check Credentials:**
   ```bash
   # In config
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   ```

2. **Update Broker Password File:**
   ```bash
   sudo mosquitto_passwd -c /etc/mosquitto/passwd username
   # Enter password when prompted
   
   # Restart broker
   sudo systemctl restart mosquitto
   ```

3. **Verify ACL Rules:**
   ```bash
   # Check /etc/mosquitto/acl
   user device1
   topic read modax/devices/device1/#
   topic write modax/devices/device1/#
   ```

### MQTT Connection Keeps Dropping

**Symptoms:**
- Frequent reconnections in logs
- Intermittent data loss
- "Connection lost, reconnecting..." messages

**Diagnosis:**
```bash
# Check network stability
ping -c 100 mqtt_broker_ip

# Monitor MQTT traffic
mosquitto_sub -h localhost -t '#' -v

# Check system resources
top  # Look for memory/CPU issues
```

**Solutions:**

1. **Adjust Keepalive:**
   ```python
   # In mqtt_handler.py
   client.connect(host, port, keepalive=60)  # Increase keepalive
   ```

2. **Increase Reconnect Delay:**
   ```bash
   MQTT_RECONNECT_DELAY_MAX=120  # Max 2 minutes
   ```

3. **Check Network Quality:**
   - Use wired connection if possible
   - Check for WiFi interference
   - Verify router settings

## API Issues

### API Returns 500 Internal Server Error

**Symptoms:**
- API calls fail with 500 status
- "Internal Server Error" in HMI

**Diagnosis:**
```bash
# Check detailed logs
tail -f python-control-layer/logs/control_layer.log

# Test API directly
curl -v http://localhost:8000/api/v1/devices

# Check for Python errors
python -c "import fastapi; print(fastapi.__version__)"
```

**Solutions:**

1. **Check Dependencies:**
   ```bash
   cd python-control-layer
   pip install -r requirements.txt --upgrade
   ```

2. **Validate Input:**
   ```bash
   # Test with valid data
   curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"device_id": "device1"}'
   ```

3. **Review Error Logs:**
   - Check exception stack traces
   - Look for missing configuration
   - Verify database connections

### API Timeouts

**Symptoms:**
- Requests time out after several seconds
- "Request timeout" errors
- Slow API responses

**Diagnosis:**
```bash
# Measure response time
time curl http://localhost:8000/api/v1/devices

# Check system load
top
htop

# Monitor API performance
curl http://localhost:8000/metrics  # If Prometheus enabled
```

**Solutions:**

1. **Increase Timeout:**
   ```bash
   # In HMI or client config
   REQUEST_TIMEOUT=30  # 30 seconds
   ```

2. **Optimize Queries:**
   - Reduce data aggregation window
   - Add database indexes
   - Use caching

3. **Scale Resources:**
   - Increase memory allocation
   - Add more CPU cores
   - Use async operations

### API Authentication Fails

**Symptoms:**
- 401 Unauthorized responses
- "Invalid API key" errors

**Solutions:**

1. **Generate API Key:**
   ```bash
   # Generate new key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Configure API Key:**
   ```bash
   # In config
   API_KEY=your_generated_key
   
   # In requests
   curl -H "X-API-Key: your_generated_key" \
     http://localhost:8000/api/v1/devices
   ```

3. **Check Key Expiration:**
   - Verify key is not expired
   - Regenerate if needed

## HMI Problems

### HMI Shows "No Data Available"

**Symptoms:**
- Empty device list
- "No data available" message
- All fields show N/A

**Diagnosis:**
```bash
# Check if Control Layer is running
curl http://localhost:8000/api/v1/devices

# Check if devices are publishing data
mosquitto_sub -h localhost -t 'modax/devices/#' -v

# Check HMI logs
# Look in Event Viewer (Windows) or HMI log files
```

**Solutions:**

1. **Start ESP32 Devices:**
   - Power on ESP32 devices
   - Check serial monitor for connection status
   - Verify MQTT broker address in ESP32 config

2. **Wait for Data:**
   - System needs ~10 seconds for first data aggregation
   - Click "Refresh" button manually

3. **Check Control Layer:**
   ```bash
   # Verify devices are registered
   curl http://localhost:8000/api/v1/devices
   ```

### HMI Crashes or Freezes

**Symptoms:**
- HMI becomes unresponsive
- Application crashes
- High CPU/memory usage

**Diagnosis:**
```bash
# Check system resources
# Windows: Task Manager
# Linux: top or htop

# Check for exceptions in logs
# Windows Event Viewer
```

**Solutions:**

1. **Update .NET Runtime:**
   ```bash
   # Download latest .NET 8.0
   # https://dotnet.microsoft.com/download
   ```

2. **Reduce Update Frequency:**
   - Increase timer interval from 2s to 5s
   - In HMI settings or config

3. **Clear Cache:**
   - Delete temporary files
   - Restart application

4. **Check Memory Leaks:**
   - Monitor memory usage over time
   - Report if consistently increasing

### HMI Charts Not Updating

**Symptoms:**
- Static charts
- Old data displayed
- Real-time updates not working

**Solutions:**

1. **Enable WebSocket (if implemented):**
   ```bash
   WEBSOCKET_ENABLED=true
   WEBSOCKET_URL=ws://localhost:8000/ws
   ```

2. **Check Polling Interval:**
   - Ensure timer is enabled
   - Verify network connectivity

3. **Clear Chart Cache:**
   - Restart HMI
   - Force refresh (Ctrl+R)

## ESP32 Field Layer Issues

### ESP32 Won't Connect to WiFi

**Symptoms:**
- "WiFi connection failed" in serial monitor
- Device repeatedly restarting
- Cannot reach MQTT broker

**Diagnosis:**
```cpp
// Add debug output in main.cpp
Serial.println("WiFi SSID: " + String(WIFI_SSID));
Serial.println("WiFi Status: " + String(WiFi.status()));
```

**Solutions:**

1. **Check Credentials:**
   ```cpp
   // In config.h or main.cpp
   #define WIFI_SSID "your_network_name"
   #define WIFI_PASSWORD "your_password"
   ```

2. **Check WiFi Range:**
   - Move ESP32 closer to router
   - Use WiFi extender
   - Check for interference

3. **Reset ESP32:**
   - Hold BOOT button
   - Press EN/RST button
   - Release both

4. **Check WiFi Band:**
   - ESP32 only supports 2.4GHz
   - Ensure router broadcasts 2.4GHz

### ESP32 Sensor Readings Incorrect

**Symptoms:**
- Unrealistic sensor values
- Constant zero readings
- Erratic fluctuations

**Diagnosis:**
```cpp
// Add debug output
Serial.print("Raw ADC: ");
Serial.println(analogRead(CURRENT_SENSOR_PIN));
Serial.print("Temperature: ");
Serial.println(temperatureSensor.readCelsius());
```

**Solutions:**

1. **Check Wiring:**
   - Verify connections
   - Check for loose wires
   - Test with multimeter

2. **Calibrate Sensors:**
   ```cpp
   // In sensor initialization
   currentSensor.calibrate();  // Zero offset
   temperatureSensor.setOffset(-2.5);  // Adjust offset
   ```

3. **Check Power Supply:**
   - Ensure stable 5V supply
   - Check for voltage drops
   - Use capacitors for noise filtering

4. **Verify Sensor Specs:**
   - Check datasheet for correct pins
   - Verify I2C addresses
   - Ensure correct voltage levels

### ESP32 High Memory Usage

**Symptoms:**
- Frequent reboots
- Watchdog timer resets
- "Out of memory" errors

**Diagnosis:**
```cpp
// In loop()
Serial.print("Free heap: ");
Serial.println(ESP.getFreeHeap());
```

**Solutions:**

1. **Reduce Buffer Sizes:**
   ```cpp
   #define BUFFER_SIZE 512  // Reduce from 1024
   #define MAX_READINGS 50  // Reduce from 100
   ```

2. **Use PROGMEM:**
   ```cpp
   const char msg[] PROGMEM = "Long string constant";
   ```

3. **Clear Buffers:**
   ```cpp
   // Periodically clear accumulated data
   if (millis() - lastClear > 60000) {
     readings.clear();
     lastClear = millis();
   }
   ```

## Performance Issues

### High CPU Usage

**Symptoms:**
- System sluggish
- API slow to respond
- High temperature

**Diagnosis:**
```bash
# Check CPU usage
top -o %CPU

# Profile Python application
python -m cProfile main.py

# Check for CPU-intensive operations
strace -c -p <pid>
```

**Solutions:**

1. **Optimize Data Processing:**
   ```python
   # Use numpy vectorized operations
   import numpy as np
   result = np.mean(sensor_data)  # Instead of loop
   ```

2. **Reduce Aggregation Window:**
   ```bash
   AGGREGATION_WINDOW=5  # Reduce from 10 seconds
   ```

3. **Use Async Operations:**
   ```python
   async def process_data():
       await asyncio.gather(*tasks)
   ```

### High Memory Usage

**Symptoms:**
- System running out of RAM
- Swap usage increasing
- OOM killer activating

**Diagnosis:**
```bash
# Check memory
free -h
top -o %MEM

# Python memory profiling
pip install memory_profiler
python -m memory_profiler main.py
```

**Solutions:**

1. **Limit Data Buffer:**
   ```python
   # Use ring buffer with max size
   from collections import deque
   buffer = deque(maxlen=1000)
   ```

2. **Clear Old Data:**
   ```python
   # Periodically clean up
   if len(historical_data) > MAX_HISTORY:
       historical_data = historical_data[-MAX_HISTORY:]
   ```

3. **Use Generators:**
   ```python
   def process_large_dataset():
       for item in dataset:
           yield process(item)  # Instead of list
   ```

### Slow Database Queries

**Symptoms:**
- API endpoints slow
- Timeout errors
- High database CPU

**Solutions:**

1. **Add Indexes:**
   ```sql
   CREATE INDEX idx_device_time ON sensor_data(device_id, timestamp);
   ```

2. **Optimize Queries:**
   ```sql
   -- Use time ranges
   SELECT * FROM sensor_data 
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   LIMIT 1000;
   ```

3. **Use Connection Pooling:**
   ```python
   # Configure pool size
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=40
   )
   ```

## Data Issues

### Missing Sensor Data

**Symptoms:**
- Gaps in time series
- Devices show offline
- Incomplete historical data

**Diagnosis:**
```bash
# Check recent data
curl http://localhost:8000/api/v1/devices/<device_id>/recent

# Check MQTT messages
mosquitto_sub -h localhost -t 'modax/devices/+/sensors' -v

# Check for errors in logs
grep ERROR python-control-layer/logs/*.log
```

**Solutions:**

1. **Check Network:**
   - Verify ESP32 WiFi connection
   - Check MQTT broker connectivity
   - Test network stability

2. **Verify MQTT Topics:**
   ```bash
   # Expected format
   modax/devices/<device_id>/sensors
   ```

3. **Check Buffer Overflow:**
   - Reduce sensor sampling rate
   - Increase buffer sizes
   - Process data faster

### Incorrect Analysis Results

**Symptoms:**
- False anomaly alerts
- Incorrect wear predictions
- Bad optimization recommendations

**Diagnosis:**
```bash
# Test AI layer directly
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device1","temperature":25.0,"current":1.5}'

# Check thresholds
grep THRESHOLD python-ai-layer/*.py
```

**Solutions:**

1. **Adjust Thresholds:**
   ```python
   # In anomaly_detector.py
   TEMP_THRESHOLD = 75.0  # Adjust based on your system
   CURRENT_THRESHOLD = 3.0
   ```

2. **Calibrate Baselines:**
   - Let system run for calibration period
   - Use normal operation data
   - Update baseline values

3. **Verify Sensor Accuracy:**
   - Cross-check with known values
   - Calibrate sensors
   - Replace faulty sensors

## Security Issues

### Unauthorized Access

**Symptoms:**
- Unknown devices connecting
- Unexpected API calls
- Security audit alerts

**Immediate Actions:**

1. **Enable Authentication:**
   ```bash
   # MQTT
   MQTT_USERNAME=secure_user
   MQTT_PASSWORD=<strong_password>
   
   # API
   API_KEY_REQUIRED=true
   API_KEY=<generate_secure_key>
   ```

2. **Enable TLS:**
   ```bash
   # MQTT
   MQTT_USE_TLS=true
   MQTT_CA_CERT=/path/to/ca.crt
   
   # API
   API_USE_HTTPS=true
   ```

3. **Review Access Logs:**
   ```bash
   tail -f python-control-layer/logs/security_audit.log
   ```

4. **Change All Credentials:**
   - Generate new API keys
   - Update MQTT passwords
   - Rotate TLS certificates

### TLS/SSL Connection Fails

**Symptoms:**
- "Certificate verification failed"
- "SSL handshake error"
- Clients cannot connect

**Solutions:**

1. **Check Certificate Validity:**
   ```bash
   openssl x509 -in cert.pem -text -noout
   # Check expiration date
   ```

2. **Verify Certificate Chain:**
   ```bash
   openssl verify -CAfile ca.crt server.crt
   ```

3. **Update CA Bundle:**
   ```bash
   # Linux
   sudo update-ca-certificates
   
   # Use custom CA
   MQTT_CA_CERT=/path/to/custom-ca.crt
   ```

## Docker/Deployment Issues

### Container Won't Start

**Symptoms:**
- `docker ps` shows container exited
- Container restarts repeatedly
- Error in `docker logs`

**Diagnosis:**
```bash
# Check container logs
docker logs <container_name>

# Inspect container
docker inspect <container_name>

# Check resource limits
docker stats
```

**Solutions:**

1. **Check Environment Variables:**
   ```bash
   docker run -e MQTT_HOST=mqtt_broker ...
   ```

2. **Verify Port Availability:**
   ```bash
   # Check if port is in use
   lsof -i :8000
   
   # Use different port
   docker run -p 8001:8000 ...
   ```

3. **Check Volume Mounts:**
   ```bash
   # Verify paths exist
   docker run -v /host/path:/container/path ...
   ```

### Docker Network Issues

**Symptoms:**
- Containers cannot communicate
- DNS resolution fails
- Connection refused between services

**Solutions:**

1. **Use Docker Network:**
   ```bash
   docker network create modax-network
   docker run --network modax-network ...
   ```

2. **Use Service Names:**
   ```bash
   # In docker-compose.yml
   services:
     control-layer:
       ...
     ai-layer:
       ...
   # Reference as http://ai-layer:8001
   ```

3. **Check Network Configuration:**
   ```bash
   docker network inspect modax-network
   ```

## Getting Help

### Before Asking for Help

1. **Check Documentation:**
   - `docs/INDEX.md` - Full documentation index
   - `docs/FAQ.md` - Frequently asked questions
   - `README.md` - Quick start guide

2. **Search Issues:**
   - GitHub Issues: existing solutions
   - ISSUES.md: known problems

3. **Collect Information:**
   - Version: `git describe --tags`
   - Logs: relevant error messages
   - Configuration: anonymized config files
   - Steps to reproduce

### Where to Get Help

1. **GitHub Issues:**
   - Bug reports: Technical issues
   - Feature requests: New functionality
   - Questions: General inquiries

2. **Documentation:**
   - Architecture: `docs/ARCHITECTURE.md`
   - API: `docs/API.md`
   - Configuration: `docs/CONFIGURATION.md`

3. **Community:**
   - Discussions tab on GitHub
   - Contributing: `CONTRIBUTING.md`

### Reporting Bugs

Include:
- MODAX version
- Operating system
- Full error message
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (sanitized)
- Screenshots if applicable

### Emergency Support

For critical production issues:
1. Check `docs/HIGH_AVAILABILITY.md`
2. Review `docs/BACKUP_RECOVERY.md`
3. Enable emergency logging
4. Collect system state
5. Contact maintainers

---

**Note:** This guide is continuously updated. If you encounter an issue not covered here, please contribute by documenting your solution!

Last Updated: 2025-12-09
