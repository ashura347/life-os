# LIFE OS — Hardware Testing & Validation Plan

This document outlines the 13-point validation checklist for testing real ESP32 microcontroller sensors connected to the LIFE OS Flask backend.

---

## 📋 13-Point Hardware Test Matrix

| # | Test Scenario | Expected Outcome | Pass/Fail Criteria |
|---|---|---|---|
| 1 | **ESP32 Power On** | Red power LED illuminates | ESP32 initializes without reboot loops |
| 2 | **Sensor Detection** | MAX30102, DS18B20, and MPU6050 detected | Serial Monitor displays `SUCCESS!` for all 3 sensors |
| 3 | **Serial Debugging** | Sensor readings printed every 3s | Valid numeric values displayed in Serial Monitor |
| 4 | **Wi-Fi Connection** | ESP32 obtains local IP address | Serial Monitor prints `[Wi-Fi] Connected successfully!` |
| 5 | **Flask Server Reachability** | HTTP connection established | HTTP status code `200` / `201` returned |
| 6 | **Heartbeat Intake** | `POST /api/device/heartbeat` succeeds | Device status updates to `CONNECTED` in SQLite |
| 7 | **Vital Data Intake** | `POST /api/vitals` succeeds | Vitals record stored with `source: ESP32_REAL_SENSOR` |
| 8 | **Dashboard Updates** | Dashboard refreshes automatically | Dashboard displays real hardware badge and updated vitals |
| 9 | **Invalid Reading Rejection** | Out-of-bounds vitals rejected | Backend returns `400 Bad Request` without storing corrupted data |
| 10 | **Wi-Fi Disconnection Handling** | Connection drop detected | Firmware retries connection gracefully without crashing |
| 11 | **Sensor Disconnection Fault** | Sensor unplugged | Device status shows `ERROR` / `SENSOR_FAULT` without false medical alerts |
| 12 | **Rule-Based Alert Evaluation** | Abnormal vitals submitted | Rule Engine evaluates rules and creates alert if persistence met |
| 13 | **Notification Safety** | Emergency workflow initiated | Notifications logged in `TEST` mode. Zero real SMS/calls triggered |

---

## 🔒 Safety Verification Protocol

- **Prototype Disclaimer**: Always verify that the dashboard renders: *"Prototype sensor data — not medical-grade."*
- **Test Notification Check**: Confirm `notification_service.py` executes exclusively in `TEST` mode with zero real-world network sockets.
