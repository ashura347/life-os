"""
LIFE OS — Emergency Response Routes Module (Part 6)
Provides REST API endpoints and Web views for location-aware emergency response workflows.
"""

from flask import Blueprint, jsonify, request, render_template, redirect, url_for
import services.database as db
import services.emergency_service as emergency_service
import services.hospital_service as hospital_service

emergency_bp = Blueprint('emergency_bp', __name__)


# =========================================================================
# REST API ENDPOINTS
# =========================================================================

@emergency_bp.route('/api/emergency-events', methods=['POST'])
def create_emergency_event_api():
    """
    POST /api/emergency-events
    Initiates an emergency response event for a given alert_id.
    
    Expected JSON Payload: {"alert_id": 1, "selected_facility": "KEM Hospital Pune" (optional)}
    """
    data = request.get_json(silent=True)
    if not data or 'alert_id' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field 'alert_id' in JSON payload.",
            "code": "MISSING_ALERT_ID"
        }), 400

    alert_id = data['alert_id']
    selected_facility = data.get('selected_facility')

    result = emergency_service.create_emergency_event(alert_id, selected_facility)

    if not result.get('success'):
        status_code = 404 if result.get('code') == 'ALERT_NOT_FOUND' else 400
        return jsonify(result), status_code

    return jsonify(result), 201 if not result.get('is_existing') else 200


@emergency_bp.route('/api/emergency-events/<int:event_id>', methods=['GET'])
def get_emergency_event_api(event_id):
    """
    GET /api/emergency-events/<event_id>
    Retrieves full details of a specific emergency response event.
    """
    event_details = emergency_service.get_emergency_event_details(event_id)
    if not event_details:
        return jsonify({
            "success": False,
            "error": f"Emergency Event ID {event_id} not found.",
            "code": "EVENT_NOT_FOUND"
        }), 404

    return jsonify({
        "success": True,
        "event": event_details
    }), 200


@emergency_bp.route('/api/emergency-events/<int:event_id>/facilities', methods=['GET'])
def get_event_facilities_api(event_id):
    """
    GET /api/emergency-events/<event_id>/facilities
    Retrieves nearby healthcare facilities for a specific emergency event.
    """
    event_details = emergency_service.get_emergency_event_details(event_id)
    if not event_details:
        return jsonify({
            "success": False,
            "error": f"Emergency Event ID {event_id} not found.",
            "code": "EVENT_NOT_FOUND"
        }), 404

    facilities_result = hospital_service.search_nearby_facilities(
        event_details['location'],
        event_details['latitude'],
        event_details['longitude']
    )

    return jsonify(facilities_result), 200


@emergency_bp.route('/api/emergency-events/<int:event_id>/acknowledge', methods=['POST'])
def acknowledge_event_api(event_id):
    """
    POST /api/emergency-events/<event_id>/acknowledge
    Transitions event status to ACKNOWLEDGED.
    """
    updated_details = emergency_service.acknowledge_emergency_event(event_id)
    if not updated_details:
        return jsonify({
            "success": False,
            "error": f"Emergency Event ID {event_id} not found.",
            "code": "EVENT_NOT_FOUND"
        }), 404

    return jsonify({
        "success": True,
        "message": f"Emergency Event #{event_id} acknowledged successfully.",
        "event": updated_details
    }), 200


@emergency_bp.route('/api/emergency-events/<int:event_id>/resolve', methods=['POST'])
def resolve_event_api(event_id):
    """
    POST /api/emergency-events/<event_id>/resolve
    Transitions event status to RESOLVED.
    Optionally accepts {"selected_facility": "Ruby Hall Clinic"}.
    """
    data = request.get_json(silent=True) or {}
    selected_facility = data.get('selected_facility')

    updated_details = emergency_service.resolve_emergency_event(event_id, selected_facility)
    if not updated_details:
        return jsonify({
            "success": False,
            "error": f"Emergency Event ID {event_id} not found.",
            "code": "EVENT_NOT_FOUND"
        }), 404

    return jsonify({
        "success": True,
        "message": f"Emergency Event #{event_id} resolved successfully.",
        "event": updated_details
    }), 200


@emergency_bp.route('/api/emergency-events/<int:event_id>/test', methods=['POST'])
def run_test_event_api(event_id):
    """
    POST /api/emergency-events/<event_id>/test
    Runs a test demonstration emergency workflow, setting state to TEST_COMPLETED.
    """
    updated_details = emergency_service.execute_test_emergency_workflow(event_id)
    if not updated_details:
        return jsonify({
            "success": False,
            "error": f"Emergency Event ID {event_id} not found.",
            "code": "EVENT_NOT_FOUND"
        }), 404

    return jsonify({
        "success": True,
        "message": f"Test Emergency Workflow executed for Event #{event_id}.",
        "event": updated_details
    }), 200


# =========================================================================
# WEB DASHBOARD / EMERGENCY PAGES
# =========================================================================

@emergency_bp.route('/emergency/<int:event_id>')
def emergency_page(event_id):
    """
    GET /emergency/<event_id>
    Renders the dedicated Emergency Response Event monitoring page.
    """
    event_details = emergency_service.get_emergency_event_details(event_id)
    if not event_details:
        return redirect(url_for('dashboard'))

    return render_template(
        'emergency.html',
        event=event_details
    )


@emergency_bp.route('/emergency_history/<patient_id>')
def emergency_history_page(patient_id):
    """
    GET /emergency_history/<patient_id>
    Renders the emergency event history log for a patient.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return redirect(url_for('dashboard'))

    raw_events = db.get_all_emergency_events_for_patient(patient_id, limit=50)
    events = [emergency_service.get_emergency_event_details(e['id']) for e in raw_events]
    events = [e for e in events if e]

    return render_template(
        'emergency_history.html',
        patient=patient,
        events=events
    )
