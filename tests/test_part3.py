"""
LIFE OS — Automated Test Suite for Part 3
Verifies ESP32 Telemetry POST /api/vitals, Device Heartbeats, Status Timeouts, and REST APIs.
"""

import sys
import os
import unittest
import time

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app
import services.database as db


class Part3TestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and initialize DB schemas."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.init_db()

    def test_1_post_vitals_valid(self):
        """1. Test POST /api/vitals with valid telemetry payload."""
        payload = {
            'patient_id': 'P001',
            'heart_rate': 84,
            'spo2': 98,
            'temperature': 36.9,
            'movement_status': 'Resting'
        }
        response = self.client.post('/api/vitals', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['vitals']['heart_rate'], 84)

    def test_2_post_vitals_invalid_data(self):
        """2. Test POST /api/vitals with invalid numeric data."""
        payload = {
            'patient_id': 'P001',
            'heart_rate': 'NOT_NUMERIC',
            'spo2': 98,
            'temperature': 36.8
        }
        response = self.client.post('/api/vitals', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_3_post_vitals_nonexistent_patient(self):
        """3. Test POST /api/vitals with a non-existent patient ID."""
        payload = {
            'patient_id': 'NONEXISTENT_P000',
            'heart_rate': 80,
            'spo2': 98,
            'temperature': 36.8
        }
        response = self.client.post('/api/vitals', json=payload)
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)

    def test_4_get_latest_vitals(self):
        """4. Test GET /api/vitals/<patient_id>/latest returns recent record."""
        response = self.client.get('/api/vitals/P001/latest')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['vitals']['patient_id'], 'P001')

    def test_5_device_heartbeat_endpoint(self):
        """5. Test POST /api/device/heartbeat registers device ping."""
        payload = {
            'device_id': 'LIFEOS-001',
            'patient_id': 'P001'
        }
        response = self.client.post('/api/device/heartbeat', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['device_status']['connection_status'], 'CONNECTED')

    def test_6_device_status_endpoint(self):
        """6. Test GET /api/device/status returns status object."""
        # Ping heartbeat first
        self.client.post('/api/device/heartbeat', json={'device_id': 'LIFEOS-001', 'patient_id': 'P001'})

        response = self.client.get('/api/device/status?device_id=LIFEOS-001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['connection_status'], 'CONNECTED')
        self.assertIn('disclaimer', data)

    def test_7_dashboard_retrieves_latest(self):
        """7. Test dashboard renders and retrieves latest database vitals & device state."""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Demo Patient', response.data)
        self.assertIn(b'LIFEOS-001', response.data)

    def test_8_simulated_esp32_payload_format(self):
        """8. Test ESP32 JSON payload formatting compliance."""
        esp32_payload = {
            'patient_id': 'P001',
            'heart_rate': 82,
            'spo2': 98,
            'temperature': 36.8,
            'movement_status': 'Normal'
        }
        response = self.client.post('/api/vitals', json=esp32_payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['vitals']['patient_id'], 'P001')
        self.assertEqual(data['vitals']['movement_status'], 'Normal')


if __name__ == '__main__':
    unittest.main()
