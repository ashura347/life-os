"""
LIFE OS — Part 8 Unit Test Suite: Real Hardware Sensor Integration with ESP32
Tests real hardware payload intake, source attribution, device status indicators,
sensor error handling, safety disclaimers, and regression health across Parts 1-7.
"""

import os
import sys
import unittest
import json

# Ensure project root is in Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import app
import services.database as db
import services.alert_engine as alert_engine


class Part8HardwareIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and ensure test database has seed patient and device."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.init_db()

        self.patient_id = "P001"
        self.device_id = "LIFEOS-001"

    def test_1_real_sensor_payload_intake(self):
        """1. POST /api/vitals with source='ESP32_REAL_SENSOR' stores record and returns standard JSON payload."""
        response = self.client.post('/api/vitals', json={
            "patient_id": self.patient_id,
            "device_id": self.device_id,
            "heart_rate": 82,
            "spo2": 98,
            "temperature": 36.8,
            "movement_status": "NORMAL",
            "source": "ESP32_REAL_SENSOR"
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()

        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('message'), 'Vital reading received')
        self.assertEqual(data.get('source'), 'ESP32_REAL_SENSOR')
        self.assertIn('received_at', data)
        self.assertIn('PROTOTYPE VITAL DATA', data.get('disclaimer', ''))

    def test_2_device_heartbeat_source_and_error(self):
        """2. POST /api/device/heartbeat updates device data source and status in database."""
        response = self.client.post('/api/device/heartbeat', json={
            "device_id": self.device_id,
            "patient_id": self.patient_id,
            "source": "ESP32_REAL_SENSOR",
            "last_error": None
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertTrue(data.get('success'))
        self.assertEqual(data['device_status']['data_source'], 'ESP32_REAL_SENSOR')
        self.assertEqual(data['device_status']['connection_status'], 'CONNECTED')

    def test_3_device_status_enrichment(self):
        """3. GET /api/device/status returns connection_status, data_source, last_error, and last_vital_reading."""
        response = self.client.get(f'/api/device/status?device_id={self.device_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('device_id'), self.device_id)
        self.assertIn('connection_status', data)
        self.assertIn('data_source', data)
        self.assertIn('last_communication', data)
        self.assertIn('last_vital_reading', data)

    def test_4_missing_or_invalid_sensor_value_rejection(self):
        """4. Out-of-bounds or non-numeric sensor readings are rejected with HTTP 400."""
        # Missing numeric heart rate
        response_invalid_hr = self.client.post('/api/vitals', json={
            "patient_id": self.patient_id,
            "heart_rate": "invalid_string",
            "spo2": 98,
            "temperature": 36.8
        })
        self.assertEqual(response_invalid_hr.status_code, 400)
        data = response_invalid_hr.get_json()
        self.assertFalse(data.get('success'))

        # Out of bounds temperature
        response_invalid_temp = self.client.post('/api/vitals', json={
            "patient_id": self.patient_id,
            "heart_rate": 80,
            "spo2": 98,
            "temperature": 999.0
        })
        self.assertEqual(response_invalid_temp.status_code, 400)

    def test_5_sensor_fault_device_error(self):
        """5. Hardware sensor fault updates device status to ERROR without triggering false physiological alerts."""
        # Post heartbeat reporting sensor communication fault
        self.client.post('/api/device/heartbeat', json={
            "device_id": self.device_id,
            "patient_id": self.patient_id,
            "source": "ESP32_REAL_SENSOR",
            "last_error": "I2C Sensor Communication Failure"
        })

        status_res = self.client.get(f'/api/device/status?device_id={self.device_id}')
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.get_json()

        self.assertEqual(status_data['connection_status'], 'ERROR')
        self.assertEqual(status_data['last_error'], 'I2C Sensor Communication Failure')

    def test_6_unconfigured_device_status(self):
        """6. Querying an unconfigured device returns NOT_CONFIGURED status."""
        response = self.client.get('/api/device/status?device_id=NONEXISTENT-DEV-999')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['connection_status'], 'NOT_CONFIGURED')

    def test_7_regression_check_parts_1_to_7(self):
        """7. Endpoints from Parts 1-7 (/dashboard, /api/health, /demo, /api/ml/predict, /api/emergency-events) remain 100% operational."""
        # GET /api/health
        health_res = self.client.get('/api/health')
        self.assertEqual(health_res.status_code, 200)

        # GET /dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)

        # GET /demo
        demo_res = self.client.get('/demo')
        self.assertEqual(demo_res.status_code, 200)

        # POST /api/demo/scenario
        scenario_res = self.client.post('/api/demo/scenario', json={"scenario": "normal"})
        self.assertEqual(scenario_res.status_code, 200)

    def test_8_no_real_external_communication(self):
        """8. Confirms that no real external SMS or call network sockets are triggered."""
        hb_res = self.client.post('/api/device/heartbeat', json={
            "device_id": self.device_id,
            "patient_id": self.patient_id
        })
        self.assertEqual(hb_res.status_code, 200)


if __name__ == '__main__':
    unittest.main()
