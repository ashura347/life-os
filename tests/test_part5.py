"""
LIFE OS — Automated Test Suite for Part 5 (AI/ML Risk Analysis)
Verifies ML service inference, model fallbacks, POST /api/ml/predict API,
input feature validation, and independence from Part 4 rule engine.
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
import services.ml_service as ml_service
import services.alert_engine as alert_engine


class Part5TestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and ensure DB schema is initialized."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.init_db()

        self.unique_id = f"P_PART5_{int(time.time()*1000)}"
        db.add_patient(self.unique_id, "ML Test Patient", 50, "ML Emergency Contact")

    def test_1_ml_service_unavailable_fallback(self):
        """1. Test that ml_service returns graceful fallback when model path is invalid."""
        original_path = ml_service.MODEL_PATH
        ml_service.MODEL_PATH = "invalid/path/to/missing_model.json"
        ml_service._MODEL_CACHE = None # Reset cache

        res = ml_service.predict_risk({'heart_rate': 80, 'spo2': 98, 'temperature': 36.8})
        self.assertFalse(res['available'])
        self.assertEqual(res['risk_category'], 'UNKNOWN')
        self.assertIn('disclaimer', res)

        # Restore path
        ml_service.MODEL_PATH = original_path
        ml_service._MODEL_CACHE = None

    def test_2_valid_prediction_request(self):
        """2. Test POST /api/ml/predict with valid telemetry returns structured risk assessment."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 78,
            'spo2': 98,
            'temperature': 36.8,
            'movement_status': 'Normal'
        }
        res = self.client.post('/api/ml/predict', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn(data['risk_category'], ['LOW_RISK', 'MODERATE_RISK', 'ELEVATED'])
        self.assertGreaterEqual(data['confidence'], 0.0)
        self.assertEqual(data['model_version'], 'prototype-v1')
        self.assertIn('disclaimer', data)

    def test_3_invalid_prediction_input(self):
        """3. Test POST /api/ml/predict returns HTTP 400 on non-numeric vital input."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 'NON_NUMERIC_STRING',
            'spo2': 98,
            'temperature': 36.8
        }
        res = self.client.post('/api/ml/predict', json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)

    def test_4_missing_required_features(self):
        """4. Test POST /api/ml/predict returns HTTP 400 when required fields are missing."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 80
            # Missing spo2 and temperature
        }
        res = self.client.post('/api/ml/predict', json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)

    def test_5_model_loading_failure_handling(self):
        """5. Test that server API returns 200 with available=false if model fails to load."""
        original_cache = ml_service._MODEL_CACHE
        ml_service._MODEL_CACHE = {'tree_root': None} # Corrupted cache

        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 80,
            'spo2': 98,
            'temperature': 36.8
        }
        res = self.client.post('/api/ml/predict', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data['available'])
        self.assertEqual(data['risk_category'], 'UNKNOWN')

        # Restore cache
        ml_service._MODEL_CACHE = original_cache

    def test_6_part4_rule_engine_independence(self):
        """6. Test that Part 4 rule-based alert engine operates independently from ML prediction."""
        payload_high_hr = {
            'patient_id': self.unique_id,
            'heart_rate': 125,
            'spo2': 98,
            'temperature': 36.8
        }
        # Post 2 consecutive high HR readings to trigger Part 4 Rule Engine CRITICAL alert
        self.client.post('/api/vitals', json=payload_high_hr)
        res_vitals = self.client.post('/api/vitals', json=payload_high_hr)
        vitals_data = res_vitals.get_json()

        # Rule engine creates alert
        self.assertTrue(vitals_data['alert_created'])
        self.assertEqual(vitals_data['patient_status'], 'CRITICAL')

        # Rule status check
        rule_status = alert_engine.get_patient_system_status(self.unique_id)
        self.assertEqual(rule_status, 'CRITICAL')

    def test_7_ml_output_displayed_separately(self):
        """7. Test that ML prediction API returns advisory category distinct from rule status."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 80,
            'spo2': 98,
            'temperature': 36.8
        }
        res_ml = self.client.post('/api/ml/predict', json=payload)
        data_ml = res_ml.get_json()

        # Verify response contains specific ML metadata
        self.assertIn('risk_category', data_ml)
        self.assertIn('confidence', data_ml)
        self.assertIn('model_version', data_ml)
        self.assertIn('disclaimer', data_ml)

    def test_8_no_emergency_communication_triggered(self):
        """8. Test that ML prediction API does not trigger any side-effect alert creation in database."""
        initial_alerts_count = len(db.get_all_alerts_for_patient(self.unique_id))

        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 140, # Elevated HR
            'spo2': 88,       # Low SpO2
            'temperature': 39.5
        }
        res_ml = self.client.post('/api/ml/predict', json=payload)
        self.assertEqual(res_ml.status_code, 200)

        final_alerts_count = len(db.get_all_alerts_for_patient(self.unique_id))
        # ML prediction alone MUST NOT insert alerts into database
        self.assertEqual(initial_alerts_count, final_alerts_count)


if __name__ == '__main__':
    unittest.main()
