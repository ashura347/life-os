"""
LIFE OS — Prototype Test Data Utilities (tests/test_data.py)
Provides standardized, clearly labeled demonstration test datasets for testing and Demo Mode.
OPERATES STRICTLY IN TEST MODE. NO REAL PATIENT DATA OR EXTERNAL EMERGENCY DISPATCHES.
"""

TEST_PATIENT_P001 = {
    "patient_id": "P001",
    "name": "Demo Patient",
    "age": 30,
    "emergency_contact": "Demo Contact (+91 98765 43210)",
    "location": "Pune, Maharashtra",
    "latitude": 18.5204,
    "longitude": 73.8567
}

TEST_PATIENT_E2E = {
    "patient_id": "P_E2E",
    "name": "E2E Integration Test Patient",
    "age": 42,
    "emergency_contact": "Test Contact (+91 90000 11111)",
    "location": "Pune, Maharashtra",
    "latitude": 18.5204,
    "longitude": 73.8567
}

TEST_DEVICE = {
    "device_id": "LIFEOS-001",
    "patient_id": "P001",
    "status": "CONNECTED"
}

NORMAL_VITALS_PAYLOAD = {
    "patient_id": "P001",
    "heart_rate": 75,
    "spo2": 98,
    "temperature": 36.8,
    "movement_status": "Resting"
}

WARNING_VITALS_PAYLOAD = {
    "patient_id": "P001",
    "heart_rate": 108,
    "spo2": 94,
    "temperature": 37.9,
    "movement_status": "Moving"
}

CRITICAL_VITALS_PAYLOAD = {
    "patient_id": "P001",
    "heart_rate": 125,
    "spo2": 91,
    "temperature": 38.6,
    "movement_status": "Restless"
}

CURATED_TEST_FACILITIES = [
    {
        "facility_id": "HOSP-001",
        "name": "KEM Hospital Pune",
        "address": "489, Rasta Peth, Sardar Moodliar Road, Pune, Maharashtra 411011",
        "distance": "1.8 km",
        "contact_number": "+91 20 2612 5600",
        "services": ["24/7 Emergency Care", "ICU", "Cardiology", "Trauma Center"],
        "source": "Curated Prototype Healthcare Registry (Pune)"
    },
    {
        "facility_id": "HOSP-002",
        "name": "Ruby Hall Clinic",
        "address": "40, Sassoon Road, Sangamvadi, Pune, Maharashtra 411001",
        "distance": "3.2 km",
        "contact_number": "+91 20 6645 5100",
        "services": ["Emergency & Trauma", "Cardiac ICU", "Neurology"],
        "source": "Curated Prototype Healthcare Registry (Pune)"
    }
]

SAFETY_DISCLAIMER = (
    "STUDENT PROTOTYPE NOTICE: LIFE OS is an academic decision-support demonstration project. "
    "All vital readings, alerts, healthcare facilities, and notifications operate in TEST MODE. "
    "System outputs do NOT constitute certified clinical medical diagnoses or automated emergency dispatches."
)
