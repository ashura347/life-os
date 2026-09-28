"""
LIFE OS — Machine Learning Prediction Service (services/ml_service.py)

Safely loads the prototype risk analysis model and performs inference on incoming vital records.
If the model file is missing or corrupted, provides a graceful fallback without crashing.
"""

import os
import json
from ml.predict import extract_features, RISK_CATEGORIES
from ml.train_model import DecisionTreeNode

# Path to trained JSON model artifact
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'models', 'risk_model.json')

DISCLAIMER_TEXT = (
    "AI/ML prototype risk assessment — experimental decision-support output, "
    "not a medical diagnosis."
)

_MODEL_CACHE = None
_MODEL_VERSION = 'prototype-v1'


def load_model():
    """
    Safely loads the trained JSON Decision Tree model artifact.
    Returns model dictionary if successful, or None if file is missing/unreadable.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not os.path.exists(MODEL_PATH):
        return None

    try:
        with open(MODEL_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tree_root = DecisionTreeNode.from_dict(data.get('tree_root'))
        _MODEL_CACHE = {
            'model_version': data.get('model_version', _MODEL_VERSION),
            'algorithm': data.get('algorithm', 'DecisionTree'),
            'metrics': data.get('metrics', {}),
            'tree_root': tree_root
        }
        return _MODEL_CACHE
    except Exception as e:
        print(f"[ML Service Warning] Failed to load model artifact: {e}")
        return None


def predict_tree_sample(node, sample):
    """Recursively evaluates sample down DecisionTree node tree."""
    if node.is_leaf():
        return node.value, node.probabilities
    if sample[node.feature_idx] <= node.threshold:
        return predict_tree_sample(node.left, sample)
    else:
        return predict_tree_sample(node.right, sample)


def predict_risk(vital_record):
    """
    Accepts a vital record dict, validates features, and performs model inference.
    Returns structured prototype risk assessment dictionary.
    """
    model_data = load_model()

    if not model_data or not model_data.get('tree_root'):
        return {
            'available': False,
            'risk_category': 'UNKNOWN',
            'confidence': 0.0,
            'model_version': _MODEL_VERSION,
            'message': 'AI/ML model file unavailable. Running in rule-only mode.',
            'disclaimer': DISCLAIMER_TEXT
        }

    # Extract numerical feature vector
    try:
        features = extract_features(vital_record)[0]
    except Exception as e:
        return {
            'available': False,
            'risk_category': 'UNKNOWN',
            'confidence': 0.0,
            'model_version': _MODEL_VERSION,
            'message': f"Feature extraction error: {e}",
            'disclaimer': DISCLAIMER_TEXT
        }

    # Execute tree prediction
    try:
        class_idx, probabilities = predict_tree_sample(model_data['tree_root'], features)
        risk_category = RISK_CATEGORIES.get(class_idx, 'UNKNOWN')
        confidence = round(probabilities[class_idx], 2) if probabilities else 1.0

        return {
            'available': True,
            'risk_category': risk_category,
            'confidence': confidence,
            'model_version': model_data.get('model_version', _MODEL_VERSION),
            'disclaimer': DISCLAIMER_TEXT
        }
    except Exception as e:
        return {
            'available': False,
            'risk_category': 'UNKNOWN',
            'confidence': 0.0,
            'model_version': _MODEL_VERSION,
            'message': f"Inference exception: {e}",
            'disclaimer': DISCLAIMER_TEXT
        }
