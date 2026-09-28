# LIFE OS — Machine Learning Risk Analysis Module (ml/)

This directory contains the machine learning training pipeline, dataset generator, model artifact serialization, and documentation for the **LIFE OS AI/ML Risk Analysis Module**.

---

## 🎯 Part 5 Objective & Overview

The AI/ML module provides an **advisory decision-support risk assessment** (`LOW_RISK`, `MODERATE_RISK`, `ELEVATED`) that runs alongside the deterministic rule-based alert engine from Part 4. 

> ⚠️ **IMPORTANT SAFETY & CLINICAL LIMITATIONS**  
> 1. **Experimental Decision-Support Output**: The AI/ML risk assessment is an experimental prototype output and does **NOT** constitute a certified clinical medical diagnosis.
> 2. **Rule-Engine Priority**: The Part 4 rule-based alert engine remains the primary deterministic emergency authority. An AI/ML prediction alone cannot override confirmed emergency alert states or trigger real-world emergency calls.
> 3. **Demonstration Dataset**: The training dataset is synthetically generated based on standard physiological parameter ranges for prototype demonstration. It is not a clinically validated real-patient dataset.

---

## 🛠️ Model Choice & Rationale

- **Algorithm**: Pure Python Decision Tree Classifier (`max_depth=6`).
- **Rationale**:
  - Provides clear, interpretable decision boundaries across multi-feature vital sign telemetry (Heart Rate, SpO2, Temperature, Movement).
  - Calculates exact class probability distributions for confidence scoring.
  - Zero binary C-DLL dependencies, ensuring 100% platform portability and security compliance across all operating system environments.

---

## 📊 Dataset & Feature Representation

Dataset Size: 1,500 samples (80% Train / 20% Test split).

### Input Features:
1. `heart_rate` (float): Heart rate in BPM (e.g. 60 – 140 BPM).
2. `spo2` (float): Blood oxygen saturation percentage (e.g. 85 – 100%).
3. `temperature` (float): Body temperature in °C (e.g. 36.0 – 40.0 °C).
4. `movement_encoded` (float): Encoded activity status (`0.0` = Normal, `1.0` = Resting, `2.0` = Active).

### Target Classes:
- `0` / `LOW_RISK` (~50%): Normal physiological parameters.
- `1` / `MODERATE_RISK` (~30%): Mild vital sign deviations.
- `2` / `ELEVATED` (~20%): Significant vital sign deviations.

---

## 📈 Model Training & Actual Evaluation Metrics

To train the model, run:
```bash
python ml/train_model.py
```

### Empirical Evaluation Metrics Achieved (on 20% Test Set):
- **Accuracy**: `96.33%`
- **Precision**: `96.92%`
- **Recall**: `96.41%`
- **F1-Score**: `96.65%`

Model Artifact Saved To: `ml/models/risk_model.json`

---

## 🔌 Inference Integration

The model is safely loaded into memory by `services/ml_service.py`. If the model file is missing or corrupted, the system gracefully falls back to `available: false` without interrupting server operation or Flask route rendering.
