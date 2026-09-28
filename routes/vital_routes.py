"""
LIFE OS — Vital Records Routes & API Blueprint
Handles Web UI vital history pages and REST API endpoints for telemetry intake & alert evaluation.
"""

from flask import Blueprint, render_template, request, jsonify
import services.database as db
import services.alert_engine as alert_engine

vital_bp = Blueprint('vital_bp', __name__)


# =========================================================================
# Web UI Routes
# =========================================================================

@vital_bp.route('/vitals/<patient_id>', methods=['GET'])
def view_vital_history(patient_id):
    """
    Renders the Vital History page for a specific patient.
    Displays recent readings in a table ordered newest first.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return render_template(
            'vitals.html',
            patient=None,
            history=[],
            error=f"Patient ID '{patient_id}' was not found in the database."
        ), 404

    history = db.get_recent_vital_records(patient_id, limit=50)
    latest = db.get_latest_vital_record(patient_id)
    patient_status = alert_engine.get_patient_system_status(patient_id)

    return render_template(
        'vitals.html',
        patient=patient,
        latest=latest,
        history=history,
        patient_status=patient_status,
        error=None
    )


# =========================================================================
# REST API Endpoints (Telemetry Intake & Alert Integration)
# =========================================================================

@vital_bp.route('/api/vitals/<patient_id>', methods=['GET'])
def get_patient_vitals_api(patient_id):
    """
    REST Endpoint: GET /api/vitals/<patient_id>
    Retrieves history of vital records for a given patient.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"No patient record exists with ID '{patient_id}'."
        }), 404

    records = db.get_recent_vital_records(patient_id, limit=50)
    patient_status = alert_engine.get_patient_system_status(patient_id)

    return jsonify({
        'success': True,
        'patient_id': patient_id,
        'records_count': len(records),
        'patient_status': patient_status,
        'records': records,
        'disclaimer': 'SIMULATED/TEST VITAL DATA'
    }), 200


@vital_bp.route('/api/vitals/<patient_id>/latest', methods=['GET'])
def get_latest_vital_api(patient_id):
    """
    REST Endpoint: GET /api/vitals/<patient_id>/latest
    Retrieves the single latest vital reading for a patient along with derived alert status.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"No patient record exists with ID '{patient_id}'."
        }), 404

    latest = db.get_latest_vital_record(patient_id)
    if not latest:
        return jsonify({
            'error': 'No Records Found',
            'message': f"No vital records registered for patient '{patient_id}' yet."
        }), 404

    patient_status = alert_engine.get_patient_system_status(patient_id)

    return jsonify({
        'success': True,
        'patient': patient,
        'vitals': latest,
        'patient_status': patient_status,
        'disclaimer': 'SIMULATED/TEST VITAL DATA'
    }), 200


@vital_bp.route('/api/vitals', methods=['POST'])
def post_vital_record_api():
    """
    REST Endpoint: POST /api/vitals
    Intake endpoint for sensor telemetry (ESP32 / Simulated Client).
    Triggers the Alert Engine to evaluate rules and create alert records if criteria are met.

    Payload format:
    {
        "patient_id": "P001",
        "heart_rate": 82,
        "spo2": 98,
        "temperature": 36.8,
        "movement_status": "NORMAL",
        "device_id": "LIFEOS-001",
        "source": "ESP32_REAL_SENSOR"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid Payload', 'message': 'Request body must be valid JSON.'}), 400

    patient_id = str(data.get('patient_id', '')).strip()
    device_id = str(data.get('device_id', 'LIFEOS-001')).strip()
    source = str(data.get('source', 'SIMULATED')).strip()
    heart_rate = data.get('heart_rate')
    spo2 = data.get('spo2')
    temperature = data.get('temperature')
    movement_status = str(data.get('movement_status', 'Normal')).strip()

    # 1. Validate Patient ID non-empty
    if not patient_id:
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'patient_id field is required.'}), 400

    # 2. Validate Patient Existence in SQLite
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'success': False,
            'error': 'Patient Not Found',
            'message': f"Cannot record vitals. Patient '{patient_id}' does not exist in database."
        }), 404

    # 3. Validate Numeric Heart Rate
    if heart_rate is None or isinstance(heart_rate, bool):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'heart_rate must be a numeric value.'}), 400
    try:
        hr_val = int(heart_rate)
        if hr_val <= 0 or hr_val > 300:
            return jsonify({'success': False, 'error': 'Validation Error', 'message': 'heart_rate must be a realistic numeric value (1-300).'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'heart_rate must be a valid integer.'}), 400

    # 4. Validate Numeric SpO2
    if spo2 is None or isinstance(spo2, bool):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'spo2 must be a numeric value.'}), 400
    try:
        spo2_val = int(spo2)
        if spo2_val < 0 or spo2_val > 100:
            return jsonify({'success': False, 'error': 'Validation Error', 'message': 'spo2 must be a percentage between 0 and 100.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'spo2 must be a valid integer.'}), 400

    # 5. Validate Numeric Temperature
    if temperature is None or isinstance(temperature, bool):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'temperature must be a numeric value.'}), 400
    try:
        temp_val = float(temperature)
        if temp_val < 20.0 or temp_val > 45.0:
            return jsonify({'success': False, 'error': 'Validation Error', 'message': 'temperature must be a numeric value in °C (20.0 - 45.0).'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'temperature must be a valid floating-point number.'}), 400

    # Update Device Heartbeat and Source Metadata
    if device_id:
        db.update_device_heartbeat(device_id, patient_id, source=source)

    # Insert vital record into SQLite database
    new_record = db.add_vital_record(
        patient_id=patient_id,
        heart_rate=hr_val,
        spo2=spo2_val,
        temperature=temp_val,
        movement_status=movement_status if movement_status else 'Normal',
        source=source
    )

    # Trigger Alert Engine Evaluation
    eval_result = alert_engine.evaluate_vital_reading(patient_id, new_record)

    response_payload = {
        'success': True,
        'message': 'Vital reading received',
        'source': source,
        'alert_created': eval_result['alert_created'],
        'patient_status': eval_result['patient_status'],
        'patient': patient,
        'vitals': new_record,
        'received_at': new_record.get('recorded_at'),
        'disclaimer': 'PROTOTYPE VITAL DATA — NOT MEDICAL GRADE'
    }

    if eval_result['alert_created'] and eval_result.get('alert'):
        alert = eval_result['alert']
        response_payload['alert_id'] = alert['id']
        response_payload['severity'] = alert['severity']
        response_payload['alert_type'] = alert['alert_type']
        response_payload['alert_message'] = alert['message']

    return jsonify(response_payload), 201
