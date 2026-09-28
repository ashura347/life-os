# LIFE OS — Patient Monitoring and Emergency Response System (Part 8 Complete)

**LIFE OS** is an IoT-based patient monitoring and emergency response system built as a modular student prototype. Part 8 introduces **Real Hardware Sensor Integration with ESP32 microcontrollers** (MAX30102 pulse oximeter, DS18B20 temperature sensor, and MPU6050 accelerometer/gyroscope) while preserving all previous software features, rule evaluations, advisory AI/ML risk predictions, and location-aware emergency response workflows.

---

## ⚡ Integration Report & System Status

- **Complete End-to-End Workflow**: Fully verified from Real Physical ESP32 / Sensor Telemetry Ingestion → Database Persistence → Rule Engine Evaluation → Advisory AI/ML Risk Assessment → Emergency Event Creation → Healthcare Facility Discovery → Test Notification Audit Log → Acknowledge & Resolve Lifecycle.
- **Hardware Integration Status**: ESP32 C++ Firmware (`esp32/real_sensor_device.ino`) complete with pinout maps, library guides, fault handling, heartbeat telemetry, and data source tagging (`ESP32_REAL_SENSOR`).
- **System Health Diagnostics (`GET /api/health`)**: Active and reporting `database: connected`, `ml_model: available`, `alert_engine: ready`, `hospital_service: test_mode`, `notification_mode: TEST`.
- **Test Suite Status**: **55 / 55 Unit, Hardware Intake & End-to-End Integration Tests Passed** (0 Failures).

---

## ⚡ End-to-End Architecture & Data Flow

```text
                               +-----------------------------+
                               |   ESP32 / Simulator / Demo  |
                               +-----------------------------+
                                              |
                                      POST /api/vitals
                                              v
                               +-----------------------------+
                               |    Flask REST API Intake    |
                               +-----------------------------+
                                     /       |           \
                                    /        |            \
                                   v         v             v
             +-----------------------+  +----------+  +-----------------------+
             | Part 4 Rule Engine    |  |  SQLite  |  | Part 5 Advisory ML    |
             | - Threshold evaluation|  | Database |  | - Predictive risk     |
             | - Active deduplication|  +----------+  | - Confidence meter    |
             +-----------------------+                +-----------------------+
                         |                                        |
                         v (Escalation)                           v (Advisory UI)
             +-----------------------+                +-----------------------+
             | Part 6 Emergency      |                | Dashboard & Health    |
             | Response Workflow     |                | Status Panel          |
             +-----------------------+                | - GET /api/health     |
              /          |          \                 | - System Health Grid  |
             v           v           v                +-----------------------+
    +------------+  +----------+  +-------------------+
    | Registered |  | Nearby   |  | TEST Notification |
    | Location   |  | Facilities| | (Audit Log Only)  |
    +------------+  +----------+  +-------------------+
```

> ⚠️ **IMPORTANT SAFETY & CLINICAL DISCLAIMER**  
> - **Student Prototype Only**: LIFE OS is an academic demonstration system and is NOT a certified clinical medical device.
> - **No Diagnostic Claims**: System alerts and emergency events represent software rule evaluations and do NOT provide certified medical diagnoses.
> - **No Real Emergency Dispatches**: The emergency response engine operates strictly in **TEST mode**. Zero real SMS messages, phone calls, or hospital dispatches are executed.
> - **Facility Availability**: Facility details (name, address, distance, contact) are retrieved from curated test registries or map APIs. Real-time emergency room, ICU bed, or doctor capacity is NOT verified or claimed.

---

## 🗄️ Database Schemas

### 1. `patients` Table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Primary key |
| `patient_id` | TEXT UNIQUE | Unique patient code (e.g. `P001`) |
| `name` | TEXT | Patient full name |
| `age` | INTEGER | Patient age |
| `emergency_contact` | TEXT | Contact telephone/name |
| `location` | TEXT | Registered location (default `'Pune, Maharashtra'`) |
| `latitude` | REAL | Latitude coordinate (`18.5204`) |
| `longitude` | REAL | Longitude coordinate (`73.8567`) |
| `created_at` | TIMESTAMP | Registration timestamp |

### 2. `vital_records` Table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Record ID |
| `patient_id` | TEXT | References `patients(patient_id)` |
| `heart_rate` | INTEGER | Pulse in BPM |
| `spo2` | INTEGER | Blood oxygen % |
| `temperature` | REAL | Body temp in °C |
| `movement_status` | TEXT | Activity status (`Resting`, `Moving`, `Restless`) |
| `recorded_at` | TIMESTAMP | Telemetry intake timestamp |

### 3. `devices` Table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Device ID |
| `device_id` | TEXT UNIQUE | Hardware identifier (`LIFEOS-001`) |
| `patient_id` | TEXT | Assigned patient ID |
| `last_seen` | TIMESTAMP | Heartbeat timestamp |

