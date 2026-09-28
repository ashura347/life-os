"""
LIFE OS — Machine Learning Feature Preprocessing & Inference Helper (ml/predict.py)
"""

# Feature Names for Model Inputs
FEATURE_NAMES = ['heart_rate', 'spo2', 'temperature', 'movement_encoded']

# Categorical Encoding for Movement Status
MOVEMENT_ENCODING = {
    'normal': 0,
    'resting': 1,
    'active': 2
}

# Target Risk Category Mapping
RISK_CATEGORIES = {
    0: 'LOW_RISK',
    1: 'MODERATE_RISK',
    2: 'ELEVATED'
}


def encode_movement(movement_status):
    """Encodes string movement_status into numeric integer."""
    if not movement_status:
        return 0
    clean_str = str(movement_status).strip().lower()
    return MOVEMENT_ENCODING.get(clean_str, 0)


def extract_features(vital_record):
    """
    Extracts numerical feature vector [heart_rate, spo2, temperature, movement_encoded]
    from a vital record dictionary.
    """
    try:
        hr = float(vital_record['heart_rate'])
        spo2 = float(vital_record['spo2'])
        temp = float(vital_record['temperature'])
        mov_encoded = float(encode_movement(vital_record.get('movement_status', 'Normal')))
        return [[hr, spo2, temp, mov_encoded]]
    except Exception as e:
        raise ValueError(f"Feature extraction failed: {e}")
