#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// WiFi credentials - should be configured per deployment
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker settings
const char* mqtt_server = "192.168.1.100";  // Configure to your broker
const int mqtt_port = 1883;
const char* mqtt_topic_data = "modax/sensor/data";
const char* mqtt_topic_safety = "modax/sensor/safety";

// Device identification
const char* device_id = "ESP32_FIELD_001";

// Hardware pins
const int CURRENT_SENSOR_PIN_1 = 34;  // ADC1_CH6
const int CURRENT_SENSOR_PIN_2 = 35;  // ADC1_CH7
const int TEMP_SENSOR_PIN_1 = 32;     // ADC1_CH4
const int EMERGENCY_STOP_PIN = 25;
const int DOOR_SENSOR_PIN = 26;

// Sampling intervals
const unsigned long SENSOR_INTERVAL = 100;   // 100ms = 10Hz
const unsigned long SAFETY_INTERVAL = 50;    // 50ms = 20Hz (faster for safety)

// Objects
WiFiClient espClient;
PubSubClient mqttClient(espClient);
Adafruit_MPU6050 mpu;

// Timing
unsigned long lastSensorTime = 0;
unsigned long lastSafetyTime = 0;

// Safety state
struct SafetyState {
  bool emergencyStop;
  bool doorClosed;
  bool overloadDetected;
  bool temperatureOk;
};

SafetyState safetyState = {false, true, false, true};

// Function declarations
void setupWiFi();
void setupMQTT();
void reconnectMQTT();
void readSensors();
void checkSafety();
void publishSensorData(float current1, float current2, float temp1, 
                      float vibX, float vibY, float vibZ);
void publishSafetyData();
float readCurrent(int pin);
float readTemperature(int pin);

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== MODAX Field Layer ESP32 ===");
  
  // Initialize I2C for MPU6050
  Wire.begin();
  
  // Initialize MPU6050 vibration sensor
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    // Continue anyway for demo purposes
  } else {
    Serial.println("MPU6050 initialized");
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }
  
  // Configure pins
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  pinMode(DOOR_SENSOR_PIN, INPUT_PULLUP);
  pinMode(CURRENT_SENSOR_PIN_1, INPUT);
  pinMode(CURRENT_SENSOR_PIN_2, INPUT);
  pinMode(TEMP_SENSOR_PIN_1, INPUT);
  
  // Setup WiFi and MQTT
  setupWiFi();
  setupMQTT();
  
  Serial.println("Setup complete");
}

void loop() {
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  unsigned long currentTime = millis();
  
  // Check safety systems at high frequency (AI-FREE ZONE)
  if (currentTime - lastSafetyTime >= SAFETY_INTERVAL) {
    lastSafetyTime = currentTime;
    checkSafety();
  }
  
  // Read and publish sensor data
  if (currentTime - lastSensorTime >= SENSOR_INTERVAL) {
    lastSensorTime = currentTime;
    readSensors();
  }
}

