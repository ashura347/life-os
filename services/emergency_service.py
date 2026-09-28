"""
LIFE OS — Emergency Event Service Module (Part 6)
Orchestrates location-aware emergency response events, facility discovery,
and test notifications for critical and warning alerts.
"""

import services.database as db
import services.hospital_service as hospital_service
import services.notification_service as notification_service


def create_emergency_event(alert_id, selected_facility=None):
    """
    Creates and initiates an emergency response workflow for an existing active/acknowledged alert.
    
    Data Flow:
    1. Validate alert existence & escalation eligibility.
    2. Retrieve patient profile, location & latest vitals.
    3. Create emergency event record (status: CREATED).
    4. Search nearby healthcare facilities (status: FACILITY_SEARCHED).
    5. Generate test notification log (status: CONTACT_NOTIFIED).
    """
    # 1. Validate Alert ID
    try:
        alert_id_int = int(alert_id)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "Invalid alert ID format.",
            "code": "INVALID_ALERT_ID"
        }

    alert = db.get_alert_by_id(alert_id_int)
    if not alert:
        return {
            "success": False,
            "error": f"Alert ID {alert_id} not found.",
            "code": "ALERT_NOT_FOUND"
        }

    # 2. Check Escalation Eligibility (Must be ACTIVE or ACKNOWLEDGED)
    if alert['status'] not in ('ACTIVE', 'ACKNOWLEDGED'):
        return {
            "success": False,
            "error": f"Alert ID {alert_id} is in '{alert['status']}' state and is not eligible for emergency escalation.",
            "code": "NOT_ELIGIBLE_FOR_ESCALATION"
        }

    # Deduplication check: check if an active emergency event already exists for this alert
    existing_event = db.get_emergency_event_by_alert_id(alert_id_int)
    if existing_event and existing_event['response_status'] not in ('RESOLVED',):
        # Fetch facilities and return existing active event
        facilities_result = hospital_service.search_nearby_facilities(
            existing_event['location'],
            existing_event['latitude'],
            existing_event['longitude']
        )
        patient = db.get_patient(existing_event['patient_id'])
        vitals = db.get_latest_vital_record(existing_event['patient_id'])
        test_notification = notification_service.send_test_notification(
            existing_event['id'],
            existing_event['patient_id'],
            alert['message'],
            patient.get('emergency_contact', 'Demo Contact') if patient else 'Demo Contact',
            existing_event['location']
        )

        return {
            "success": True,
            "event_id": existing_event['id'],
            "alert": alert,
            "patient": patient,
            "vitals": vitals,
            "location": existing_event['location'],
            "latitude": existing_event['latitude'],
            "longitude": existing_event['longitude'],
            "status": existing_event['response_status'],
            "selected_facility": existing_event.get('selected_facility'),
            "facilities": facilities_result.get('facilities', []),
            "facilities_source": facilities_result.get('source_type'),
            "notification": test_notification,
            "created_at": existing_event['created_at'],
            "is_existing": True,
            "disclaimer": "Software emergency event workflow state. Not a clinical diagnosis or real hospital dispatch."
        }

    # 3. Retrieve Patient & Authorized Location
    patient_id = alert['patient_id']
    patient = db.get_patient(patient_id)
    vitals = db.get_latest_vital_record(patient_id)

    location = (patient.get('location') if patient else None) or 'Pune, Maharashtra'
    latitude = patient.get('latitude') if patient else 18.5204
    longitude = patient.get('longitude') if patient else 73.8567
    contact_person = (patient.get('emergency_contact') if patient else None) or 'Demo Contact'

    # 4. Create Emergency Event (CREATED)
    event = db.create_emergency_event_record(
        alert_id=alert_id_int,
        patient_id=patient_id,
        location=location,
        latitude=latitude,
        longitude=longitude,
        selected_facility=selected_facility,
        response_status='CREATED'
    )
    event_id = event['id']

    # 5. Search Healthcare Facilities (FACILITY_SEARCHED)
    facilities_result = hospital_service.search_nearby_facilities(location, latitude, longitude)
    db.update_emergency_event_status(event_id, response_status='FACILITY_SEARCHED', selected_facility=selected_facility)

    # 6. Generate Test Notification Log (CONTACT_NOTIFIED)
    test_notification = notification_service.send_test_notification(
        event_id=event_id,
        patient_id=patient_id,
        alert_message=alert['message'],
        recipient=contact_person,
        location=location
    )
    updated_event = db.update_emergency_event_status(event_id, response_status='CONTACT_NOTIFIED', selected_facility=selected_facility)

    return {
        "success": True,
        "event_id": event_id,
        "alert": alert,
        "patient": patient,
        "vitals": vitals,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "status": updated_event['response_status'],
        "selected_facility": selected_facility,
        "facilities": facilities_result.get('facilities', []),
        "facilities_source": facilities_result.get('source_type'),
        "notification": test_notification,
        "created_at": updated_event['created_at'],
        "is_existing": False,
        "disclaimer": "Software emergency event workflow state. Not a clinical diagnosis or real hospital dispatch."
    }


