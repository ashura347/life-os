"""
LIFE OS — Automated Test Suite for Part 4
Verifies Alert Engine rules, persistence checking, deduplication, alert lifecycle, and REST APIs.
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
import services.alert_engine as alert_engine


class Part4TestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and ensure DB schema is initialized."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.init_db()

        # Create clean unique test patient for isolated testing
        self.unique_id = f"P_PART4_{int(time.time()*1000)}"
        db.add_patient(self.unique_id, "Alert Test Patient", 45, "Emergency Info")

    def test_1_normal_vital_reading(self):
        """1. Test that normal vitals do not generate any alerts."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 75,
            'spo2': 98,
            'temperature': 36.8,
            'movement_status': 'Normal'
        }
        res = self.client.post('/api/vitals', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertFalse(data['alert_created'])
        self.assertEqual(data['patient_status'], 'NORMAL')

    def test_2_invalid_vital_reading(self):
        """2. Test invalid vital payload returns 400 Bad Request."""
        payload = {
            'patient_id': self.unique_id,
            'heart_rate': 'INVALID_STRING',
            'spo2': 98,
            'temperature': 36.8
        }
        res = self.client.post('/api/vitals', json=payload)
        self.assertEqual(res.status_code, 400)

    def test_3_single_abnormal_reading_persistence_check(self):
        """3. Test that a single noisy abnormal reading does NOT create an alert immediately due to persistence rules."""
        payload_abnormal = {
            'patient_id': self.unique_id,
            'heart_rate': 130, # Critical HR threshold exceeded once
            'spo2': 98,
            'temperature': 36.8
        }
        res = self.client.post('/api/vitals', json=payload_abnormal)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()

        # Single reading should NOT create alert because CONSECUTIVE_ABNORMAL_REQUIRED = 2
        self.assertFalse(data['alert_created'])

    def test_4_repeated_abnormal_readings_trigger_alert(self):
        """4. Test that repeated consecutive abnormal readings trigger an alert when persistence condition is met."""
        payload_high_hr = {
            'patient_id': self.unique_id,
            'heart_rate': 125,
            'spo2': 98,
            'temperature': 36.8
        }
        # Post 1st abnormal reading (no alert yet)
        res1 = self.client.post('/api/vitals', json=payload_high_hr)
        self.assertFalse(res1.get_json()['alert_created'])

        # Post 2nd consecutive abnormal reading (persistence condition met!)
        res2 = self.client.post('/api/vitals', json=payload_high_hr)
        data2 = res2.get_json()
        self.assertTrue(data2['alert_created'])
        self.assertEqual(data2['severity'], 'CRITICAL')
        self.assertEqual(data2['patient_status'], 'CRITICAL')

    def test_5_duplicate_active_alert_prevention(self):
        """5. Test deduplication: repeated abnormal readings do NOT create duplicate active alerts for ongoing conditions."""
        payload_high_hr = {
            'patient_id': self.unique_id,
            'heart_rate': 125,
            'spo2': 98,
            'temperature': 36.8
        }
        # Trigger initial alert
        self.client.post('/api/vitals', json=payload_high_hr)
        res_trigger = self.client.post('/api/vitals', json=payload_high_hr)
        self.assertTrue(res_trigger.get_json()['alert_created'])

        # Post 3rd consecutive reading while alert is still ACTIVE
        res_dup = self.client.post('/api/vitals', json=payload_high_hr)
        self.assertFalse(res_dup.get_json()['alert_created']) # Prevent duplicate

        # Verify only 1 active alert exists in SQLite
        active = db.get_active_alerts(self.unique_id)
        self.assertEqual(len(active), 1)

    def test_6_alert_history_retrieval(self):
        """6. Test GET /api/alerts/<patient_id> retrieves alert history."""
        # Trigger alert
        payload = {'patient_id': self.unique_id, 'heart_rate': 130, 'spo2': 98, 'temperature': 36.8}
        self.client.post('/api/vitals', json=payload)
        self.client.post('/api/vitals', json=payload)

        res = self.client.get(f'/api/alerts/{self.unique_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['alerts_count'] > 0)
        self.assertEqual(data['alerts'][0]['patient_id'], self.unique_id)

    def test_7_acknowledge_alert(self):
        """7. Test POST /api/alerts/<alert_id>/acknowledge marks alert as ACKNOWLEDGED."""
        # Trigger alert
        payload = {'patient_id': self.unique_id, 'heart_rate': 130, 'spo2': 98, 'temperature': 36.8}
        self.client.post('/api/vitals', json=payload)
        res_trig = self.client.post('/api/vitals', json=payload)
        alert_id = res_trig.get_json()['alert_id']

        # Acknowledge Alert
        res_ack = self.client.post(f'/api/alerts/{alert_id}/acknowledge')
        self.assertEqual(res_ack.status_code, 200)
        data_ack = res_ack.get_json()
        self.assertEqual(data_ack['alert']['status'], 'ACKNOWLEDGED')

    def test_8_resolve_alert(self):
        """8. Test POST /api/alerts/<alert_id>/resolve marks alert as RESOLVED and updates status."""
        # Trigger alert
        payload = {'patient_id': self.unique_id, 'heart_rate': 130, 'spo2': 98, 'temperature': 36.8}
        self.client.post('/api/vitals', json=payload)
        res_trig = self.client.post('/api/vitals', json=payload)
        alert_id = res_trig.get_json()['alert_id']

        # Resolve Alert
        res_res = self.client.post(f'/api/alerts/{alert_id}/resolve')
        self.assertEqual(res_res.status_code, 200)
        data_res = res_res.get_json()
        self.assertEqual(data_res['alert']['status'], 'RESOLVED')

        # Verify patient status resets back to NORMAL
        status = alert_engine.get_patient_system_status(self.unique_id)
        self.assertEqual(status, 'NORMAL')

    def test_9_nonexistent_patient(self):
        """9. Test GET /api/alerts/<nonexistent_id> returns 404 Not Found."""
        res = self.client.get('/api/alerts/NONEXISTENT_P9999')
        self.assertEqual(res.status_code, 404)

    def test_10_nonexistent_alert(self):
        """10. Test acknowledging/resolving a non-existent alert_id returns 404."""
        res_ack = self.client.post('/api/alerts/999999/acknowledge')
        self.assertEqual(res_ack.status_code, 404)

        res_res = self.client.post('/api/alerts/999999/resolve')
        self.assertEqual(res_res.status_code, 404)

    def test_11_existing_parts_regression_check(self):
        """11. Regression check: verify dashboard, vitals history, and device status endpoints work cleanly."""
        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)

        res_vitals = self.client.get(f'/vitals/{self.unique_id}')
        self.assertEqual(res_vitals.status_code, 200)

        res_device = self.client.get('/api/device/status')
        self.assertEqual(res_device.status_code, 200)


if __name__ == '__main__':
    unittest.main()
