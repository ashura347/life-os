# LIFE OS — ESP32 Setup & Firmware Compilation Guide

This document provides step-by-step instructions for configuring Arduino IDE, installing required libraries, configuring Wi-Fi and server settings, and flashing `esp32/real_sensor_device.ino` to the ESP32 microcontroller.

---

## 🛠️ Step 1: Arduino IDE & ESP32 Core Setup

1. **Download Arduino IDE**: Install Arduino IDE v2.x or higher from [arduino.cc](https://www.arduino.cc/en/software).
2. **Add ESP32 Board Package**:
   - Go to **File -> Preferences**.
   - Paste the following URL into **Additional Boards Manager URLs**:
     ```text
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools -> Board -> Boards Manager**, search for `esp32` by Espressif Systems, and click **Install**.

---

## 📚 Step 2: Install Required Arduino Libraries

Go to **Tools -> Manage Libraries** (or press `Ctrl + Shift + I`) and install the following libraries:

1. **ArduinoJson** (by *Benoit Blanchon*) — Version 6.x or 7.x.
2. **SparkFun MAX3010x Pulse and Proximity Sensor Library** (by *SparkFun Electronics*).
3. **OneWire** (by *Paul Stoffregen*).
4. **DallasTemperature** (by *Miles Burton*).
5. **Adafruit MPU6050** (by *Adafruit*).
6. **Adafruit Unified Sensor** (by *Adafruit*).

---

## ⚙️ Step 3: Configure Wi-Fi & Server Parameters

Open `esp32/real_sensor_device.ino` in Arduino IDE and update the Wi-Fi and Server placeholders:

```cpp
// Replace placeholders with your actual Wi-Fi and computer IP address
const char* WIFI_SSID     = "YOUR_WIFI_NAME";        // e.g. "HomeNetwork"
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";    // e.g. "SecretPass123"
const char* SERVER_URL    = "http://192.168.1.100:5000"; // Replace 192.168.1.100 with your computer's local IP address
```

### Finding your local IP address:
- **Windows**: Open Command Prompt (`cmd`) and run `ipconfig`. Look for **IPv4 Address** (e.g. `192.168.1.100`).
- **Same Network Requirement**: Ensure the ESP32 and your computer are connected to the exact same Wi-Fi router.

---

## 🚀 Step 4: Flash Firmware to ESP32

1. Connect the ESP32 board to your computer via a micro-USB or USB-C cable.
2. Select Board: **Tools -> Board -> ESP32 Arduino -> DOIT ESP32 DEVKIT V1** (or matching your ESP32 model).
3. Select Port: **Tools -> Port -> COMx** (Windows) or `/dev/cu.usbserial-xxx` (macOS).
4. Click **Upload** (or press `Ctrl + U`).
5. Open Serial Monitor: **Tools -> Serial Monitor** and set baud rate to **`115200`**.

---

## 🔍 Troubleshooting Checklist

- **Wi-Fi Connection Fails**: Verify SSID and password spelling. Ensure router operates on 2.4GHz (ESP32 does not support 5GHz Wi-Fi).
- **MAX30102 Not Detected**: Verify SDA (GPIO 21) and SCL (GPIO 22) I2C connections.
- **DS18B20 Reads -127°C**: Confirm 4.7kΩ pull-up resistor is installed between Data (GPIO 4) and 3.3V.
- **HTTP POST Fails**: Verify Flask server is running (`python app.py`) and firewall permits incoming connections on port 5000.
