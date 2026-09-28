"""
LIFE OS — Automated Test Suite for Part 2
Verifies Patient CRUD, Vital Records CRUD, REST API endpoints, and validation logic.
"""

import sys
import os
import unittest

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app
import services.database as db


class Part2TestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and ensure DB schema is initialized."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.init_db()

    def test_1_create_patient(self):
        """1. Test creating a new patient via API."""
        import time
        unique_id = f"P_TEST_{int(time.time()*1000)}"
        payload = {
            'patient_id': unique_id,
            'name': 'Unit Test Patient',
            'age': 40,
            'emergency_contact': 'Test Contact Info'
        }
        response = self.client.post('/api/patients', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['patient']['patient_id'], unique_id)

    def test_2_retrieve_patient(self):
        """2. Test retrieving patient details by patient_id."""
        response = self.client.get('/api/patients/P001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['patient']['patient_id'], 'P001')
        self.assertEqual(data['patient']['name'], 'Demo Patient')

    def test_3_insert_vital_record(self):
        """3. Test inserting a vital record for an existing patient."""
        payload = {
            'patient_id': 'P001',
            'heart_rate': 85,
            'spo2': 99,
            'temperature': 37.1,
            'movement_status': 'Active'
        }
        response = self.client.post('/api/vitals', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['vitals']['heart_rate'], 85)
        self.assertEqual(data['vitals']['spo2'], 99)

    def test_4_retrieve_latest_vital_record(self):
        """4. Test retrieving the latest vital record for a patient."""
        response = self.client.get('/api/vitals/P001/latest')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('vitals', data)
        self.assertEqual(data['vitals']['patient_id'], 'P001')

    def test_5_retrieve_vital_history(self):
        """5. Test retrieving recent vital records history."""
        response = self.client.get('/api/vitals/P001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['records_count'] > 0)
        self.assertIsInstance(data['records'], list)

    def test_6_retrieve_dashboard(self):
        """6. Test dashboard page rendering with SQLite database data."""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Demo Patient', response.data)
        self.assertIn(b'P001', response.data)

    def test_7_invalid_patient_id(self):
        """7. Test graceful handling of non-existent patient IDs."""
        response = self.client.get('/api/patients/NONEXISTENT_ID_999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)

    def test_8_invalid_vital_data(self):
        """8. Test validation error responses on invalid vital payload data."""
        # Non-numeric Heart Rate
        payload_bad_hr = {
            'patient_id': 'P001',
            'heart_rate': 'INVALID_HR',
            'spo2': 98,
            'temperature': 36.8
        }
        res1 = self.client.post('/api/vitals', json=payload_bad_hr)
        self.assertEqual(res1.status_code, 400)

        # SpO2 Out of Range (>100)
        payload_bad_spo2 = {
            'patient_id': 'P001',
            'heart_rate': 80,
            'spo2': 150,
            'temperature': 36.8
        }
        res2 = self.client.post('/api/vitals', json=payload_bad_spo2)
        self.assertEqual(res2.status_code, 400)

        # Non-existent Patient Insertion
        payload_bad_patient = {
            'patient_id': 'PATIENT_DOES_NOT_EXIST',
            'heart_rate': 80,
            'spo2': 98,
            'temperature': 36.8
        }
        res3 = self.client.post('/api/vitals', json=payload_bad_patient)
        self.assertEqual(res3.status_code, 404)


if __name__ == '__main__':
    unittest.main()
