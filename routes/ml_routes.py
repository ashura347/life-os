"""
LIFE OS — Machine Learning REST API Blueprint (routes/ml_routes.py)
Provides POST /api/ml/predict for advisory prototype risk assessments.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import services.database as db
import services.ml_service as ml_service

ml_bp = Blueprint('ml_bp', __name__)


@ml_bp.route('/api/ml/predict', methods=['POST'])
def predict_ml_risk_api():
    """
    REST Endpoint: POST /api/ml/predict
    Evaluates incoming vital signs using the prototype ML Decision Tree model.

    Payload format:
    {
        "patient_id": "P001",
        "heart_rate": 82,
        "spo2": 98,
        "temperature": 36.8,
        "movement_status": "Normal"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid Payload', 'message': 'Request body must be valid JSON.'}), 400

    patient_id = str(data.get('patient_id', '')).strip()
    heart_rate = data.get('heart_rate')
    spo2 = data.get('spo2')
    temperature = data.get('temperature')

    # 1. Validate Patient ID non-empty
    if not patient_id:
        return jsonify({'error': 'Validation Error', 'message': 'patient_id field is required.'}), 400

    # 2. Confirm Patient Exists in SQLite
    patient = db.get_patient(patient_id)
    if not patient:
        return jsonify({
            'error': 'Patient Not Found',
            'message': f"Cannot perform ML prediction. Patient '{patient_id}' does not exist."
        }), 404

    # 3. Validate Numeric Vital Features
    if heart_rate is None or isinstance(heart_rate, bool) or not isinstance(heart_rate, (int, float)):
        return jsonify({'error': 'Validation Error', 'message': 'heart_rate must be a numeric value.'}), 400
    if spo2 is None or isinstance(spo2, bool) or not isinstance(spo2, (int, float)):
        return jsonify({'error': 'Validation Error', 'message': 'spo2 must be a numeric value.'}), 400
    if temperature is None or isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        return jsonify({'error': 'Validation Error', 'message': 'temperature must be a numeric value.'}), 400

    # Execute ML Model Inference
    result = ml_service.predict_risk(data)

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return jsonify({
        'success': True,
        'patient_id': patient_id,
        'available': result['available'],
        'risk_category': result['risk_category'],
        'confidence': result['confidence'],
        'model_version': result['model_version'],
        'timestamp': now_str,
        'disclaimer': result['disclaimer']
    }), 200
