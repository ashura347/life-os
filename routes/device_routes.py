"""
LIFE OS — Device Registration & Heartbeat Routes (Part 3 & 8)
Handles ESP32 device connection heartbeat pings and connection status endpoints.
"""

from flask import Blueprint, request, jsonify
import services.database as db

device_bp = Blueprint('device_bp', __name__)


@device_bp.route('/api/device/heartbeat', methods=['POST'])
def device_heartbeat_api():
    """
    REST Endpoint: POST /api/device/heartbeat
    Registers periodic heartbeat pings from ESP32 devices.

    Expected JSON Payload:
    {
        "device_id": "LIFEOS-001",
        "patient_id": "P001",
        "source": "ESP32_REAL_SENSOR",
        "last_error": null
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid Request', 'message': 'JSON payload is required.'}), 400

    device_id = str(data.get('device_id', '')).strip()
    patient_id = str(data.get('patient_id', '')).strip()
    source = str(data.get('source', 'SIMULATED')).strip()
    last_error = data.get('last_error')

    if not device_id:
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'device_id cannot be empty.'}), 400
    if not patient_id:
        return jsonify({'success': False, 'error': 'Validation Error', 'message': 'patient_id cannot be empty.'}), 400

    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({'success': False, 'error': 'Patient Not Found', 'message': f"Patient '{patient_id}' does not exist."}), 404

    # Update heartbeat timestamp in SQLite
    device_status = db.update_device_heartbeat(
        device_id=device_id,
        patient_id=patient_id,
        source=source,
        last_error=last_error
    )

    return jsonify({
        'success': True,
        'message': 'Heartbeat received successfully',
        'device_status': device_status
    }), 200


@device_bp.route('/api/device/status', methods=['GET'])
def get_device_status_api():
    """
    REST Endpoint: GET /api/device/status
    Retrieves the current software connection status for a device.
    Query param: ?device_id=LIFEOS-001 (defaults to LIFEOS-001)
    """
    device_id = request.args.get('device_id', 'LIFEOS-001').strip()
    status = db.get_device_status(device_id, timeout_seconds=20)
    latest_vital = db.get_latest_vital_record(status.get('patient_id', 'P001')) if status.get('patient_id') != 'NOT_CONFIGURED' else None

    return jsonify({
        'success': True,
        'device_id': status['device_id'],
        'patient_id': status['patient_id'],
        'connection_status': status['connection_status'],
        'data_source': status.get('data_source', 'SIMULATED'),
        'last_error': status.get('last_error'),
        'last_communication': status['last_communication'],
        'last_vital_reading': latest_vital,
        'disclaimer': status['disclaimer']
    }), 200