def get_emergency_event_details(event_id):
    """Retrieves detailed information for a specific emergency event ID."""
    try:
        event_id_int = int(event_id)
    except (ValueError, TypeError):
        return None

    event = db.get_emergency_event_by_id(event_id_int)
    if not event:
        return None

    alert = db.get_alert_by_id(event['alert_id'])
    patient = db.get_patient(event['patient_id'])
    vitals = db.get_latest_vital_record(event['patient_id'])
    facilities_result = hospital_service.search_nearby_facilities(
        event['location'],
        event['latitude'],
        event['longitude']
    )
    test_notification = notification_service.send_test_notification(
        event['id'],
        event['patient_id'],
        alert['message'] if alert else "Emergency Alert Triggered",
        patient.get('emergency_contact', 'Demo Contact') if patient else 'Demo Contact',
        event['location']
    )

    return {
        "event_id": event['id'],
        "alert_id": event['alert_id'],
        "patient_id": event['patient_id'],
        "patient": patient,
        "alert": alert,
        "vitals": vitals,
        "location": event['location'],
        "latitude": event['latitude'],
        "longitude": event['longitude'],
        "response_status": event['response_status'],
        "selected_facility": event.get('selected_facility'),
        "facilities": facilities_result.get('facilities', []),
        "facilities_source": facilities_result.get('source_type'),
        "notification": test_notification,
        "created_at": event['created_at'],
        "updated_at": event['updated_at'],
        "disclaimer": "Software emergency event workflow state. Not a clinical diagnosis or real hospital dispatch."
    }


def acknowledge_emergency_event(event_id):
    """Marks an emergency event as ACKNOWLEDGED."""
    try:
        event_id_int = int(event_id)
    except (ValueError, TypeError):
        return None

    event = db.get_emergency_event_by_id(event_id_int)
    if not event:
        return None

    updated = db.update_emergency_event_status(event_id_int, response_status='ACKNOWLEDGED')
    return get_emergency_event_details(event_id_int)


def resolve_emergency_event(event_id, selected_facility=None):
    """Marks an emergency event as RESOLVED."""
    try:
        event_id_int = int(event_id)
    except (ValueError, TypeError):
        return None

    event = db.get_emergency_event_by_id(event_id_int)
    if not event:
        return None

    updated = db.update_emergency_event_status(event_id_int, response_status='RESOLVED', selected_facility=selected_facility)
    return get_emergency_event_details(event_id_int)


def execute_test_emergency_workflow(event_id):
    """Executes a demonstration test workflow for an emergency event, updating state to TEST_COMPLETED."""
    try:
        event_id_int = int(event_id)
    except (ValueError, TypeError):
        return None

    event = db.get_emergency_event_by_id(event_id_int)
    if not event:
        return None

    updated = db.update_emergency_event_status(event_id_int, response_status='TEST_COMPLETED')
    return get_emergency_event_details(event_id_int)
