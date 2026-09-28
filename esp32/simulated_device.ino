/*
  =============================================================================
  LIFE OS — Patient Monitoring & Emergency Response System (Part 3)
  ESP32 Simulated Client Firmware (Arduino C++)
  =============================================================================
  
  Description:
    Simulates an ESP32 microcontroller sending real-time patient vitals and
    heartbeat pings over Wi-Fi to the LIFE OS Flask REST API backend.
    
  IMPORTANT NOTICE:
    All vital measurements generated in this file are STRICTLY SIMULATED TEST DATA.
    No physical sensors or emergency communication calls are executed in Part 3.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Ensure ArduinoJson library is installed in Arduino IDE
#include "sensor_config.h"

// =============================================================================
// Configurable Network & Server Parameters (Update for your local Wi-Fi setup)
// =============================================================================
const char* WIFI_SSID = "YOUR_WIFI_SSID";         // Replace with your Wi-Fi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"; // Replace with your Wi-Fi Password

// Flask Server API Base URL (Replace with your server local IP, e.g. http://192.168.1.100:5000)
const char* SERVER_BASE_URL = "http://127.0.0.1:5000"; 

const char* DEVICE_ID = "LIFEOS-001";
const char* PATIENT_ID = "P001";
const int TRANSMISSION_INTERVAL_MS = 5000; // Send telemetry every 5 seconds

// =============================================================================
// Helper Function Declarations
// =============================================================================
void connectToWiFi();
void sendHeartbeatPing();
void sendVitalTelemetry();

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n==============================================");
  Serial.println("   LIFE OS — ESP32 Simulated Device Initializing ");
  Serial.println("==============================================");
  Serial.println("NOTICE: All sensor values are SIMULATED TEST DATA.");

  connectToWiFi();
}

void loop() {
  // Ensure Wi-Fi remains connected
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (WiFi.status() == WL_CONNECTED) {
    // 1. Send Heartbeat Ping
    sendHeartbeatPing();
    
    // 2. Read simulated vitals and post to Flask API
    sendVitalTelemetry();
  } else {
    Serial.println("[ERROR] Wi-Fi connection lost. Skipping transmission tick.");
  }

  delay(TRANSMISSION_INTERVAL_MS);
}

// =============================================================================
// Wi-Fi Connection Handler
// =============================================================================
void connectToWiFi() {
  Serial.print("[Wi-Fi] Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[Wi-Fi] Connected successfully!");
    Serial.print("[Wi-Fi] Device IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[Wi-Fi WARNING] Connection failed. Will retry on next loop.");
  }
}

// =============================================================================
// 1. Send Device Heartbeat Ping (POST /api/device/heartbeat)
// =============================================================================
void sendHeartbeatPing() {
  HTTPClient http;
  String heartbeatEndpoint = String(SERVER_BASE_URL) + "/api/device/heartbeat";

  http.begin(heartbeatEndpoint);
  http.addHeader("Content-Type", "application/json");

  // Construct JSON Body
  StaticJsonDocument<128> doc;
  doc["device_id"] = DEVICE_ID;
  doc["patient_id"] = PATIENT_ID;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.print("[HTTP Heartbeat] Sending ping to ");
  Serial.println(heartbeatEndpoint);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    String responseStr = http.getString();
    Serial.print("[HTTP Heartbeat] Response Code: ");
    Serial.println(httpResponseCode);
    Serial.print("[HTTP Heartbeat] Response Body: ");
    Serial.println(responseStr);
  } else {
    Serial.print("[HTTP Error] Heartbeat failed. Error code: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}

// =============================================================================
// 2. Send Vital Telemetry Payload (POST /api/vitals)
// =============================================================================
void sendVitalTelemetry() {
  HTTPClient http;
  String vitalsEndpoint = String(SERVER_BASE_URL) + "/api/vitals";

  // Read simulated values from sensor_config.h placeholder functions
  int hr = readSimulatedHeartRate();
  int spo2 = readSimulatedSpO2();
  float temp = readSimulatedTemperature();
  String movement = readSimulatedMovement();

  http.begin(vitalsEndpoint);
  http.addHeader("Content-Type", "application/json");

  // Construct JSON Body
  StaticJsonDocument<256> doc;
  doc["patient_id"] = PATIENT_ID;
  doc["heart_rate"] = hr;
  doc["spo2"] = spo2;
  doc["temperature"] = temp;
  doc["movement_status"] = movement;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.println("----------------------------------------------");
  Serial.println("[HTTP Telemetry] Posting Vitals Payload:");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    String responseStr = http.getString();
    Serial.print("[HTTP Telemetry] Status Code: ");
    Serial.println(httpResponseCode);
    Serial.print("[HTTP Telemetry] Server Response: ");
    Serial.println(responseStr);
  } else {
    Serial.print("[HTTP Error] Vitals post failed. Error code: ");
    Serial.println(httpResponseCode);
  }

  Serial.println("----------------------------------------------");
  http.end();
}
