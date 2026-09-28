"""
LIFE OS — Test Emergency Notification Service Module (Part 6)
Provides safe, testable notification logging for emergency response workflows.
Ensures ZERO real-world SMS, phone call, or external emergency service dispatches occur.
"""

from datetime import datetime

def send_test_notification(event_id, patient_id, alert_message, recipient="Demo Contact", location="Pune, Maharashtra"):
    """
    Generates a simulated software audit log for an emergency notification.
    Operates strictly in TEST mode for student prototype safety.
    """
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_payload = {
        "mode": "TEST",
        "event_id": int(event_id),
        "patient_id": str(patient_id),
        "recipient": str(recipient) if recipient else "Authorized Emergency Contact",
        "message": f"TEST EMERGENCY ALERT: Emergency event #{event_id} created for patient {patient_id}. Alert: '{alert_message}'. Location: {location}.",
        "timestamp": now_str,
        "status": "SENT_TEST_LOG",
        "disclaimer": "TEST NOTIFICATION ONLY. No real SMS, phone call, or emergency service dispatch was executed."
    }
    return notification_payload