### 4. `alerts` Table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Alert ID |
| `patient_id` | TEXT | References `patients(patient_id)` |
| `alert_type` | TEXT | Alert category (e.g. `HIGH_HEART_RATE_CRITICAL`) |
| `severity` | TEXT | `WARNING` or `CRITICAL` |
| `message` | TEXT | Human-readable explanation |
| `triggered_at` | TIMESTAMP | Escalation timestamp |
| `status` | TEXT | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED` |

### 5. `emergency_events` Table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Event ID |
| `alert_id` | INTEGER | References `alerts(id)` |
| `patient_id` | TEXT | References `patients(patient_id)` |
| `location` | TEXT | Location string |
| `latitude` | REAL | Latitude |
| `longitude` | REAL | Longitude |
| `selected_facility` | TEXT | Selected destination hospital |
| `response_status` | TEXT | `CREATED`, `FACILITY_SEARCHED`, `CONTACT_NOTIFIED`, `ACKNOWLEDGED`, `RESOLVED`, `TEST_COMPLETED` |

---

## 🔌 API Endpoint Reference

| Method | Endpoint | Description | Payload / Parameters |
|---|---|---|---|
| `GET` | `/api/health` | System health check diagnostics | Returns application & service health status JSON |
| `POST` | `/api/demo/scenario` | Execute prototype demo simulation scenario | Payload: `{"scenario": "normal" \| "warning" \| "critical" \| "emergency" \| "reset"}` |
| `POST` | `/api/vitals` | Intake telemetry, evaluate rules & ML risk | Payload: `{"patient_id": "P001", "heart_rate": 82, "spo2": 98, "temperature": 36.8, "movement_status": "Resting"}` |
| `GET` | `/api/vitals/<patient_id>/latest` | Get latest telemetry for patient | URL parameter -> Latest vital record JSON |
| `POST` | `/api/ml/predict` | Get advisory AI/ML risk prediction | Payload: `{"patient_id": "P001", "heart_rate": 125, "spo2": 91, ...}` |
| `POST` | `/api/emergency-events` | Initiate location-aware emergency response | Payload: `{"alert_id": 1}` |
| `GET` | `/api/emergency-events/<event_id>` | Get emergency event details | URL parameter -> Emergency event JSON |
| `POST` | `/api/emergency-events/<event_id>/acknowledge` | Mark emergency event `ACKNOWLEDGED` | URL parameter |
| `POST` | `/api/emergency-events/<event_id>/resolve` | Mark emergency event `RESOLVED` | Optional payload: `{"selected_facility": "Ruby Hall Clinic"}` |
| `POST` | `/api/device/heartbeat` | Update ESP32 device heartbeat | Payload: `{"device_id": "LIFEOS-001", "patient_id": "P001"}` |
| `GET` | `/api/alerts/<patient_id>` | Get alert history log | URL parameter |

---

## 📂 Project Structure

```
life_os/
│
├── app.py                      # Flask server registering patient, vital, device, alert, ml, emergency, health, & demo blueprints
├── requirements.txt            # Python dependencies (Flask>=3.0.0, scikit-learn>=1.3.0, joblib>=1.3.0)
│
├── database/
│   └── life_os.db              # SQLite DB containing patients, vital_records, devices, alerts, & emergency_events
│
├── ml/                         # Machine Learning module
│   ├── README.md               # Model architecture & metric documentation
│   ├── dataset_generator.py    # Generator for 1,500 sample synthetic vitals
│   ├── predict.py              # Pure Python Decision Tree inference engine
│   ├── train_model.py          # Training pipeline & JSON exporter
│   ├── data/
│   │   └── synthetic_vitals.csv# Synthetic training dataset
│   └── models/
│       └── risk_model.json     # Serialized decision tree model
│
├── services/
│   ├── database.py             # SQLite service layer (CRUD helpers & schema migration)
│   ├── alert_config.py         # Prototype threshold settings & persistence rules
│   ├── alert_engine.py         # Rule-based Alert Engine evaluation
│   ├── ml_service.py           # Safe ML prediction service wrapper
│   ├── hospital_service.py     # Nearby healthcare facility discovery service
│   ├── notification_service.py # Test emergency notification service (TEST mode audit log)
│   ├── emergency_service.py    # Emergency response event workflow orchestrator
│   ├── health_service.py       # [NEW] System health diagnostics service
│   └── demo_service.py         # [NEW] Prototype demonstration scenario orchestrator
│
├── routes/
│   ├── patient_routes.py       # Patient management views & REST API
│   ├── vital_routes.py         # Vital history views & POST /api/vitals
│   ├── device_routes.py        # Device heartbeat REST API
│   ├── alert_routes.py         # Alert history views & management REST API
│   ├── ml_routes.py            # POST /api/ml/predict REST API route
│   ├── emergency_routes.py     # Emergency response REST API & Web views
│   ├── health_routes.py        # [NEW] GET /api/health system health API
│   └── demo_routes.py           # [NEW] Demo Mode control room view & API
│
├── esp32/
│   ├── simulated_device.ino    # Arduino C++ firmware sketch for ESP32 microcontrollers
│   ├── sensor_config.h         # C++ sensor configuration header
│   └── simulated_device.py     # Python CLI simulator script
│
├── templates/
│   ├── base.html               # [UPDATED] Layout template with Demo Control Room nav link
│   ├── dashboard.html          # [UPDATED] Dashboard with System Integration & Health Diagnostics Card
│   ├── demo.html               # [NEW] Interactive Demo Mode Control Room UI
│   ├── emergency.html          # Location-Aware Emergency Event Hub UI
│   ├── emergency_history.html  # Patient emergency event history log
│   ├── alerts.html             # Alert Management UI
│   ├── patient.html            # Patient profile view
│   ├── patient_management.html # Patient registration form
│   └── vitals.html             # Vital history table
│
├── static/
│   ├── css/
│   │   └── style.css           # [UPDATED] Styling for health cards, demo console, & status badges
│   └── js/
│       └── dashboard.js        # Client JS with periodic polling & emergency trigger helpers
│
├── tests/
│   ├── test_data.py            # [NEW] Prototype test data utilities & datasets
│   ├── test_part2.py           # Database & patient unit tests (8/8 passed)
│   ├── test_part3.py           # IoT REST API & device status test suite (8/8 passed)
│   ├── test_part4.py           # Part 4 Alert Engine unit test suite (11/11 passed)
│   ├── test_part5.py           # Part 5 AI/ML Risk Analysis test suite (8/8 passed)
│   ├── test_part6.py           # Part 6 Location-Aware Emergency Response test suite (11/11 passed)
│   └── test_end_to_end.py      # [NEW] Part 7 End-to-End 17-step integration test suite (1/1 passed)
│
└── README.md                   # Project documentation
```

---

## 🚀 Installation & Execution Guide

### 1. Environment Setup
```bash
# Navigate to project directory
cd C:\Users\ARYAN\.gemini\antigravity\scratch\life_os