void setupWiFi() {
  delay(10);
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setupMQTT() {
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setBufferSize(512);  // Increase buffer for protobuf messages
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (mqttClient.connect(device_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void readSensors() {
  // Read current sensors
  float current1 = readCurrent(CURRENT_SENSOR_PIN_1);
  float current2 = readCurrent(CURRENT_SENSOR_PIN_2);
  
  // Read temperature
  float temp1 = readTemperature(TEMP_SENSOR_PIN_1);
  
  // Read vibration data
  sensors_event_t accel, gyro, temp;
  float vibX = 0, vibY = 0, vibZ = 0;
  
  if (mpu.getEvent(&accel, &gyro, &temp)) {
    vibX = accel.acceleration.x;
    vibY = accel.acceleration.y;
    vibZ = accel.acceleration.z;
  }
  
  // Publish sensor data
  publishSensorData(current1, current2, temp1, vibX, vibY, vibZ);
}

void checkSafety() {
  // SAFETY-CRITICAL SECTION - NO AI PROCESSING
  // These checks must be deterministic and fast
  
  bool prevEmergencyStop = safetyState.emergencyStop;
  
  // Read safety inputs (inverted due to pullup)
  safetyState.emergencyStop = !digitalRead(EMERGENCY_STOP_PIN);
  safetyState.doorClosed = !digitalRead(DOOR_SENSOR_PIN);
  
  // Check for motor overload based on current
  float current1 = readCurrent(CURRENT_SENSOR_PIN_1);
  float current2 = readCurrent(CURRENT_SENSOR_PIN_2);
  safetyState.overloadDetected = (current1 > 10.0) || (current2 > 10.0);  // 10A threshold
  
  // Check temperature safety
  float temp1 = readTemperature(TEMP_SENSOR_PIN_1);
  safetyState.temperatureOk = (temp1 < 85.0);  // 85°C threshold
  
  // Publish safety data if state changed or periodically
  static unsigned long lastSafetyPublish = 0;
  if (prevEmergencyStop != safetyState.emergencyStop || 
      millis() - lastSafetyPublish > 1000) {
    publishSafetyData();
    lastSafetyPublish = millis();
  }
  
  // Local safety action - immediate response
  if (safetyState.emergencyStop || !safetyState.doorClosed || 
      safetyState.overloadDetected || !safetyState.temperatureOk) {
    // Would trigger hardware safety relay here
    Serial.println("SAFETY TRIGGERED!");
  }
}

void publishSensorData(float current1, float current2, float temp1,
                       float vibX, float vibY, float vibZ) {
  // In a full implementation, this would use nanopb to encode protobuf
  // For now, using JSON for simplicity
  
  char payload[512];
  float vibMagnitude = sqrt(vibX*vibX + vibY*vibY + vibZ*vibZ);
  
  snprintf(payload, sizeof(payload),
    "{\"timestamp\":%lu,\"device_id\":\"%s\",\"motor_currents\":[%.2f,%.2f],"
    "\"vibration\":{\"x\":%.2f,\"y\":%.2f,\"z\":%.2f,\"magnitude\":%.2f},"
    "\"temperatures\":[%.2f]}",
    millis(), device_id, current1, current2, vibX, vibY, vibZ, vibMagnitude, temp1
  );
  
  mqttClient.publish(mqtt_topic_data, payload);
  
  Serial.print("Published sensor data: ");
  Serial.println(payload);
}

void publishSafetyData() {
  // Safety data always uses separate high-priority topic
  char payload[256];
  
  snprintf(payload, sizeof(payload),
    "{\"timestamp\":%lu,\"device_id\":\"%s\",\"emergency_stop\":%s,"
    "\"door_closed\":%s,\"overload_detected\":%s,\"temperature_ok\":%s}",
    millis(), device_id,
    safetyState.emergencyStop ? "true" : "false",
    safetyState.doorClosed ? "true" : "false",
    safetyState.overloadDetected ? "true" : "false",
    safetyState.temperatureOk ? "true" : "false"
  );
  
  mqttClient.publish(mqtt_topic_safety, payload);
  
  Serial.print("Published safety data: ");
  Serial.println(payload);
}

float readCurrent(int pin) {
  // ACS712 current sensor: 0A = 2.5V, sensitivity = 100mV/A
  int rawValue = analogRead(pin);
  float voltage = rawValue * (3.3 / 4095.0);  // ESP32 ADC is 12-bit
  float current = (voltage - 1.65) / 0.1;     // Convert to amperes
  return abs(current);
}

float readTemperature(int pin) {
  // Simple thermistor reading
  int rawValue = analogRead(pin);
  float voltage = rawValue * (3.3 / 4095.0);
  // Simplified Steinhart-Hart equation for demo
  float resistance = 10000.0 * voltage / (3.3 - voltage);
  float tempC = 25.0 + (resistance - 10000.0) / 100.0;  // Simplified
  return tempC;
}
