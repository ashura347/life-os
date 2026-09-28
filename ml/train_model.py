"""
LIFE OS — Pure Python Machine Learning Model Training Script (ml/train_model.py)

Trains a Decision Tree / Ensemble Classifier for vital signs risk prediction,
evaluates accuracy, precision, recall, and F1 metrics, and saves the trained model
to ml/models/risk_model.json.

Zero C-DLL dependency — guaranteed compatible across all operating system security policies.

USAGE:
  python ml/train_model.py
"""

import os
import random
import math
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'ml', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_model.json')


def generate_synthetic_dataset(n_samples=1500, random_seed=42):
    """
    Generates a demonstration dataset of vital signs and risk category labels.

    DISCLAIMER:
    This dataset is synthetically generated based on standard physiological parameter ranges
    for student prototype validation. It is not a clinically validated patient dataset.
    """
    random.seed(random_seed)
    dataset = []

    # Features: [heart_rate, spo2, temperature, movement_encoded]
    # Labels  : 0=LOW_RISK, 1=MODERATE_RISK, 2=ELEVATED

    # 1. LOW_RISK (label 0): Normal vitals (~50% of dataset)
    for _ in range(int(n_samples * 0.5)):
        hr = round(random.gauss(75, 6), 1)
        spo2 = round(random.gauss(98, 1), 1)
        temp = round(random.gauss(36.8, 0.2), 1)
        mov = random.choice([0, 1, 2])

        hr = max(60.0, min(95.0, hr))
        spo2 = max(96.0, min(100.0, spo2))
        temp = max(36.2, min(37.4, temp))
        dataset.append({'features': [hr, spo2, temp, float(mov)], 'label': 0})

    # 2. MODERATE_RISK (label 1): Mild vital abnormalities (~30% of dataset)
    for _ in range(int(n_samples * 0.3)):
        pattern = random.choice(['mild_hr', 'mild_spo2', 'mild_fever'])
        mov = random.choice([0, 1, 2])

        if pattern == 'mild_hr':
            hr = round(random.uniform(96, 112), 1)
            spo2 = round(random.uniform(95, 98), 1)
            temp = round(random.uniform(36.6, 37.5), 1)
        elif pattern == 'mild_spo2':
            hr = round(random.uniform(70, 95), 1)
            spo2 = round(random.uniform(93, 95), 1)
            temp = round(random.uniform(36.6, 37.5), 1)
        else: # mild fever
            hr = round(random.uniform(75, 100), 1)
            spo2 = round(random.uniform(96, 99), 1)
            temp = round(random.uniform(37.6, 38.2), 1)

        dataset.append({'features': [hr, spo2, temp, float(mov)], 'label': 1})

    # 3. ELEVATED (label 2): Severe vital abnormalities (~20% of dataset)
    for _ in range(int(n_samples * 0.2)):
        pattern = random.choice(['high_hr', 'low_spo2', 'high_fever'])
        mov = random.choice([0, 1, 2])

        if pattern == 'high_hr':
            hr = round(random.uniform(115, 145), 1)
            spo2 = round(random.uniform(92, 97), 1)
            temp = round(random.uniform(36.8, 38.0), 1)
        elif pattern == 'low_spo2':
            hr = round(random.uniform(80, 115), 1)
            spo2 = round(random.uniform(85, 92), 1)
            temp = round(random.uniform(36.6, 37.8), 1)
        else: # high fever
            hr = round(random.uniform(90, 125), 1)
            spo2 = round(random.uniform(94, 98), 1)
            temp = round(random.uniform(38.4, 40.0), 1)

        dataset.append({'features': [hr, spo2, temp, float(mov)], 'label': 2})

    random.shuffle(dataset)
    return dataset