# Activate Virtual Environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 2. Start the Flask Server
```bash
.\.venv\Scripts\python.exe app.py
```
Server listens on: `http://127.0.0.1:5000`

### 3. Open Web Dashboards
- **Main Patient Dashboard**: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
- **Demo Control Room**: [http://127.0.0.1:5000/demo](http://127.0.0.1:5000/demo)
- **Emergency Response Event**: [http://127.0.0.1:5000/emergency/1](http://127.0.0.1:5000/emergency/1)
- **API Health Diagnostics**: [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)

---

## 🧪 Running Automated Tests

Run all unit and end-to-end test suites (47 total tests):

```bash
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Run specific test suites:
```bash
# End-to-End 17-Step Integration Test
.\.venv\Scripts\python.exe tests/test_end_to_end.py

# Part 6 Location-Aware Emergency Response Test
.\.venv\Scripts\python.exe tests/test_part6.py
```

---

## 🎮 How to Use Interactive Demo Mode

1. Navigate to `http://127.0.0.1:5000/demo`.
2. Observe the prominent **DEMO / TEST MODE ACTIVE** banner.
3. Click scenario buttons to test live system behavior:
   - **1. Normal Condition**: Posts 75 BPM / 98% SpO2. Status: `NORMAL`.
   - **2. Warning Condition**: Posts 108 BPM / 94% SpO2. Status: `WARNING`.
   - **3. Critical Condition**: Posts consecutive 125 BPM vitals. Triggers `HIGH_HEART_RATE_CRITICAL` alert. Status: `CRITICAL`.
   - **4. Emergency Response Event**: Escalates alert to emergency event, discovers Pune facilities, logs test notification.
   - **5. Reset Demo State**: Resolves active alerts and resets status to `NORMAL`.

---

## 🚀 Future Hardware & Clinical Deployment Roadmap

1. **Clinical Regulatory Validation**: Formal clinical trials and ISO 13485 / FDA SaMD compliance certification.
2. **End-to-End Security**: Integration of OAuth2 / JWT authentication, role-based access control (RBAC), and HIPAA-compliant data encryption at rest.
3. **Verified Hospital Integration**: Direct API connection with regional Health Information Exchanges (HIEs) for live ICU bed and emergency room capacity data.
4. **Telecommunications Carrier Integration**: Authorized SMS and voice call dispatch gateways (e.g. Twilio / Sinch) with patient consent management.
5. **Physical ESP32 Hardware Integration**: Connecting physical MAX30102 pulse oximeter sensors, DS18B20 temperature probes, and SIM808 GPS modules over Wi-Fi/4G.
