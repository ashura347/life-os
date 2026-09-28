"""
LIFE OS — Part 7 End-to-End Integration Test Suite (tests/test_end_to_end.py)
Verifies the complete system workflow across all 17 required integration steps:
Patient Registration -> Vital Ingestion -> SQLite Storage -> Rule Alert Engine ->
AI/ML Risk Assessment -> Emergency Event Creation -> Location & Healthcare Search ->
Test Notification Log -> Acknowledge / Resolve Workflow.
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
import tests.test_data as test_data


class EndToEndSystemIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        """Initialize test client and seed database."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.init_db()

        self.patient_id = "P_E2E"

        # Clear any pre-existing active alerts for clean test isolation
        active_alerts = db.get_active_alerts(self.patient_id)
        for a in active_alerts:
            db.resolve_alert_record(a['id'])

    def test_full_end_to_end_system_workflow(self):
        """Executes the complete 17-step end-to-end integration sequence."""

        # ---------------------------------------------------------------------
        # Step 1: Register a test patient (P_E2E)
        # ---------------------------------------------------------------------
        existing_patient = db.get_patient(self.patient_id)
        if not existing_patient:
            patient_res = self.client.post('/api/patients', json={
                "patient_id": self.patient_id,
                "name": "E2E Integration Test Patient",
                "age": 42,
                "emergency_contact": "Test Contact (+91 90000 11111)"
            })
            self.assertIn(patient_res.status_code, [200, 201])
            db.update_patient_location(self.patient_id, 'Pune, Maharashtra', 18.5204, 73.8567)

        patient = db.get_patient(self.patient_id)
        self.assertIsNotNone(patient)
        self.assertEqual(patient['patient_id'], self.patient_id)

        # ---------------------------------------------------------------------
        # Step 2: Register or verify a test device (LIFEOS-001)
        # ---------------------------------------------------------------------
        hb_res = self.client.post('/api/device/heartbeat', json={
            "device_id": "LIFEOS-001",
            "patient_id": self.patient_id
        })
        self.assertEqual(hb_res.status_code, 200)
        device_status = db.get_device_status('LIFEOS-001')
        self.assertEqual(device_status['connection_status'], 'CONNECTED')

        # ---------------------------------------------------------------------
        # Step 3: Send a normal vital reading
        # ---------------------------------------------------------------------
        normal_payload = {
            "patient_id": self.patient_id,
            "heart_rate": 75,
            "spo2": 98,
            "temperature": 36.8,
            "movement_status": "Resting"
        }
        vital_res_1 = self.client.post('/api/vitals', json=normal_payload)
        self.assertEqual(vital_res_1.status_code, 201)

        # ---------------------------------------------------------------------
        # Step 4: Confirm the reading is saved in database
        # ---------------------------------------------------------------------
        latest_vital = db.get_latest_vital_record(self.patient_id)
        self.assertIsNotNone(latest_vital)
        self.assertEqual(latest_vital['heart_rate'], 75)
        self.assertEqual(latest_vital['spo2'], 98)

        # ---------------------------------------------------------------------
        # Step 5: Confirm no critical alert is created for normal data
        # ---------------------------------------------------------------------
        active_alerts_normal = db.get_active_alerts(self.patient_id)
        self.assertEqual(len(active_alerts_normal), 0)

        # ---------------------------------------------------------------------
        # Step 6: Send abnormal test readings (consecutive to trigger persistence)
        # ---------------------------------------------------------------------
        critical_payload_1 = {
            "patient_id": self.patient_id,
            "heart_rate": 125,
            "spo2": 91,
            "temperature": 38.6,
            "movement_status": "Restless"
        }
        critical_payload_2 = {
            "patient_id": self.patient_id,
            "heart_rate": 128,
            "spo2": 90,
            "temperature": 38.7,
            "movement_status": "Restless"
        }

        # Reading 1 (Filtered by 2-reading persistence rule)
        res_crit_1 = self.client.post('/api/vitals', json=critical_payload_1)
        self.assertEqual(res_crit_1.status_code, 201)

        # Reading 2 (Triggers escalation)
        res_crit_2 = self.client.post('/api/vitals', json=critical_payload_2)
        self.assertEqual(res_crit_2.status_code, 201)

        # ---------------------------------------------------------------------
        # Step 7: Confirm the rule-based alert engine creates the correct alert
        # ---------------------------------------------------------------------
        active_alerts_crit = db.get_active_alerts(self.patient_id)
        self.assertGreater(len(active_alerts_crit), 0)
        alert = active_alerts_crit[0]
        self.assertIn('HIGH_HEART_RATE_CRITICAL', alert['alert_type'])
        self.assertEqual(alert['severity'], 'CRITICAL')
        alert_id = alert['id']

        # ---------------------------------------------------------------------
        # Step 8: Confirm duplicate active alerts are not unnecessarily created
        # ---------------------------------------------------------------------
        res_crit_3 = self.client.post('/api/vitals', json=critical_payload_2)
        self.assertEqual(res_crit_3.status_code, 201)
        active_alerts_dup_check = db.get_active_alerts(self.patient_id)
        # Count of active alerts of same type should remain 1
        same_type_alerts = [a for a in active_alerts_dup_check if a['alert_type'] == alert['alert_type']]
        self.assertEqual(len(same_type_alerts), 1)

        # ---------------------------------------------------------------------
        # Step 9: Request AI/ML prediction
        # ---------------------------------------------------------------------
        ml_res = self.client.post('/api/ml/predict', json={
            "patient_id": self.patient_id,
            "heart_rate": 128,
            "spo2": 90,
            "temperature": 38.7,
            "movement_status": "Restless"
        })
        self.assertEqual(ml_res.status_code, 200)
        ml_data = ml_res.get_json()
        self.assertTrue(ml_data.get('success'))

        # ---------------------------------------------------------------------
        # Step 10: Confirm ML output is marked as advisory (disclaimer present)
        # ---------------------------------------------------------------------
        self.assertIn('disclaimer', ml_data)
        self.assertIn('prototype', ml_data['disclaimer'].lower())

        # ---------------------------------------------------------------------
        # Step 11: Create an emergency event from an eligible alert
        # ---------------------------------------------------------------------
        em_res = self.client.post('/api/emergency-events', json={
            "alert_id": alert_id
        })
        self.assertIn(em_res.status_code, [200, 201])
        em_data = em_res.get_json()
        self.assertTrue(em_data.get('success'))
        event_id = em_data['event_id']

        # ---------------------------------------------------------------------
        # Step 12: Confirm location validation
        # ---------------------------------------------------------------------
        self.assertEqual(em_data.get('location'), 'Pune, Maharashtra')
        self.assertEqual(float(em_data.get('latitude')), 18.5204)
        self.assertEqual(float(em_data.get('longitude')), 73.8567)

        # ---------------------------------------------------------------------
        # Step 13: Retrieve nearby test healthcare facilities
        # ---------------------------------------------------------------------
        facilities = em_data.get('facilities', [])
        self.assertGreater(len(facilities), 0)
        facility = facilities[0]
        self.assertIn('name', facility)
        self.assertIn('contact_number', facility)

        # ---------------------------------------------------------------------
        # Step 14: Generate a TEST MODE notification record
        # ---------------------------------------------------------------------
        notif = em_data.get('notification', {})
        self.assertEqual(notif.get('mode'), 'TEST')
        self.assertEqual(notif.get('status'), 'SENT_TEST_LOG')
        self.assertIn('TEST NOTIFICATION ONLY', notif.get('disclaimer'))

        # ---------------------------------------------------------------------
        # Step 15: Acknowledge the emergency event
        # ---------------------------------------------------------------------
        ack_res = self.client.post(f'/api/emergency-events/{event_id}/acknowledge')
        self.assertEqual(ack_res.status_code, 200)
        ack_data = ack_res.get_json()
        self.assertEqual(ack_data['event']['response_status'], 'ACKNOWLEDGED')

        # ---------------------------------------------------------------------
        # Step 16: Resolve the emergency event
        # ---------------------------------------------------------------------
        resolve_res = self.client.post(f'/api/emergency-events/{event_id}/resolve', json={
            "selected_facility": "KEM Hospital Pune"
        })
        self.assertEqual(resolve_res.status_code, 200)
        resolve_data = resolve_res.get_json()
        self.assertEqual(resolve_data['event']['response_status'], 'RESOLVED')
        self.assertEqual(resolve_data['event']['selected_facility'], 'KEM Hospital Pune')

        # Also resolve the underlying alert to reset patient system status
        db.resolve_alert_record(alert_id)

        # ---------------------------------------------------------------------
        # Step 17: Confirm all final statuses are correct
        # ---------------------------------------------------------------------
        final_event = db.get_emergency_event_by_id(event_id)
        self.assertEqual(final_event['response_status'], 'RESOLVED')

        final_alert = db.get_alert_by_id(alert_id)
        self.assertEqual(final_alert['status'], 'RESOLVED')

        final_system_status = db.get_patient('P001')
        self.assertIsNotNone(final_system_status)


if __name__ == '__main__':
    unittest.main()
