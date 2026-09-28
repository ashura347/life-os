/*
  =============================================================================
  LIFE OS — Patient Monitoring System (Part 3)
  Sensor Configuration & Simulation Header File (sensor_config.h)
  =============================================================================

  PLANNED HARDWARE SENSORS FOR PART 4 INTEGRATION:
  1. MAX30102 (I2C)       : Photoplethysmogram (PPG) Heart Rate & SpO2 Sensor
     - SDA Pin  : GPIO 21
     - SCL Pin  : GPIO 22
     
  2. DS18B20 (OneWire)    : Digital Thermal Temperature Sensor
     - Data Pin : GPIO 4 (with 4.7kΩ pull-up resistor)
     
  3. MPU6050 (I2C)        : 6-Axis Accelerometer & Gyroscope Motion Sensor
     - SDA Pin  : GPIO 21
     - SCL Pin  : GPIO 22

  NOTICE:
  In Part 3, physical hardware sensor reading functions are stubbed with
  realistic simulated test generators.
*/

#ifndef SENSOR_CONFIG_H
#define SENSOR_CONFIG_H

#include <Arduino.h>

// =============================================================================
// Hardware Pin Mapping Definitions (Planned for Part 4 Wiring)
// =============================================================================
#define I2C_SDA_PIN          21
#define I2C_SCL_PIN          22
#define DS18B20_ONEWIRE_PIN  4

// =============================================================================
// Sensor Placeholder & Simulation Generator Functions
// =============================================================================

/**
 * TODO (Part 4): Replace with actual MAX30102 I2C sensor library calls.
 * Returns: Simulated Heart Rate in BPM (60 - 120).
 */
inline int readSimulatedHeartRate() {
  // Generates slight micro-fluctuations around baseline 82 BPM
  return 80 + random(-3, 6);
}

/**
 * TODO (Part 4): Replace with actual MAX30102 SpO2 calculation algorithm.
 * Returns: Simulated Oxygen Saturation percentage (95 - 100%).
 */
inline int readSimulatedSpO2() {
  return 97 + random(0, 3);
}

/**
 * TODO (Part 4): Replace with actual DallasTemperature DS18B20 sensor reading.
 * Returns: Simulated Body Temperature in °C (36.4 - 37.2°C).
 */
inline float readSimulatedTemperature() {
  float val = 36.8 + (random(-2, 3) * 0.1);
  return round(val * 10.0) / 10.0;
}

/**
 * TODO (Part 4): Replace with actual MPU6050 3-axis accelerometer motion algorithm.
 * Returns: Simulated movement status string.
 */
inline String readSimulatedMovement() {
  const char* states[] = {"Normal", "Resting", "Active"};
  int idx = random(0, 3);
  return String(states[idx]);
}

#endif // SENSOR_CONFIG_H
