"""
LIFE OS — Patient Routes & API Blueprint
Handles Web UI views and REST API endpoints for patient management.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import services.database as db

patient_bp = Blueprint('patient_bp', __name__)


# =========================================================================
# Web UI Routes
# =========================================================================

@patient_bp.route('/patients', methods=['GET'])
def list_patients():
    """Renders the Patient Management page with all registered patients."""
    patients = db.get_all_patients()
    return render_template('patient_management.html', patients=patients)


@patient_bp.route('/patients/add', methods=['POST'])
def add_patient_form():
    """Web form submission handler to register a new test patient."""
    patient_id = request.form.get('patient_id', '').strip()
    name = request.form.get('name', '').strip()
    age_raw = request.form.get('age', '').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()

    # Basic Validation
    if not patient_id:
        return render_template('patient_management.html', patients=db.get_all_patients(), error="Patient ID is required.")
    if not name:
        return render_template('patient_management.html', patients=db.get_all_patients(), error="Patient Name is required.")
    if not age_raw or not age_raw.isdigit():
        return render_template('patient_management.html', patients=db.get_all_patients(), error="Valid numeric age is required.")

    if db.get_patient(patient_id):
        return render_template('patient_management.html', patients=db.get_all_patients(), error=f"Patient ID '{patient_id}' already exists.")

    db.add_patient(patient_id, name, int(age_raw), emergency_contact)
    return redirect(url_for('patient_bp.list_patients'))


# =========================================================================
# REST API Endpoints (For ESP32 / External Integrations)
# =========================================================================

@patient_bp.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient_api(patient_id):
    """
    REST Endpoint: GET /api/patients/<patient_id>
    Retrieves patient details by patient_id.
    """
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"No patient record exists with ID '{patient_id}'."
        }), 404

    return jsonify({
        'success': True,
        'patient': patient,
        'disclaimer': 'DEMONSTRATION/TEST DATA'
    }), 200


@patient_bp.route('/api/patients', methods=['POST'])
def create_patient_api():
    """
    REST Endpoint: POST /api/patients
    Accepts JSON body: {"patient_id": "P002", "name": "Test User", "age": 35, "emergency_contact": "Contact info"}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid Request', 'message': 'JSON payload is required.'}), 400

    patient_id = str(data.get('patient_id', '')).strip()
    name = str(data.get('name', '')).strip()
    age = data.get('age')
    emergency_contact = str(data.get('emergency_contact', '')).strip()

    # Validation
    if not patient_id:
        return jsonify({'error': 'Validation Error', 'message': 'Patient ID cannot be empty.'}), 400
    if not name:
        return jsonify({'error': 'Validation Error', 'message': 'Patient name cannot be empty.'}), 400
    if age is None or not isinstance(age, (int, float)) or int(age) <= 0:
        return jsonify({'error': 'Validation Error', 'message': 'Age must be a positive integer.'}), 400

    if db.get_patient(patient_id):
        return jsonify({'error': 'Conflict', 'message': f"Patient ID '{patient_id}' already exists."}), 400

    new_patient = db.add_patient(patient_id, name, int(age), emergency_contact)
    return jsonify({
        'success': True,
        'patient': new_patient,
        'message': 'Patient registered successfully.',
        'disclaimer': 'DEMONSTRATION/TEST DATA'
    }), 201
