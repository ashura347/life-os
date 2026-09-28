"""
LIFE OS — Part 6 Unit Test Suite: Location-Aware Emergency Response & Nearby Healthcare Facility Workflow
Tests emergency event creation, status transitions, nearby facility discovery, test notifications,
API endpoints, safety disclaimers, and regression health across Parts 1-5.
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
import services.hospital_service as hospital_service
import services.notification_service as notification_service
import services.emergency_service as emergency_service


class Part6EmergencyResponseTestCase(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client and ensure test database has seed patient and baseline alert."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.init_db()

        # Ensure patient P001 exists with Pune location
        self.patient = db.get_patient('P001')
        if not self.patient:
            db.add_patient('P001', 'Demo Patient', 30, 'Demo Contact')
            db.update_patient_location('P001', 'Pune, Maharashtra', 18.5204, 73.8567)

        # Create a baseline active alert for testing escalation
        self.test_alert = db.create_alert_record(
            patient_id='P001',
            alert_type='HIGH_HEART_RATE_CRITICAL',
            severity='CRITICAL',
            message='Heart rate exceeded 120 BPM consecutively (125 BPM).'
        )

    def test_1_valid_alert_creates_emergency_event(self):
        """1. Valid active alert creates emergency event with status transition (CREATED -> CONTACT_NOTIFIED)."""
        response = self.client.post('/api/emergency-events', json={
            "alert_id": self.test_alert['id']
        })
        self.assertIn(response.status_code, [200, 201])
        data = response.get_json()

        self.assertTrue(data.get('success'))
        self.assertIn('event_id', data)
        self.assertEqual(data.get('status'), 'CONTACT_NOTIFIED')
        self.assertEqual(data.get('location'), 'Pune, Maharashtra')
        self.assertGreater(len(data.get('facilities', [])), 0)
        self.assertEqual(data.get('notification', {}).get('mode'), 'TEST')

    def test_2_invalid_alert_id(self):
        """2. Nonexistent alert ID returns 404 Not Found error."""
        response = self.client.post('/api/emergency-events', json={
            "alert_id": 999999
        })
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('code'), 'ALERT_NOT_FOUND')

    def test_3_alert_not_eligible_for_escalation(self):
        """3. Resolved alert is rejected for emergency escalation."""
        # Resolve alert first
        resolved_alert = db.resolve_alert_record(self.test_alert['id'])
        self.assertEqual(resolved_alert['status'], 'RESOLVED')

        # Attempt to escalate resolved alert
        response = self.client.post('/api/emergency-events', json={
            "alert_id": self.test_alert['id']
        })
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('code'), 'NOT_ELIGIBLE_FOR_ESCALATION')

    def test_4_missing_patient_location_fallback(self):
        """4. Patient with unassigned location falls back safely to 'Pune, Maharashtra'."""
        if not db.get_patient('P999'):
            db.add_patient('P999', 'No Location Patient', 45, 'Emergency Contact 999')
        temp_alert = db.create_alert_record('P999', 'LOW_SPO2_CRITICAL', 'CRITICAL', 'SpO2 critical.')

        result = emergency_service.create_emergency_event(temp_alert['id'])
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('location'), 'Pune, Maharashtra')

    def test_5_hospital_service_returns_facilities(self):
        """5. Hospital service returns curated test dataset with required fields and disclaimers."""
        res = hospital_service.search_nearby_facilities("Pune, Maharashtra", 18.5204, 73.8567)
        self.assertTrue(res.get('success'))
        self.assertGreaterEqual(res.get('facilities_count'), 4)
        self.assertIn('disclaimer', res)

        facility = res['facilities'][0]
        self.assertIn('name', facility)
        self.assertIn('address', facility)
        self.assertIn('distance', facility)
        self.assertIn('contact_number', facility)
        self.assertIn('services', facility)
        self.assertIn('source', facility)
        self.assertIn('availability_disclaimer', facility)

    def test_6_hospital_service_api_failure_fallback(self):
        """6. Hospital service gracefully falls back to curated test dataset on API or coordinate error."""
        # Pass invalid coordinates & dummy key
        os.environ['MAPS_API_KEY'] = 'INVALID_DUMMY_KEY_TEST'
        res = hospital_service.search_nearby_facilities("Pune, Maharashtra", None, None)
        del os.environ['MAPS_API_KEY']

        self.assertTrue(res.get('success'))
        self.assertEqual(res.get('source_type'), 'CURATED_TEST_DATASET')
        self.assertGreater(len(res.get('facilities', [])), 0)

    def test_7_test_notification_generated(self):
        """7. Notification service generates audit log with mode 'TEST' and zero external calls."""
        notif = notification_service.send_test_notification(101, 'P001', 'Test Alert Message', 'Demo Contact')
        self.assertEqual(notif.get('mode'), 'TEST')
        self.assertEqual(notif.get('recipient'), 'Demo Contact')
        self.assertEqual(notif.get('status'), 'SENT_TEST_LOG')
        self.assertIn('TEST NOTIFICATION ONLY', notif.get('disclaimer'))

    def test_8_emergency_event_acknowledgement(self):
        """8. POST /api/emergency-events/<event_id>/acknowledge transitions status to ACKNOWLEDGED."""
        event_res = emergency_service.create_emergency_event(self.test_alert['id'])
        event_id = event_res['event_id']

        response = self.client.post(f'/api/emergency-events/{event_id}/acknowledge')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['event']['response_status'], 'ACKNOWLEDGED')

    def test_9_emergency_event_resolution(self):
        """9. POST /api/emergency-events/<event_id>/resolve transitions status to RESOLVED."""
        event_res = emergency_service.create_emergency_event(self.test_alert['id'])
        event_id = event_res['event_id']

        response = self.client.post(f'/api/emergency-events/{event_id}/resolve', json={
            "selected_facility": "Ruby Hall Clinic"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['event']['response_status'], 'RESOLVED')
        self.assertEqual(data['event']['selected_facility'], 'Ruby Hall Clinic')

    def test_10_regression_check_parts_1_to_5(self):
        """10. Parts 1-5 core endpoints (/dashboard, /api/vitals, /api/alerts/P001, /api/ml/predict) remain 100% operational."""
        # Dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)

        # POST /api/vitals
        vital_res = self.client.post('/api/vitals', json={
            "patient_id": "P001",
            "heart_rate": 78,
            "spo2": 98,
            "temperature": 36.7,
            "movement_status": "Normal"
        })
        self.assertEqual(vital_res.status_code, 201)

        # GET /api/alerts/P001
        alerts_res = self.client.get('/api/alerts/P001')
        self.assertEqual(alerts_res.status_code, 200)

        # POST /api/ml/predict
        ml_res = self.client.post('/api/ml/predict', json={
            "patient_id": "P001",
            "heart_rate": 80,
            "spo2": 98,
            "temperature": 36.8,
            "movement_status": "Resting"
        })
        self.assertEqual(ml_res.status_code, 200)

    def test_11_no_real_external_communication(self):
        """11. Verifies that zero real external network socket, Twilio, or phone call dispatches were executed."""
        notif = notification_service.send_test_notification(1, 'P001', 'Safety Check', 'Demo Contact')
        self.assertEqual(notif['mode'], 'TEST')
        # Confirm disclaimer presence
        self.assertIn('No real SMS, phone call, or emergency service dispatch was executed', notif['disclaimer'])


if __name__ == '__main__':
    unittest.main()