class DecisionTreeNode:
    """Pure Python Decision Tree Node."""
    def __init__(self, feature_idx=None, threshold=None, left=None, right=None, value=None, probabilities=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.probabilities = probabilities

    def is_leaf(self):
        return self.value is not None

    def to_dict(self):
        """Serializes node to dictionary for JSON storage."""
        if self.is_leaf():
            return {'value': self.value, 'probabilities': self.probabilities}
        return {
            'feature_idx': self.feature_idx,
            'threshold': self.threshold,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

    @classmethod
    def from_dict(cls, d):
        """Deserializes node from dictionary."""
        if not d:
            return None
        if 'value' in d and d['value'] is not None:
            return cls(value=d['value'], probabilities=d['probabilities'])
        return cls(
            feature_idx=d['feature_idx'],
            threshold=d['threshold'],
            left=cls.from_dict(d['left']),
            right=cls.from_dict(d['right'])
        )


class PurePythonDecisionTree:
    """Pure Python Decision Tree Classifier implementation."""
    def __init__(self, max_depth=5, min_samples_split=5):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def _gini(self, labels):
        if not labels:
            return 0
        total = len(labels)
        counts = {}
        for l in labels:
            counts[l] = counts.get(l, 0) + 1
        return 1.0 - sum((cnt / total) ** 2 for cnt in counts.values())

    def _best_split(self, X, y):
        best_gini = float('inf')
        best_feature = None
        best_threshold = None
        n_samples = len(X)
        n_features = len(X[0])

        for f_idx in range(n_features):
            values = sorted(list(set(row[f_idx] for row in X)))
            for i in range(len(values) - 1):
                threshold = (values[i] + values[i + 1]) / 2.0
                left_y = [y[j] for j in range(n_samples) if X[j][f_idx] <= threshold]
                right_y = [y[j] for j in range(n_samples) if X[j][f_idx] > threshold]

                if not left_y or not right_y:
                    continue

                gini = (len(left_y) / n_samples) * self._gini(left_y) + (len(right_y) / n_samples) * self._gini(right_y)
                if gini < best_gini:
                    best_gini = gini
                    best_feature = f_idx
                    best_threshold = threshold

        return best_feature, best_threshold

    def _build_tree(self, X, y, depth=0):
        n_samples = len(X)
        n_labels = len(set(y))

        # Calculate class probabilities
        probs = [y.count(c) / float(n_samples) for c in range(3)]
        most_common = max(range(3), key=lambda c: y.count(c))

        if depth >= self.max_depth or n_labels == 1 or n_samples < self.min_samples_split:
            return DecisionTreeNode(value=most_common, probabilities=probs)

        feature_idx, threshold = self._best_split(X, y)
        if feature_idx is None:
            return DecisionTreeNode(value=most_common, probabilities=probs)

        left_X, left_y, right_X, right_y = [], [], [], []
        for i in range(n_samples):
            if X[i][feature_idx] <= threshold:
                left_X.append(X[i])
                left_y.append(y[i])
            else:
                right_X.append(X[i])
                right_y.append(y[i])

        left_child = self._build_tree(left_X, left_y, depth + 1)
        right_child = self._build_tree(right_X, right_y, depth + 1)

        return DecisionTreeNode(feature_idx=feature_idx, threshold=threshold, left=left_child, right=right_child)

    def fit(self, X, y):
        self.root = self._build_tree(X, y)

    def _predict_sample(self, node, sample):
        if node.is_leaf():
            return node.value, node.probabilities
        if sample[node.feature_idx] <= node.threshold:
            return self._predict_sample(node.left, sample)
        else:
            return self._predict_sample(node.right, sample)

    def predict(self, sample):
        val, probs = self._predict_sample(self.root, sample)
        return val, probs


def train_and_evaluate_model():
    print("=================================================================")
    print("  LIFE OS — Training Pure Python AI/ML Risk Analysis Model      ")
    print("=================================================================")

    # 1. Generate Dataset
    dataset = generate_synthetic_dataset(n_samples=1500, random_seed=42)
    X = [d['features'] for d in dataset]
    y = [d['label'] for d in dataset]

    print(f"[Dataset] Generated {len(X)} synthetic physiological samples.")
    print(f"          Classes: 0=LOW_RISK ({y.count(0)}), 1=MODERATE_RISK ({y.count(1)}), 2=ELEVATED ({y.count(2)})\n")

    # 2. Train / Test Split (80% Train, 20% Test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # 3. Train Decision Tree
    tree = PurePythonDecisionTree(max_depth=6, min_samples_split=6)
    print("[Training] Fitting Pure Python DecisionTree (max_depth=6)...")
    tree.fit(X_train, y_train)

    # 4. Evaluate Test Metrics
    y_pred = [tree.predict(sample)[0] for sample in X_test]
    correct = sum(1 for i in range(len(y_test)) if y_test[i] == y_pred[i])
    acc = float(correct) / len(y_test)

    # Multi-class Weighted Precision & Recall calculation
    classes = [0, 1, 2]
    precisions, recalls, f1s = [], [], []

    for c in classes:
        tp = sum(1 for i in range(len(y_test)) if y_test[i] == c and y_pred[i] == c)
        fp = sum(1 for i in range(len(y_test)) if y_test[i] != c and y_pred[i] == c)
        fn = sum(1 for i in range(len(y_test)) if y_test[i] == c and y_pred[i] != c)

        prec = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    avg_prec = sum(precisions) / len(classes)
    avg_rec = sum(recalls) / len(classes)
    avg_f1 = sum(f1s) / len(classes)

    print("\n-----------------------------------------------------------------")
    print("                      EVALUATION METRICS                         ")
    print("-----------------------------------------------------------------")
    print(f"  Accuracy  : {acc * 100:.2f}%")
    print(f"  Precision : {avg_prec * 100:.2f}%")
    print(f"  Recall    : {avg_rec * 100:.2f}%")
    print(f"  F1-Score  : {avg_f1 * 100:.2f}%")
    print("-----------------------------------------------------------------\n")

    # 5. Save Model to JSON File
    model_data = {
        'model_version': 'prototype-v1',
        'algorithm': 'PurePythonDecisionTree',
        'metrics': {
            'accuracy': acc,
            'precision': avg_prec,
            'recall': avg_rec,
            'f1_score': avg_f1
        },
        'tree_root': tree.root.to_dict()
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(model_data, f, indent=2)

    print(f"[Save] Model artifact saved successfully to: {MODEL_PATH}")
    print("=================================================================\n")

    return model_data


if __name__ == '__main__':
    train_and_evaluate_model()
