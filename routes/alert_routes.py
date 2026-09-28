"""
LIFE OS — Alert Management Routes & API Blueprint (routes/alert_routes.py)
Handles Web UI alert history view (/alerts/<patient_id>) and REST API endpoints.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import services.database as db
import services.alert_engine as alert_engine

alert_bp = Blueprint('alert_bp', __name__)


# =========================================================================
# Web UI Routes
# =========================================================================

@alert_bp.route('/alerts/<patient_id>', methods=['GET'])
def view_alert_history(patient_id):
    """
    Renders the Alert History & Management UI for a specific patient.
    Displays active alerts, alert history log, and action buttons.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return render_template(
            'alerts.html',
            patient=None,
            history=[],
            active_alerts=[],
            patient_status='NORMAL',
            error=f"Patient ID '{patient_id}' was not found in the database."
        ), 404

    history = alert_engine.get_alert_history(patient_id, limit=50)
    active = alert_engine.get_active_alerts(patient_id)
    patient_status = alert_engine.get_patient_system_status(patient_id)

    return render_template(
        'alerts.html',
        patient=patient,
        history=history,
        active_alerts=active,
        patient_status=patient_status,
        error=None
    )


# =========================================================================
# REST API Endpoints (Alert Management)
# =========================================================================

@alert_bp.route('/api/alerts/<patient_id>', methods=['GET'])
def get_patient_alerts_api(patient_id):
    """
    REST Endpoint: GET /api/alerts/<patient_id>
    Retrieves full alert history for a patient.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"No patient record exists with ID '{patient_id}'."
        }), 404

    history = alert_engine.get_alert_history(patient_id, limit=50)
    patient_status = alert_engine.get_patient_system_status(patient_id)

    return jsonify({
        'success': True,
        'patient_id': patient_id,
        'patient_status': patient_status,
        'alerts_count': len(history),
        'alerts': history,
        'disclaimer': 'PROTOTYPE ALERT ENGINE — REQUIRES CLINICAL VALIDATION'
    }), 200


@alert_bp.route('/api/alerts/<patient_id>/active', methods=['GET'])
def get_active_alerts_api(patient_id):
    """
    REST Endpoint: GET /api/alerts/<patient_id>/active
    Retrieves active (non-resolved) alerts for a patient.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"No patient record exists with ID '{patient_id}'."
        }), 404

    active = alert_engine.get_active_alerts(patient_id)
    patient_status = alert_engine.get_patient_system_status(patient_id)

    return jsonify({
        'success': True,
        'patient_id': patient_id,
        'patient_status': patient_status,
        'active_alerts_count': len(active),
        'active_alerts': active,
        'disclaimer': 'PROTOTYPE ALERT ENGINE — REQUIRES CLINICAL VALIDATION'
    }), 200


@alert_bp.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert_api(alert_id):
    """
    REST Endpoint: POST /api/alerts/<alert_id>/acknowledge
    Marks an alert as ACKNOWLEDGED.
    """
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        return jsonify({
            'error': 'Alert Not Found',
            'message': f"No alert record exists with ID '{alert_id}'."
        }), 404

    updated = alert_engine.acknowledge_alert(alert_id)
    patient_status = alert_engine.get_patient_system_status(alert['patient_id'])

    return jsonify({
        'success': True,
        'message': f"Alert #{alert_id} acknowledged successfully.",
        'alert': updated if updated else alert,
        'patient_status': patient_status
    }), 200


@alert_bp.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert_api(alert_id):
    """
    REST Endpoint: POST /api/alerts/<alert_id>/resolve
    Marks an alert as RESOLVED.
    """
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        return jsonify({
            'error': 'Alert Not Found',
            'message': f"No alert record exists with ID '{alert_id}'."
        }), 404

    updated = alert_engine.resolve_alert(alert_id)
    patient_status = alert_engine.get_patient_system_status(alert['patient_id'])

    return jsonify({
        'success': True,
        'message': f"Alert #{alert_id} resolved successfully.",
        'alert': updated if updated else alert,
        'patient_status': patient_status
    }), 200
