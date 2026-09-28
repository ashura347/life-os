# LIFE OS — ESP32 Hardware Wiring Schematic Guide

This document details the hardware pinout and electrical connection matrix for connecting MAX30102, DS18B20, and MPU6050 sensors to an ESP32 Development Board.

---

## 🔌 Hardware Pinout & Wiring Table

| Component | Pin Label | ESP32 GPIO Pin | Wire Color Code | Notes / Requirements |
|---|---|---|---|---|
| **ESP32 Board** | `3V3` | Output Power | Red | 3.3V power supply rail |
| **ESP32 Board** | `GND` | Ground | Black | Common Ground rail |
| **MAX30102 (Pulse Oximeter)** | `VIN` / `VCC` | `3V3` | Red | 3.3V power input |
| **MAX30102** | `GND` | `GND` | Black | Ground connection |
| **MAX30102** | `SDA` | `GPIO 21` | Blue | Primary I2C Data Line |
| **MAX30102** | `SCL` | `GPIO 22` | Yellow | Primary I2C Clock Line |
| **DS18B20 (Temperature Sensor)** | `VDD` / Red | `3V3` | Red | 3.3V power input |
| **DS18B20** | `GND` / Black | `GND` | Black | Ground connection |
| **DS18B20** | `DATA` / Yellow | `GPIO 4` | Green | OneWire Bus Data line |
| **DS18B20 Resistor** | Pull-up | Across `VDD` & `DATA` | — | **Mandatory 4.7kΩ Pull-up Resistor** |
| **MPU6050 (6-Axis Motion)** | `VCC` | `3V3` | Red | 3.3V power input |
| **MPU6050** | `GND` | `GND` | Black | Ground connection |
| **MPU6050** | `SDA` | `GPIO 21` | Blue | Shared I2C Data Line |
| **MPU6050** | `SCL` | `GPIO 22` | Yellow | Shared I2C Clock Line |
| **Optional OLED (SSD1306)** | `VCC` / `GND` | `3V3` / `GND` | Red / Black | Optional 0.96" 128x64 OLED display |
| **Optional OLED** | `SDA` / `SCL` | `GPIO 21` / `GPIO 22` | Blue / Yellow | Shared I2C Bus |
| **Optional Buzzer / LED** | `POS` / `NEG` | `GPIO 15` / `GND` | White / Black | Optional status indicator |

---

## ⚡ Important Wiring & I2C Bus Rules

1. **Shared I2C Bus**: The MAX30102 and MPU6050 both use I2C communication and share `GPIO 21 (SDA)` and `GPIO 22 (SCL)`. I2C devices can safely share the same clock and data pins because MAX30102 (`0x57`) and MPU6050 (`0x68`) have unique I2C slave addresses.
2. **DS18B20 Pull-up Resistor**: A **4.7kΩ pull-up resistor** MUST be placed between the DS18B20 `DATA` pin (GPIO 4) and `3V3` power. Without this resistor, the OneWire protocol cannot pull the bus HIGH and temperature readings will fail (`-127.0°C`).
3. **Operating Voltage**: Ensure all sensors receive 3.3V VCC. Applying 5V directly to ESP32 GPIO inputs will permanently damage the microcontroller.
